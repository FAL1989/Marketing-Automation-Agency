from enum import Enum
from typing import Dict, List
from fastapi import HTTPException, Security, Request, Depends
from app.models.user import User
from app.api.dependencies.auth import get_current_user

class Role(Enum):
    ADMIN = "admin"
    MANAGER = "manager"
    EDITOR = "editor"
    USER = "user"

class RBACService:
    def __init__(self):
        # Define permissões por papel
        self.role_permissions: Dict[Role, List[str]] = {
            Role.ADMIN: ["*"],  # Acesso total
            Role.MANAGER: [
                "content:write", "content:read",
                "analytics:read", "users:read"
            ],
            Role.EDITOR: [
                "content:write", "content:read"
            ],
            Role.USER: [
                "content:read"
            ]
        }
        
    async def check_permission(self, user: User, required_permission: str) -> bool:
        """
        Verifica se o usuário tem a permissão necessária.
        Implementa verificação hierárquica de permissões.
        """
        user_role = Role(user.role)
        user_permissions = self.role_permissions[user_role]
        
        # Admins têm acesso total
        if "*" in user_permissions:
            return True
            
        # Verifica permissão específica
        return required_permission in user_permissions

# Middleware de autorização
async def require_permission(permission: str):
    async def permission_middleware(
        request: Request,
        user: User = Depends(get_current_user)
    ):
        rbac = RBACService()
        if not await rbac.check_permission(user, permission):
            raise HTTPException(
                status_code=403,
                detail="Permissões insuficientes"
            )
        return user
    return permission_middleware 