from fastapi import APIRouter

router = APIRouter()

@router.get("/")
def get_matching_status():
    return {"message": "Matching route is working"}