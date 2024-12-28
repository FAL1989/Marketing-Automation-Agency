import aiohttp
from datetime import datetime
from ..config import Settings

class AlertManager:
    def __init__(self, settings: Settings):
        self.webhook_url = settings.slack_webhook_url
        self.environment = "production" if not settings.debug else "development"

    async def send_alert(self, title: str, message: str):
        """
        Envia um alerta para o Slack.
        """
        if not self.webhook_url:
            return

        payload = {
            "text": f"*[{self.environment.upper()}] {title}*\n{message}\n_Timestamp: {datetime.utcnow().isoformat()}_"
        }

        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(self.webhook_url, json=payload) as response:
                    if response.status not in (200, 201):
                        print(f"Erro ao enviar alerta: {response.status}")
            except Exception as e:
                print(f"Erro ao enviar alerta: {str(e)}") 