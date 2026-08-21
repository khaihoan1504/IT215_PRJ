from fastapi import APIRouter

router = APIRouter()

@router.get("/health", tags=["Core"])
def health_check():
    return {"status": "ok", "message": "API is healthy"}