from typing import Dict, List, Set
from collections import defaultdict

class CacheDependencyManager:
    """
    Gerencia dependências entre chaves de cache e tags
    """
    def __init__(self):
        # Dependências diretas (key -> [dependencies])
        self._dependencies: Dict[str, Set[str]] = defaultdict(set)
        
        # Dependências reversas (key -> [dependent_keys]) 
        self._reverse_dependencies: Dict[str, Set[str]] = defaultdict(set)
        
        # Mapeamento tag -> keys
        self._tag_to_keys: Dict[str, Set[str]] = defaultdict(set)
        
        # Mapeamento key -> tags
        self._key_to_tags: Dict[str, Set[str]] = defaultdict(set)

    def add_dependencies(self, key: str, dependencies: List[str]) -> None:
        """
        Adiciona dependências para uma chave
        """
        if not dependencies:
            return
            
        # Adiciona dependências diretas
        self._dependencies[key].update(dependencies)
        
        # Adiciona dependências reversas
        for dep in dependencies:
            self._reverse_dependencies[dep].add(key)

    def add_tags(self, key: str, tags: List[str]) -> None:
        """
        Adiciona tags para uma chave
        """
        if not tags:
            return
            
        # Adiciona tags para a chave
        self._key_to_tags[key].update(tags)
        
        # Adiciona chave para as tags
        for tag in tags:
            self._tag_to_keys[tag].add(key)

    def get_dependent_keys(self, key: str) -> Set[str]:
        """
        Retorna todas as chaves que dependem da chave fornecida
        """
        dependent_keys = set()
        
        # Adiciona dependentes diretos
        dependent_keys.update(self._reverse_dependencies[key])
        
        # Adiciona chaves com as mesmas tags
        for tag in self._key_to_tags[key]:
            dependent_keys.update(self._tag_to_keys[tag])
            
        return dependent_keys

    def remove_key(self, key: str) -> None:
        """
        Remove uma chave e suas dependências
        """
        # Remove dependências diretas
        if key in self._dependencies:
            for dep in self._dependencies[key]:
                self._reverse_dependencies[dep].discard(key)
            del self._dependencies[key]
            
        # Remove dependências reversas
        if key in self._reverse_dependencies:
            for dep_key in self._reverse_dependencies[key]:
                self._dependencies[dep_key].discard(key)
            del self._reverse_dependencies[key]
            
        # Remove tags
        if key in self._key_to_tags:
            for tag in self._key_to_tags[key]:
                self._tag_to_keys[tag].discard(key)
            del self._key_to_tags[key]

    def clear(self) -> None:
        """
        Limpa todas as dependências
        """
        self._dependencies.clear()
        self._reverse_dependencies.clear()
        self._tag_to_keys.clear()
        self._key_to_tags.clear()

# Instância global do gerenciador de dependências
dependency_manager = CacheDependencyManager() 