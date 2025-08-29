from fastapi import APIRouter

food_router = APIRouter(prefix="/food", tags=["food"])


@food_router.get("/list")
async def get_food_list():
    return {"message": "Hello, World!"}