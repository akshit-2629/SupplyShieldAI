from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from sqlalchemy.exc import SQLAlchemyError
import logging

logger = logging.getLogger("app")

class AppBaseException(Exception):
    """
    Base exception class for all custom application errors.
    """
    def __init__(self, message: str, error_code: str, status_code: int = 400):
        self.message = message
        self.error_code = error_code
        self.status_code = status_code
        super().__init__(self.message)

class DatabaseException(AppBaseException):
    """
    Exception raised when database queries or transactions fail.
    """
    def __init__(self, message: str = "Database operation failed", error_code: str = "DATABASE_ERROR"):
        super().__init__(message=message, error_code=error_code, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

class NotFoundException(AppBaseException):
    """
    Exception raised when a requested resource is not found.
    """
    def __init__(self, message: str = "Resource not found", error_code: str = "NOT_FOUND"):
        super().__init__(message=message, error_code=error_code, status_code=status.HTTP_404_NOT_FOUND)

class ValidationException(AppBaseException):
    """
    Exception raised during API validation checks.
    """
    def __init__(self, message: str = "Validation failed", error_code: str = "VALIDATION_ERROR"):
        super().__init__(message=message, error_code=error_code, status_code=status.HTTP_400_BAD_REQUEST)

async def app_base_exception_handler(request: Request, exc: AppBaseException) -> JSONResponse:
    """
    Handles custom AppBaseExceptions and formats the JSON response.
    """
    logger.error(f"AppBaseException on {request.url.path}: {exc.message} [{exc.error_code}]")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "message": exc.message,
            "error_code": exc.error_code
        }
    )

async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    """
    Intercepts and formats standard Starlette/FastAPI HTTPExceptions.
    """
    logger.error(f"HTTPException on {request.url.path}: {exc.detail} [{exc.status_code}]")
    
    # Map numeric HTTP status code to string codes
    error_code = "HTTP_ERROR"
    if exc.status_code == status.HTTP_404_NOT_FOUND:
        error_code = "NOT_FOUND"
    elif exc.status_code == status.HTTP_401_UNAUTHORIZED:
        error_code = "UNAUTHORIZED"
    elif exc.status_code == status.HTTP_403_FORBIDDEN:
        error_code = "FORBIDDEN"
    elif exc.status_code == status.HTTP_400_BAD_REQUEST:
        error_code = "BAD_REQUEST"
        
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "message": exc.detail,
            "error_code": error_code
        }
    )

async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """
    Formats validation errors triggered by Pydantic validators.
    """
    errors = exc.errors()
    error_msgs = []
    for err in errors:
        loc = " -> ".join([str(x) for x in err.get("loc", [])])
        msg = err.get("msg", "invalid value")
        error_msgs.append(f"{loc}: {msg}")
    
    full_message = "; ".join(error_msgs) if error_msgs else "Validation error"
    logger.error(f"ValidationError on {request.url.path}: {full_message}")
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "success": False,
            "message": full_message,
            "error_code": "VALIDATION_ERROR"
        }
    )

async def sqlalchemy_exception_handler(request: Request, exc: SQLAlchemyError) -> JSONResponse:
    """
    Catches raw database/SQLAlchemy errors and maps them to clean user-facing errors.
    """
    logger.error(f"Database error on {request.url.path}: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "message": "Database connection failed or operation error",
            "error_code": "DB_CONNECTION_ERROR"
        }
    )

async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Catch-all exception handler for uncaught runtime errors.
    """
    logger.critical(f"Unhandled exception on {request.url.path}: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "message": "An unexpected internal server error occurred",
            "error_code": "INTERNAL_SERVER_ERROR"
        }
    )

def register_exception_handlers(app):
    """
    Appends handlers to the FastAPI app instance.
    """
    app.add_exception_handler(AppBaseException, app_base_exception_handler)
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(SQLAlchemyError, sqlalchemy_exception_handler)
    app.add_exception_handler(Exception, global_exception_handler)
