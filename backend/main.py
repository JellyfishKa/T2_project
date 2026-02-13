from fastapi import FastAPI

from src.routes.llama import router as llama_router
from src.routes.qwen import router as qwen_router
from src.routes.tpro import router as tpro_router

import uvicorn

app = FastAPI()

app.include_router(qwen_router)
app.include_router(tpro_router)
app.include_router(llama_router)

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
