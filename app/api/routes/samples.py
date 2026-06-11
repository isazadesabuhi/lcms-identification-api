from fastapi import APIRouter

router = APIRouter()

@router.get("/")
def get_samples_status():
    return {"message": "Samples route is working"}