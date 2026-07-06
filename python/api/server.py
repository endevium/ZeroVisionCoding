import logging
from fastapi import FastAPI
from api.routes.routes import router as analyze_router

logging.getLogger("uvicorn.access").disabled = True
logging.getLogger("uvicorn.access").propagate = False

app = FastAPI()
app.include_router(analyze_router)

