"""
FinMind AI - Frontend static file server
Run this to serve the frontend on port 3001
"""

from fastapi import FastAPI # type: ignore[import]
from fastapi.staticfiles import StaticFiles # type: ignore[import]
from fastapi.responses import HTMLResponse # type: ignore[import]
import os

app = FastAPI()

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/", response_class=HTMLResponse)
async def index():
    with open("templates/index.html", "r") as f:
        return f.read()

if __name__ == "__main__":
    import uvicorn # type: ignore[import]
    uvicorn.run("server:app", host="0.0.0.0", port=3001, reload=True)
