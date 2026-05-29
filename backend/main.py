from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator
from backend.modules.database import init_db
from backend.api.routes_cbr import router as cbr_router
from backend.api.routes_revise import router as revise_router
from backend.api.routes_evaluation import router as eval_router
 
 
# Lifespan: inisialisasi DB saat startup
 
@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Jalankan init_db() sekali saat server pertama kali start."""
    print("[Startup] Inisialisasi database...")
    init_db()   # skip otomatis jika DB sudah ada
    print("[Startup] Server siap.")
    yield
    print("[Shutdown] Server berhenti.")
 
 
# Inisialisasi aplikasi
 
app = FastAPI(
    title       = "Sistem CBR Fuzzy — Loan Approval",
    description = (
        "Case-Based Reasoning dengan Fuzzy Trapezoidal Number "
        "untuk rekomendasi persetujuan pinjaman.\n\n"
        "**Alur:** Retrieve → Reuse → Revise (pakar) → Retain"
    ),
    version     = "1.0.0",
    lifespan    = lifespan,
)
 
 
# CORS — izinkan frontend mengakses API
 
app.add_middleware(
    CORSMiddleware,
    allow_origins     = ["*"],   # ganti dengan URL frontend saat production
    allow_credentials = True,
    allow_methods     = ["*"],
    allow_headers     = ["*"],
)
 
 
# Daftarkan router
 
app.include_router(cbr_router)
app.include_router(revise_router)
app.include_router(eval_router)
 
 
# Root endpoint
 
@app.get("/", tags=["Info"])
def root():
    return {
        "app"    : "Sistem CBR Fuzzy — Loan Approval",
        "version": "1.0.0",
        "docs"   : "/docs",
    }

@app.get("/health", tags=["Info"])
def health_check():
    return {
        "status": "ok"
    }