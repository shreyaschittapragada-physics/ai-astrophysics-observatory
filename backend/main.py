import os
import sys
import uvicorn
from fastapi import FastAPI

# This line fixes the paths automatically by grabbing your root folder location
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Now absolute paths work perfectly when running the file directly!
from backend.api.routes.iss import router as iss_router

app = FastAPI(
    title="ISS Space Tracker API",
    version="1.0.0"
)

app.include_router(iss_router)

if __name__ == "__main__":
    print("\n🚀 Firing up the ISS Tracker Engine...")
    uvicorn.run(app, host="127.0.0.1", port=8000)