import asyncio
import uvicorn
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
import socketio
import structlog

from app.core.config import settings
from app.core.database import close_connections
from app.api import auth, trading, positions, accounts, reports

log = structlog.get_logger()

# Socket.IO server for real-time position/price streaming
sio = socketio.AsyncServer(async_mode="asgi", cors_allowed_origins="*")


@asynccontextmanager
async def lifespan(app: FastAPI):
    log.info("quantcore_starting", env=settings.APP_ENV)
    yield
    await close_connections()
    log.info("quantcore_shutdown")


app = FastAPI(
    title="QuantCore AI",
    description="Institutional-grade automated trading platform",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(GZipMiddleware, minimum_size=1000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# REST API routers
app.include_router(auth.router, prefix="/api")
app.include_router(trading.router, prefix="/api")
app.include_router(positions.router, prefix="/api")
app.include_router(accounts.router, prefix="/api")
app.include_router(reports.router, prefix="/api")


# Socket.IO events
@sio.event
async def connect(sid, environ, auth):
    log.info("ws_connect", sid=sid)
    await sio.emit("connected", {"status": "ok"}, to=sid)


@sio.event
async def disconnect(sid):
    log.info("ws_disconnect", sid=sid)


@sio.event
async def subscribe_account(sid, data):
    account_id = data.get("account_id")
    if account_id:
        await sio.enter_room(sid, f"account:{account_id}")
        log.info("ws_subscribed", sid=sid, account=account_id)


@app.get("/health")
async def health():
    return {"status": "ok", "service": "QuantCore AI", "version": "1.0.0"}


# Mount Socket.IO as ASGI sub-app
socket_app = socketio.ASGIApp(sio, other_asgi_app=app)

if __name__ == "__main__":
    uvicorn.run(
        "app.main:socket_app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        loop="uvloop",
    )
