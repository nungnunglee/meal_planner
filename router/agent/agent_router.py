from fastapi import APIRouter

agent_router = APIRouter(prefix="/agent", tags=["agent"])


@agent_router.get("/list")
async def get_agent_list():
    return {"message": "Hello, World!"}