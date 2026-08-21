from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from db.database import engine, Base
from core.exceptions import custom_http_exception_handler, validation_exception_handler
from routers import health, auth, users
import models

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Event Management API")

app.add_exception_handler(StarletteHTTPException, custom_http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)

app.include_router(health.router)
app.include_router(auth.router)
app.include_router(users.router)