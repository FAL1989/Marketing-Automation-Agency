from typing import List, Dict, Any, Optional
import csv
import json
from datetime import datetime
import io
import pandas as pd
from ..core.config import settings
from ..core import monitoring
import logging
import aiofiles
import os
from pathlib import Path

logger = logging.getLogger(__name__)

class AuditExporter:
    """Exportador de logs de auditoria"""
    
    def __init__(self):
        self.export_dir = Path("exports/audit")
        self.export_dir.mkdir(parents=True, exist_ok=True)
        
    async def export_to_csv(
        self,
        events: List[Dict[str, Any]],
        output_file: Optional[str] = None
    ) -> str:
        """Exporta eventos para CSV"""
        if not events:
            return ""
            
        # Define o nome do arquivo se não fornecido
        if not output_file:
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            output_file = self.export_dir / f"audit_log_{timestamp}.csv"
            
        # Prepara os dados para exportação
        df = pd.DataFrame(events)
        
        # Organiza as colunas em uma ordem lógica
        columns = [
            "event_id",
            "timestamp",
            "event_type",
            "severity",
            "message",
            "user_id",
            "resource_id",
            "ip_address",
            "method",
            "path",
            "user_agent",
            "session_id"
        ]
        
        # Adiciona colunas extras que podem existir
        extra_columns = [col for col in df.columns if col not in columns]
        columns.extend(extra_columns)
        
        # Reordena e formata o DataFrame
        df = df.reindex(columns=columns)
        
        # Converte timestamps para formato legível
        if "timestamp" in df.columns:
            df["timestamp"] = pd.to_datetime(df["timestamp"]).dt.strftime("%Y-%m-%d %H:%M:%S")
            
        # Converte detalhes para formato legível
        if "details" in df.columns:
            df["details"] = df["details"].apply(lambda x: json.dumps(x, ensure_ascii=False) if x else "")
            
        # Salva o arquivo
        async with aiofiles.open(output_file, mode="w", encoding="utf-8", newline="") as f:
            await f.write(df.to_csv(index=False))
            
        logger.info(f"Exported {len(events)} events to {output_file}")
        return str(output_file)
        
    async def export_to_json(
        self,
        events: List[Dict[str, Any]],
        output_file: Optional[str] = None,
        pretty: bool = True
    ) -> str:
        """Exporta eventos para JSON"""
        if not events:
            return ""
            
        # Define o nome do arquivo se não fornecido
        if not output_file:
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            output_file = self.export_dir / f"audit_log_{timestamp}.json"
            
        # Prepara os dados para exportação
        export_data = {
            "metadata": {
                "exported_at": datetime.utcnow().isoformat(),
                "total_events": len(events),
                "format_version": "1.0"
            },
            "events": events
        }
        
        # Salva o arquivo
        async with aiofiles.open(output_file, mode="w", encoding="utf-8") as f:
            if pretty:
                await f.write(json.dumps(export_data, indent=2, default=str, ensure_ascii=False))
            else:
                await f.write(json.dumps(export_data, default=str, ensure_ascii=False))
                
        logger.info(f"Exported {len(events)} events to {output_file}")
        return str(output_file)
        
    async def export_to_excel(
        self,
        events: List[Dict[str, Any]],
        output_file: Optional[str] = None
    ) -> str:
        """Exporta eventos para Excel"""
        if not events:
            return ""
            
        # Define o nome do arquivo se não fornecido
        if not output_file:
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            output_file = self.export_dir / f"audit_log_{timestamp}.xlsx"
            
        # Prepara os dados para exportação
        df = pd.DataFrame(events)
        
        # Organiza as colunas em uma ordem lógica
        columns = [
            "event_id",
            "timestamp",
            "event_type",
            "severity",
            "message",
            "user_id",
            "resource_id",
            "ip_address",
            "method",
            "path",
            "user_agent",
            "session_id"
        ]
        
        # Adiciona colunas extras que podem existir
        extra_columns = [col for col in df.columns if col not in columns]
        columns.extend(extra_columns)
        
        # Reordena e formata o DataFrame
        df = df.reindex(columns=columns)
        
        # Converte timestamps para formato legível
        if "timestamp" in df.columns:
            df["timestamp"] = pd.to_datetime(df["timestamp"]).dt.strftime("%Y-%m-%d %H:%M:%S")
            
        # Converte detalhes para formato legível
        if "details" in df.columns:
            df["details"] = df["details"].apply(lambda x: json.dumps(x, ensure_ascii=False) if x else "")
            
        # Cria um writer do Excel com formatação
        writer = pd.ExcelWriter(output_file, engine="xlsxwriter")
        
        # Escreve os dados
        df.to_excel(writer, sheet_name="Audit Log", index=False)
        
        # Obtém o workbook e a worksheet
        workbook = writer.book
        worksheet = writer.sheets["Audit Log"]
        
        # Formata o cabeçalho
        header_format = workbook.add_format({
            'bold': True,
            'text_wrap': True,
            'valign': 'top',
            'fg_color': '#D7E4BC',
            'border': 1
        })
        
        # Aplica formatação
        for col_num, value in enumerate(df.columns.values):
            worksheet.write(0, col_num, value, header_format)
            worksheet.set_column(col_num, col_num, 15)
            
        # Ajusta largura das colunas
        for i, col in enumerate(df.columns):
            max_length = max(
                df[col].astype(str).apply(len).max(),
                len(str(col))
            )
            worksheet.set_column(i, i, max_length + 2)
            
        # Salva o arquivo
        writer.close()
        
        logger.info(f"Exported {len(events)} events to {output_file}")
        return str(output_file)
        
    async def create_summary_report(
        self,
        events: List[Dict[str, Any]],
        output_file: Optional[str] = None
    ) -> str:
        """Cria um relatório resumido dos eventos"""
        if not events:
            return ""
            
        # Define o nome do arquivo se não fornecido
        if not output_file:
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            output_file = self.export_dir / f"audit_summary_{timestamp}.txt"
            
        df = pd.DataFrame(events)
        
        # Gera estatísticas
        stats = {
            "total_events": len(events),
            "by_severity": df["severity"].value_counts().to_dict(),
            "by_event_type": df["event_type"].value_counts().to_dict(),
            "unique_users": df["user_id"].nunique(),
            "unique_ips": df["ip_address"].nunique(),
            "date_range": {
                "start": df["timestamp"].min(),
                "end": df["timestamp"].max()
            }
        }
        
        # Gera o relatório
        report = f"""RELATÓRIO DE AUDITORIA
Gerado em: {datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")}

RESUMO GERAL
-----------
Total de Eventos: {stats['total_events']}
Usuários Únicos: {stats['unique_users']}
IPs Únicos: {stats['unique_ips']}
Período: {stats['date_range']['start']} até {stats['date_range']['end']}

DISTRIBUIÇÃO POR SEVERIDADE
-------------------------
{self._format_dict(stats['by_severity'])}

DISTRIBUIÇÃO POR TIPO DE EVENTO
-----------------------------
{self._format_dict(stats['by_event_type'])}

EVENTOS CRÍTICOS
--------------
{self._format_critical_events(df)}

ATIVIDADES SUSPEITAS
------------------
{self._format_suspicious_activities(df)}
"""
        
        # Salva o relatório
        async with aiofiles.open(output_file, mode="w", encoding="utf-8") as f:
            await f.write(report)
            
        logger.info(f"Generated summary report at {output_file}")
        return str(output_file)
        
    def _format_dict(self, d: Dict[str, Any], indent: int = 0) -> str:
        """Formata um dicionário para exibição no relatório"""
        return "\n".join(f"{' ' * indent}{k}: {v}" for k, v in d.items())
        
    def _format_critical_events(self, df: pd.DataFrame) -> str:
        """Formata eventos críticos para o relatório"""
        critical = df[df["severity"] == "critical"].sort_values("timestamp", ascending=False)
        if len(critical) == 0:
            return "Nenhum evento crítico registrado."
            
        return "\n".join(
            f"[{row['timestamp']}] {row['event_type']}: {row['message']}"
            for _, row in critical.iterrows()
        )
        
    def _format_suspicious_activities(self, df: pd.DataFrame) -> str:
        """Formata atividades suspeitas para o relatório"""
        suspicious = df[df["event_type"].str.contains("suspicious|violation|failed", case=False)]
        if len(suspicious) == 0:
            return "Nenhuma atividade suspeita registrada."
            
        return "\n".join(
            f"[{row['timestamp']}] {row['event_type']} - IP: {row['ip_address']} - {row['message']}"
            for _, row in suspicious.iterrows()
        )

# Instância global do exportador
audit_exporter = AuditExporter() 