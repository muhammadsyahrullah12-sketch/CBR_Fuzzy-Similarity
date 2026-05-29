from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field

from backend.modules.evaluation import (
    run_sensitivity_analysis,
    get_evaluation_results,
    load_and_split_data,
    k_values,
)

router = APIRouter(prefix="/evaluation", tags=["Evaluasi & Sensitivity Analysis"])

# Status evaluasi (sederhana, in-memory)
_eval_running = False


class EvalConfig(BaseModel):
    top_n      : int  = Field(5, ge=1, le=20, description="Jumlah top-N kasus saat retrieve")
    force_split: bool = Field(False, description="Reset split data (generate ulang)")


# Jalankan evaluasi

@router.post("/run")
def run_evaluation(body: EvalConfig, background_tasks: BackgroundTasks):
    """
    Jalankan sensitivity analysis untuk k = 0.1 sampai 1.0.

    Proses ini memakan waktu beberapa menit (854 data uji × 10 nilai k).
    Dijalankan sebagai background task — cek hasilnya via GET /evaluation/results.
    """
    global _eval_running
    if _eval_running:
        raise HTTPException(
            status_code=409,
            detail="Evaluasi sedang berjalan. Tunggu hingga selesai."
        )

    def _run():
        global _eval_running
        _eval_running = True
        try:
            run_sensitivity_analysis(
                force_split=body.force_split,
                top_n=body.top_n,
            )
        finally:
            _eval_running = False

    background_tasks.add_task(_run)

    return {
        "message"  : "Evaluasi dimulai sebagai background task.",
        "k_values" : k_values,
        "info"     : "Cek hasilnya via GET /evaluation/results setelah selesai.",
        "status"   : "running",
    }


# Ambil hasil

@router.get("/results")
def get_results():
    """
    Ambil hasil sensitivity analysis yang sudah tersimpan.
    Kembalikan ringkasan per nilai k + k terbaik.
    """
    global _eval_running

    results = get_evaluation_results()
    if results is None:
        return {
            "status" : "running" if _eval_running else "not_started",
            "message": (
                "Evaluasi sedang berjalan..." if _eval_running
                else "Belum ada hasil evaluasi. Jalankan POST /evaluation/run terlebih dahulu."
            ),
        }

    return {
        "status"     : "running" if _eval_running else "completed",
        "train_size" : results["train_size"],
        "test_size"  : results["test_size"],
        "top_n"      : results["top_n"],
        "summary"    : results["summary"],
        "best_k"     : results["best_k"],
    }


@router.get("/best-k")
def get_best_k():
    """
    Ambil nilai k terbaik dari hasil evaluasi.
    Digunakan untuk mengisi default nilai k di sistem.
    """
    results = get_eval_results()
    if results is None:
        raise HTTPException(
            status_code=404,
            detail="Belum ada hasil evaluasi. Jalankan POST /evaluation/run terlebih dahulu."
        )
    return results["best_k"]


# Reset split

@router.post("/reset-split")
def reset_split():
    """
    Reset dan generate ulang split data.
    Gunakan ini hanya jika ingin mengulang seluruh proses evaluasi dari awal.
    """
    split = load_and_split_data(force=True)
    return {
        "message"   : "Split data berhasil di-reset.",
        "train_size": len(split["train"]),
        "test_size" : len(split["test"]),
    }