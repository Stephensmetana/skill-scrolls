from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os

app = FastAPI()

# --- Your API routes go here ---
@app.get("/api/hello")
async def hello():
    return {"message": "Backend is running!"}

# Serve built React app (must be last)
if os.path.exists("static"):
    app.mount("/static", StaticFiles(directory="static"), name="static")

    @app.get("/{full_path:path}")
    async def serve_react(full_path: str):
        return FileResponse("static/index.html")
