from fastapi import APIRouter # type: ignore

router = APIRouter()

@router.get("/")
def read_root():
    return {"Hello": "Bimage"}