from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get("/")
def home():
    return {
        "message": "Welcome to CareerOps API!",
        "status": "running",
    }


@router.get("/health")
def health_check():
    return {"status": "healthy"}
