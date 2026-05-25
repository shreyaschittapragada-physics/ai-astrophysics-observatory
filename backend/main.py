import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.services.tracking.router import router as tracking_router
from backend.services.tracking.router import tracker

async def TLE_background_worker():
    """Background loop that updates satellite vectors every hour without blocking traffic"""
    while True:
        try:
            if tracker:
                tracker.fetch_and_cache_tle()
        except Exception as e:
            print(f"⚠️ Error running background TLE refresh: {e}")
        # Sleep for 1 hour (3600 seconds) before checking Celestrak again
        await asyncio.sleep(3600)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handles server startup and shutdown background routines securely"""
    # Startup: Launch the worker task daemon
    worker_task = asyncio.create_task(TLE_background_worker())
    yield
    # Shutdown: Clean up task allocations on exit
    worker_task.cancel()

app = FastAPI(
    title="Project AstroEdge - AI Observatory Core",
    description="Asynchronous backend API server for autonomous satellite tracking with background worker caching.",
    version="1.1.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(tracking_router)

@app.get("/")
async def root_status():
    return {
        "status": "ONLINE",
        "platform": "Project AstroEdge Core Engine",
        "version": "1.1.0"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="127.0.0.1", port=8000, reload=True)
