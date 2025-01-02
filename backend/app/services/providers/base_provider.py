from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

class BaseProvider(ABC):
    @abstractmethod
    async def generate(
        self,
        prompt: str,
        variables: Dict[str, Any],
        model_name: Optional[str] = None
    ) -> str:
        """
        Gera conteúdo usando o provedor de IA.
        
        Args:
            prompt: O prompt base para geração
            variables: Variáveis para substituir no prompt
            model_name: Nome do modelo a ser usado (opcional)
            
        Returns:
            str: O conteúdo gerado
            
        Raises:
            Exception: Se houver erro na geração
        """
        pass
        
    @abstractmethod
    async def validate_api_key(self) -> bool:
        """
        Valida se a API key está funcionando.
        
        Returns:
            bool: True se a API key é válida, False caso contrário
        """
        pass 