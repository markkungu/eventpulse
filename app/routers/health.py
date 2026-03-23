from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get("/health")
async def health_check():
    # Full DB + Redis checks added in issue #4
    return {"status": "ok"}
