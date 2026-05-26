import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.services.tracking.router import router as tracking_router
from backend.services.tracking.router import tracker

async def TLE_background_worker():
    while True:
        try:
            if tracker:
                if hasattr(tracker, '_ensure_data_freshness'):
                    tracker._ensure_data_freshness()
                if hasattr(tracker, 'load_catalog'):
                    tracker.load_catalog()
                    print("✓ Satellite catalog background refresh complete.")
        except Exception as e:
            print(f"⚠️ Error running background TLE refresh: {e}")
        await asyncio.sleep(3600)

@asynccontextmanager
async def lifespan(app: FastAPI):
    worker_task = asyncio.create_task(TLE_background_worker())
    yield
    worker_task.cancel()

app = FastAPI(
    title="Project AstroEdge - AI Observatory Core",
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
    cv_val = getattr(tracker, 'cv', "NOT_INITIALIZED")
    return {
        "status": "ONLINE",
        "platform": "Project AstroEdge Core Engine",
        "version": "1.1.0",
        "cv": cv_val
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=False)