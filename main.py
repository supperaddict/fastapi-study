from fastapi import FastAPI
from users import router as users_router
from auth import router as auth_router
from tools import router as tools_router
from posts import router as posts_router

app = FastAPI()
app.include_router(tools_router)


app.include_router(users_router)
app.include_router(auth_router)
app.include_router(posts_router)

@app.get("/health")
def health_check():
    return {"status": "ok"}