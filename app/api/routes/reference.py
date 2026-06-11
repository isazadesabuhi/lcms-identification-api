from fastapi import APIRouter

router = APIRouter()

@router.get("/")
def get_reference_status():
    return {"message": "Reference library route is working"}