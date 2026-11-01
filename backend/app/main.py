from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.app.core.config import settings
from backend.app.database import engine, Base
from backend.app import models

# Import API Routers
from backend.app.api.products import router as products_router
from backend.app.api.skus import router as skus_router
from backend.app.api.locations import router as locations_router
from backend.app.api.inventory import router as inventory_router
from backend.app.api.reservations import router as reservations_router
from backend.app.api.orders import router as orders_router
from backend.app.api.transfers import router as transfers_router
from backend.app.api.shipments import router as shipments_router
from backend.app.api.replenishment import router as replenishment_router
from backend.app.api.anomalies import router as anomalies_router
from backend.app.api.analytics import router as analytics_router
from backend.app.api.generator import router as generator_router
from backend.app.api.validation import router as validation_router
from backend.app.api.audit import router as audit_router

# Ensure schema exists
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="StockMind AI API",
    description="Unified Inventory Intelligence & Operations Platform — Every Unit Accounted For.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health endpoint
@app.get("/health", tags=["Health"])
def health():
    return {
        "status": "healthy",
        "service": "StockMind AI API",
        "environment": settings.APP_ENV,
        "database": "connected"
    }

@app.get("/", tags=["Root"])
def root():
    return {
        "application": "StockMind AI",
        "tagline": "Unified Inventory Intelligence. Every Unit Accounted For.",
        "status": "operational",
        "version": "1.0.0",
        "api_documentation": "/docs"
    }

# Include all routers under /api/v1
app.include_router(products_router, prefix=settings.API_PREFIX)
app.include_router(skus_router, prefix=settings.API_PREFIX)
app.include_router(locations_router, prefix=settings.API_PREFIX)
app.include_router(inventory_router, prefix=settings.API_PREFIX)
app.include_router(reservations_router, prefix=settings.API_PREFIX)
app.include_router(orders_router, prefix=settings.API_PREFIX)
app.include_router(transfers_router, prefix=settings.API_PREFIX)
app.include_router(shipments_router, prefix=settings.API_PREFIX)
app.include_router(replenishment_router, prefix=settings.API_PREFIX)
app.include_router(anomalies_router, prefix=settings.API_PREFIX)
app.include_router(analytics_router, prefix=settings.API_PREFIX)
app.include_router(generator_router, prefix=settings.API_PREFIX)
app.include_router(validation_router, prefix=settings.API_PREFIX)
app.include_router(audit_router, prefix=settings.API_PREFIX)
