from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from db.database import engine, Base
from core.exceptions import custom_http_exception_handler, validation_exception_handler
from routers import health, auth, users, events, event_tasks
import models

# Tự động khởi tạo database tables
Base.metadata.create_all(bind=engine)

# Cấu hình Rate Limiter
limiter = Limiter(key_func=get_remote_address)

app = FastAPI(
    title="Event Management API",
    description=(
        "Hệ thống quản lý sự kiện - IT215 FastAPI Project.\n\n"
        "## Tính năng chính\n"
        "- **Authentication**: Đăng ký, đăng nhập, Refresh Token, JWT Bearer\n"
        "- **Events**: CRUD sự kiện (Soft Delete), quản lý thành viên ban tổ chức\n"
        "- **Event Tasks**: CRUD công việc, giao việc, workflow, search/filter/sort/phân trang\n"
        "- **Comments**: Trao đổi bình luận trên công việc sự kiện\n"
        "- **Authorization**: Phân quyền RBAC (OWNER / MEMBER / ASSIGNEE)\n"
        "- **Activity Log**: Lịch sử thao tác quan trọng\n"
        "- **Rate Limiting**: Chống brute-force trên endpoint đăng nhập\n"
    ),
    version="2.0.0",
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Cấu hình CORS
origins = [
    "http://localhost:3000",
    "http://localhost:5173",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Đăng ký Exception Handlers
app.add_exception_handler(StarletteHTTPException, custom_http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)

# Đăng ký Routers
app.include_router(health.router)
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(events.router)
app.include_router(event_tasks.router)


