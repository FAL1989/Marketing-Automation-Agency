#!/usr/bin/env python3
import asyncio
import redis.asyncio as redis
import time
import logging
from datetime import datetime
import json
import os
import sys

# Adiciona diretório pai ao path para importar módulos da aplicação
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.config import settings
from app.core.optimizations import (
    REDIS_OPTIMIZATIONS,
    MONITORING_CONFIG
)

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class RedisMonitor:
    def __init__(self, redis_url: str = settings.REDIS_URL):
        self.redis_url = redis_url
        self.redis_client = None
        self.previous_stats = {}
        self.start_time = datetime.now()
        
    async def connect(self):
        """Conecta ao Redis"""
        try:
            self.redis_client = redis.from_url(
                self.redis_url,
                decode_responses=True
            )
            await self.redis_client.ping()
            logger.info("Conectado ao Redis com sucesso")
            return True
        except Exception as e:
            logger.error(f"Erro ao conectar ao Redis: {str(e)}")
            return False
            
    async def get_stats(self) -> dict:
        """Coleta estatísticas do Redis"""
        try:
            info = await self.redis_client.info()
            
            # Calcula métricas derivadas
            used_memory = int(info.get("used_memory", 0))
            total_memory = int(REDIS_OPTIMIZATIONS["max_memory"].rstrip("gb")) * 1024 * 1024 * 1024
            memory_usage = (used_memory / total_memory) * 100 if total_memory > 0 else 0
            
            # Calcula taxa de hits/misses
            hits = int(info.get("keyspace_hits", 0))
            misses = int(info.get("keyspace_misses", 0))
            total_ops = hits + misses
            hit_rate = (hits / total_ops * 100) if total_ops > 0 else 0
            
            # Calcula métricas de performance
            ops_per_sec = float(info.get("instantaneous_ops_per_sec", 0))
            
            # Coleta métricas de memória fragmentada
            mem_fragmentation_ratio = float(info.get("mem_fragmentation_ratio", 0))
            
            stats = {
                "timestamp": datetime.now().isoformat(),
                "uptime_seconds": int(info.get("uptime_in_seconds", 0)),
                "connected_clients": int(info.get("connected_clients", 0)),
                "used_memory_human": info.get("used_memory_human", "0B"),
                "used_memory_peak_human": info.get("used_memory_peak_human", "0B"),
                "memory_usage_percent": round(memory_usage, 2),
                "mem_fragmentation_ratio": round(mem_fragmentation_ratio, 2),
                "total_connections_received": int(info.get("total_connections_received", 0)),
                "total_commands_processed": int(info.get("total_commands_processed", 0)),
                "instantaneous_ops_per_sec": ops_per_sec,
                "hit_rate_percent": round(hit_rate, 2),
                "keyspace_hits": hits,
                "keyspace_misses": misses,
                "expired_keys": int(info.get("expired_keys", 0)),
                "evicted_keys": int(info.get("evicted_keys", 0)),
                "keyspace_details": info.get("db0", {}),
                "total_keys": sum(
                    db.get("keys", 0)
                    for name, db in info.items()
                    if name.startswith("db")
                ),
                "rejected_connections": int(info.get("rejected_connections", 0)),
                "sync_full": int(info.get("sync_full", 0)),
                "sync_partial_ok": int(info.get("sync_partial_ok", 0)),
                "sync_partial_err": int(info.get("sync_partial_err", 0))
            }
            
            # Calcula métricas de variação
            if self.previous_stats:
                time_diff = (
                    datetime.fromisoformat(stats["timestamp"]) -
                    datetime.fromisoformat(self.previous_stats["timestamp"])
                ).total_seconds()
                
                # Calcula variações
                for key in ["total_commands_processed", "keyspace_hits", "keyspace_misses"]:
                    if key in self.previous_stats:
                        diff = stats[key] - self.previous_stats[key]
                        rate = diff / time_diff if time_diff > 0 else 0
                        stats[f"{key}_rate"] = round(rate, 2)
            
            self.previous_stats = stats
            return stats
            
        except Exception as e:
            logger.error(f"Erro ao coletar estatísticas: {str(e)}")
            return {}
            
    def _check_thresholds(self, stats: dict) -> list:
        """Verifica se algum limite foi ultrapassado"""
        alerts = []
        
        # Verifica uso de memória
        if stats.get("memory_usage_percent", 0) > MONITORING_CONFIG["alert_memory_threshold"]:
            alerts.append({
                "level": "WARNING",
                "message": f"Uso de memória alto: {stats['memory_usage_percent']}%"
            })
            
        # Verifica taxa de erros
        total_ops = stats.get("keyspace_hits", 0) + stats.get("keyspace_misses", 0)
        if total_ops > 0:
            error_rate = (stats.get("keyspace_misses", 0) / total_ops) * 100
            if error_rate > MONITORING_CONFIG["alert_error_rate_threshold"]:
                alerts.append({
                    "level": "WARNING",
                    "message": f"Taxa de erros alta: {error_rate:.1f}%"
                })
                
        # Verifica fragmentação de memória
        if stats.get("mem_fragmentation_ratio", 0) > 1.5:
            alerts.append({
                "level": "WARNING",
                "message": f"Alta fragmentação de memória: {stats['mem_fragmentation_ratio']}"
            })
            
        # Verifica conexões rejeitadas
        if stats.get("rejected_connections", 0) > 0:
            alerts.append({
                "level": "ERROR",
                "message": f"Conexões rejeitadas: {stats['rejected_connections']}"
            })
            
        return alerts
        
    async def save_stats(self, stats: dict, alerts: list):
        """Salva estatísticas e alertas em arquivo"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Cria diretório se não existir
        os.makedirs("monitoring/redis", exist_ok=True)
        
        # Salva estatísticas
        stats_file = f"monitoring/redis/stats_{timestamp}.json"
        with open(stats_file, "w") as f:
            json.dump(stats, f, indent=2)
            
        # Salva alertas se houver
        if alerts:
            alerts_file = f"monitoring/redis/alerts_{timestamp}.json"
            with open(alerts_file, "w") as f:
                json.dump(alerts, f, indent=2)
                
        logger.info(f"Estatísticas salvas em {stats_file}")
        if alerts:
            logger.warning(f"Alertas salvos em {alerts_file}")
            
    async def monitor(self, interval: int = MONITORING_CONFIG["stats_interval"]):
        """Monitora o Redis continuamente"""
        if not await self.connect():
            return
            
        logger.info(f"Iniciando monitoramento do Redis (intervalo: {interval}s)")
        
        try:
            while True:
                # Coleta estatísticas
                stats = await self.get_stats()
                if not stats:
                    logger.error("Falha ao coletar estatísticas")
                    await asyncio.sleep(interval)
                    continue
                    
                # Verifica thresholds
                alerts = self._check_thresholds(stats)
                
                # Salva dados
                await self.save_stats(stats, alerts)
                
                # Loga alertas
                for alert in alerts:
                    if alert["level"] == "WARNING":
                        logger.warning(alert["message"])
                    else:
                        logger.error(alert["message"])
                        
                # Loga métricas principais
                logger.info(
                    f"Redis Status: "
                    f"Memória: {stats['memory_usage_percent']}% | "
                    f"Ops/s: {stats['instantaneous_ops_per_sec']} | "
                    f"Hit Rate: {stats['hit_rate_percent']}% | "
                    f"Clientes: {stats['connected_clients']}"
                )
                
                await asyncio.sleep(interval)
                
        except asyncio.CancelledError:
            logger.info("Monitoramento interrompido")
        except Exception as e:
            logger.error(f"Erro no monitoramento: {str(e)}")
        finally:
            if self.redis_client:
                await self.redis_client.close()

async def main():
    """Função principal"""
    monitor = RedisMonitor()
    try:
        await monitor.monitor()
    except KeyboardInterrupt:
        logger.info("Monitoramento interrompido pelo usuário")

if __name__ == "__main__":
    asyncio.run(main()) 