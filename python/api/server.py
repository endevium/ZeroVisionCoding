from fastapi import FastAPI
from api.routes.routes import router as analyze_router

app = FastAPI()

app.include_router(analyze_router)

