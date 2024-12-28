from typing import List, Dict, Any, Optional
import aiohttp
import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import logging
from .config import settings

logger = logging.getLogger(__name__)

class NotificationManager:
    """Gerenciador de notificações para eventos críticos"""
    
    def __init__(self):
        self.slack_webhook_url = settings.SLACK_WEBHOOK_URL
        self.alert_email = settings.AUDIT_ALERT_EMAIL
        self.alert_slack_channel = settings.AUDIT_ALERT_SLACK_CHANNEL
        
    async def notify_critical_events(self, events: List[Dict[str, Any]]):
        """Notifica sobre eventos críticos através de múltiplos canais"""
        if not events:
            return
            
        try:
            await self._send_slack_notification(events)
        except Exception as e:
            logger.error(f"Erro ao enviar notificação para o Slack: {e}")
            
        try:
            await self._send_email_notification(events)
        except Exception as e:
            logger.error(f"Erro ao enviar notificação por email: {e}")
            
    async def _send_slack_notification(self, events: List[Dict[str, Any]]):
        """Envia notificação para o Slack"""
        if not self.slack_webhook_url:
            return
            
        blocks = self._format_slack_message(events)
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                self.slack_webhook_url,
                json={"blocks": blocks}
            ) as response:
                if response.status not in (200, 201):
                    logger.error(f"Erro ao enviar para Slack: {response.status}")
                    
    def _format_slack_message(self, events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Formata a mensagem para o Slack"""
        blocks = []
        
        # Cabeçalho
        blocks.append({
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": f"🚨 {len(events)} Eventos Críticos Detectados"
            }
        })
        
        # Resumo
        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*Período:* {self._format_time_range(events)}\n"
                       f"*Total de Eventos:* {len(events)}"
            }
        })
        
        blocks.append({"type": "divider"})
        
        # Eventos
        for event in events:
            blocks.extend(self._format_slack_event(event))
            
        return blocks
        
    def _format_slack_event(self, event: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Formata um evento individual para o Slack"""
        blocks = []
        
        # Cabeçalho do evento
        blocks.append({
            "type": "section",
            "fields": [
                {
                    "type": "mrkdwn",
                    "text": f"*Tipo:* {event['event_type']}\n*Severidade:* {event['severity']}"
                },
                {
                    "type": "mrkdwn",
                    "text": f"*Timestamp:* {event['timestamp']}\n*ID:* {event['event_id']}"
                }
            ]
        })
        
        # Mensagem do evento
        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*Mensagem:* {event['message']}"
            }
        })
        
        # Detalhes adicionais
        if event.get("details"):
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Detalhes:*\n```{self._format_details(event['details'])}```"
                }
            })
            
        blocks.append({"type": "divider"})
        return blocks
        
    async def _send_email_notification(self, events: List[Dict[str, Any]]):
        """Envia notificação por email"""
        if not self.alert_email:
            return
            
        msg = self._format_email_message(events)
        
        try:
            await aiosmtplib.send(
                msg,
                hostname=settings.SMTP_HOST,
                port=settings.SMTP_PORT,
                username=settings.SMTP_USERNAME,
                password=settings.SMTP_PASSWORD,
                use_tls=settings.SMTP_USE_TLS
            )
        except Exception as e:
            logger.error(f"Erro ao enviar email: {e}")
            raise
            
    def _format_email_message(self, events: List[Dict[str, Any]]) -> MIMEMultipart:
        """Formata a mensagem de email"""
        msg = MIMEMultipart()
        msg["Subject"] = f"[AUDITORIA] {len(events)} Eventos Críticos Detectados"
        msg["From"] = settings.SMTP_FROM_EMAIL
        msg["To"] = self.alert_email
        
        body = self._format_email_body(events)
        msg.attach(MIMEText(body, "plain"))
        
        return msg
        
    def _format_email_body(self, events: List[Dict[str, Any]]) -> str:
        """Formata o corpo do email"""
        body = f"""EVENTOS CRÍTICOS DE AUDITORIA
Gerado em: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}

RESUMO
------
Total de Eventos: {len(events)}
Período: {self._format_time_range(events)}

DETALHES DOS EVENTOS
-------------------
"""
        
        for event in events:
            body += f"""
Evento ID: {event['event_id']}
Tipo: {event['event_type']}
Severidade: {event['severity']}
Timestamp: {event['timestamp']}
Mensagem: {event['message']}

"""
            if event.get("details"):
                body += f"Detalhes:\n{self._format_details(event['details'])}\n"
                
            body += "=" * 50 + "\n"
            
        return body
        
    def _format_time_range(self, events: List[Dict[str, Any]]) -> str:
        """Formata o intervalo de tempo dos eventos"""
        timestamps = [event["timestamp"] for event in events]
        start = min(timestamps)
        end = max(timestamps)
        
        return f"{start.strftime('%Y-%m-%d %H:%M:%S')} até {end.strftime('%Y-%m-%d %H:%M:%S')}"
        
    def _format_details(self, details: Dict[str, Any]) -> str:
        """Formata detalhes adicionais do evento"""
        if not details:
            return "Nenhum detalhe adicional"
            
        formatted = []
        for key, value in details.items():
            formatted.append(f"{key}: {value}")
            
        return "\n".join(formatted)

# Instância global do gerenciador de notificações
notification_manager = NotificationManager() 