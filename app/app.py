from fastapi import FastAPI # type: ignore
from .routes import image

app = FastAPI(title="Video handling endpoint")

@app.get("/")
def read_root():
    return {"Hello": "Word"}

app.include_router(image.router)
