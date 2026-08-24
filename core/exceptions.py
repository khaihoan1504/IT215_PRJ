from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException


class CustomException(StarletteHTTPException):
    def __init__(self, status_code: int, detail: str):
        super().__init__(status_code=status_code, detail=detail)


def NotFoundException(detail: str = "Resource not found"):
    return CustomException(status_code=status.HTTP_404_NOT_FOUND, detail=detail)


def BadRequestException(detail: str = "Bad request"):
    return CustomException(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)


def ForbiddenException(detail: str = "Forbidden access"):
    return CustomException(status_code=status.HTTP_403_FORBIDDEN, detail=detail)


async def custom_http_exception_handler(request: Request, exc: StarletteHTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error_code": exc.status_code,
            "message": exc.detail,
        },
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "success": False,
            "error_code": 422,
            "message": "Validation Error",
            "details": exc.errors(),
        },
    )

