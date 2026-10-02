from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .config import settings
from .database import Base,engine
from .seed import seed
from .routers import auth,products,shop,admin,integrations

Base.metadata.create_all(bind=engine)
seed()

app=FastAPI(title="Smart E-Commerce API",version="1.0.0")
app.add_middleware(CORSMiddleware,allow_origins=[o.strip().rstrip("/") for o in settings.cors_origins.split(",") if o.strip()],allow_credentials=True,allow_methods=["*"],allow_headers=["*"])
app.include_router(auth.router)
app.include_router(products.router)
app.include_router(shop.router)
app.include_router(admin.router)
app.include_router(integrations.router)

@app.get("/")
def root(): return {"message":"Smart E-Commerce API is running","docs":"/docs"}

@app.get("/api/health")
def health(): return {"status":"ok"}
