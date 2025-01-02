from typing import Optional, Dict, Any
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import httpx
from datetime import datetime, timedelta
from .config import settings
from .events import EventType

logger = logging.getLogger(__name__)

class NotificationService:
    """
    Serviço para envio de notificações
    """
    def __init__(self):
        self.smtp_enabled = bool(settings.SMTP_HOST)
        self.slack_enabled = bool(settings.SLACK_WEBHOOK_URL)
        self._last_notifications = {}
        self._throttle_window = timedelta(minutes=5)
        self._throttle_limit = 3
    
    def _should_throttle(self, event_type: str) -> bool:
        """
        Verifica se a notificação deve ser throttled
        """
        now = datetime.utcnow()
        if event_type not in self._last_notifications:
            self._last_notifications[event_type] = []
            return False
        
        # Remove notificações antigas
        self._last_notifications[event_type] = [
            ts for ts in self._last_notifications[event_type]
            if now - ts < self._throttle_window
        ]
        
        # Verifica limite
        if len(self._last_notifications[event_type]) >= self._throttle_limit:
            return True
        
        self._last_notifications[event_type].append(now)
        return False
    
    def _format_event_data(self, event_data: Dict[str, Any]) -> str:
        """
        Formata os dados do evento para exibição
        """
        lines = []
        for key, value in event_data.items():
            if isinstance(value, dict):
                lines.append(f"{key.title()}:")
                for sub_key, sub_value in value.items():
                    lines.append(f"  {sub_key.title()}: {sub_value}")
            else:
                lines.append(f"{key.title()}: {value}")
        return "\n".join(lines)
    
    async def send_email(self, subject: str, body: str, to_email: str):
        """
        Envia um email
        """
        if not self.smtp_enabled:
            logger.warning("SMTP não configurado")
            return
        
        try:
            msg = MIMEMultipart()
            msg["From"] = settings.SMTP_FROM_EMAIL
            msg["To"] = to_email
            msg["Subject"] = subject
            
            msg.attach(MIMEText(body, "plain"))
            
            with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
                if settings.SMTP_TLS:
                    server.starttls()
                if settings.SMTP_USER and settings.SMTP_PASSWORD:
                    server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
                server.send_message(msg)
                
            logger.info(f"Email enviado para {to_email}")
            
        except Exception as e:
            logger.error(f"Erro ao enviar email: {str(e)}")
    
    async def send_slack(self, message: str, channel: Optional[str] = None):
        """
        Envia uma mensagem para o Slack
        """
        if not self.slack_enabled:
            logger.warning("Slack não configurado")
            return
        
        try:
            payload = {
                "text": message,
                "channel": channel
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    settings.SLACK_WEBHOOK_URL,
                    json=payload
                )
                response.raise_for_status()
                
            logger.info("Mensagem enviada para o Slack")
            
        except Exception as e:
            logger.error(f"Erro ao enviar mensagem para o Slack: {str(e)}")
    
    async def notify_security_event(self, event_type: EventType, event_data: Dict[str, Any]):
        """
        Notifica sobre um evento de segurança
        """
        if self._should_throttle(str(event_type)):
            logger.info(f"Notificação throttled para evento {event_type}")
            return
        
        subject = f"Alerta de Segurança: {event_type.value}"
        body = f"""
        Um evento de segurança foi detectado:
        
        Tipo: {event_type.value}
        Data/Hora: {datetime.utcnow().isoformat()}
        
        Detalhes:
        {self._format_event_data(event_data)}
        """
        
        # Envia email
        await self.send_email(subject, body, settings.AUDIT_ALERT_EMAIL)
        
        # Envia para o Slack se for um evento crítico
        if event_data.get("severity") == "critical":
            await self.send_slack(f"🚨 {subject}\n{body}")

    async def send_event(self, event_type: EventType, event_data: Dict[str, Any]):
        """
        Envia um evento para os canais configurados
        """
        if self._should_throttle(str(event_type)):
            logger.info(f"Evento throttled: {event_type}")
            return
        
        logger.info(f"Enviando evento: {event_type}", extra=event_data)
        
        # Formata a mensagem
        message = f"""
        Evento: {event_type.value}
        Data/Hora: {datetime.utcnow().isoformat()}
        
        Detalhes:
        {self._format_event_data(event_data)}
        """
        
        # Envia para o Slack se configurado
        if self.slack_enabled:
            await self.send_slack(message)
        
        # Envia por email se configurado
        if self.smtp_enabled:
            subject = f"Evento do Sistema: {event_type.value}"
            await self.send_email(subject, message, settings.AUDIT_ALERT_EMAIL)

notification_service = NotificationService() 