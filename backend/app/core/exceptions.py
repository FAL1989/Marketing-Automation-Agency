from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
import logging

logger = logging.getLogger(__name__)

class NotFoundException(HTTPException):
    def __init__(self, detail: str = "Item não encontrado"):
        super().__init__(status_code=404, detail=detail)

class UnauthorizedException(HTTPException):
    def __init__(self, detail: str = "Não autorizado"):
        super().__init__(status_code=401, detail=detail)

class ForbiddenException(HTTPException):
    def __init__(self, detail: str = "Acesso negado"):
        super().__init__(status_code=403, detail=detail)

class BadRequestException(HTTPException):
    def __init__(self, detail: str = "Requisição inválida"):
        super().__init__(status_code=400, detail=detail)

class ConflictException(HTTPException):
    def __init__(self, detail: str = "Conflito de recursos"):
        super().__init__(status_code=409, detail=detail)

async def handle_validation_error(request: Request, exc: RequestValidationError):
    """
    Handler para erros de validação
    """
    logger.warning(f"Erro de validação: {exc.errors()}")
    return JSONResponse(
        status_code=422,
        content={
            "detail": exc.errors(),
            "body": exc.body
        }
    )

async def handle_http_error(request: Request, exc: StarletteHTTPException):
    """
    Handler para erros HTTP
    """
    logger.warning(f"Erro HTTP {exc.status_code}: {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail}
    ) 