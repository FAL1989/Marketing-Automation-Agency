from typing import List
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
from app.core.config import settings
from jinja2 import Environment, select_autoescape, PackageLoader

# Configuração do template engine
env = Environment(
    loader=PackageLoader('app', 'templates/email'),
    autoescape=select_autoescape(['html', 'xml'])
)

class EmailService:
    def __init__(self):
        self.config = ConnectionConfig(
            MAIL_USERNAME=settings.MAIL_USERNAME,
            MAIL_PASSWORD=settings.MAIL_PASSWORD,
            MAIL_FROM=settings.MAIL_FROM,
            MAIL_PORT=settings.MAIL_PORT,
            MAIL_SERVER=settings.MAIL_SERVER,
            MAIL_TLS=True,
            MAIL_SSL=False,
            USE_CREDENTIALS=True
        )
        self.fastmail = FastMail(self.config)
        
    async def send_backup_codes(self, email: str, backup_codes: List[str]) -> None:
        """
        Envia códigos de backup MFA por email
        """
        template = env.get_template('mfa_backup_codes.html')
        html = template.render(
            backup_codes=backup_codes,
            app_name=settings.APP_NAME
        )
        
        message = MessageSchema(
            subject=f"{settings.APP_NAME} - Seus códigos de backup MFA",
            recipients=[email],
            body=html,
            subtype="html"
        )
        
        await self.fastmail.send_message(message)
        
    async def send_mfa_recovery(self, email: str, recovery_link: str) -> None:
        """
        Envia link de recuperação MFA
        """
        template = env.get_template('mfa_recovery.html')
        html = template.render(
            recovery_link=recovery_link,
            app_name=settings.APP_NAME
        )
        
        message = MessageSchema(
            subject=f"{settings.APP_NAME} - Recuperação de MFA",
            recipients=[email],
            body=html,
            subtype="html"
        )
        
        await self.fastmail.send_message(message)
        
    async def send_mfa_disabled_alert(self, email: str) -> None:
        """
        Envia alerta quando MFA é desabilitado
        """
        template = env.get_template('mfa_disabled_alert.html')
        html = template.render(
            app_name=settings.APP_NAME
        )
        
        message = MessageSchema(
            subject=f"{settings.APP_NAME} - Alerta de Segurança: MFA Desabilitado",
            recipients=[email],
            body=html,
            subtype="html"
        )
        
        await self.fastmail.send_message(message) 