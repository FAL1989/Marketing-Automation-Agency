from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

class BaseProvider(ABC):
    @abstractmethod
    async def generate_content(self, prompt: str, parameters: Optional[Dict[str, Any]] = None) -> str:
        """
        Gera conteúdo usando o provedor de IA.
        
        Args:
            prompt: O prompt para geração
            parameters: Parâmetros adicionais para a geração
            
        Returns:
            str: O conteúdo gerado
            
        Raises:
            Exception: Se houver erro na geração
        """
        pass 