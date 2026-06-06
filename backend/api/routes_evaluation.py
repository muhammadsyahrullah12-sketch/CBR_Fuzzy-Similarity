from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field

from backend.modules.evaluation import (
    run_evaluation as run_model_evaluation,
    get_evaluation_results,
    load_and_split_data,
)

router = APIRouter(prefix="/evaluation", tags=["Evaluasi"])

# Status evaluasi (sederhana, in-memory)
_eval_running = False


class EvalConfig(BaseModel):
    top_n      : int  = Field(5, ge=1, le=20, description="Jumlah top-N kasus saat retrieve")
    force_split: bool = Field(False, description="Reset split data (generate ulang)")


# Jalankan evaluasi

@router.post("/run")
def run_evaluation(body: EvalConfig, background_tasks: BackgroundTasks):
    """
    Jalankan evaluasi performa sistem CBR menggunakan data test.

    Proses dijalankan sebagai background task.
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
            run_model_evaluation(
                force_split=body.force_split,
                top_n=body.top_n,
            )
        finally:
            _eval_running = False

    background_tasks.add_task(_run)

    return {
        "message"  : "Evaluasi dimulai sebagai background task.",
        "info"     : "Cek hasilnya via GET /evaluation/results setelah selesai.",
        "status"   : "running",
    }


# Ambil hasil

@router.get("/results")
def get_results():
    global _eval_running

    results = get_evaluation_results()

    if results is None:
        return {
            "status": "running" if _eval_running else "not_started",
            "message": (
                "Evaluasi sedang berjalan..."
                if _eval_running
                else "Belum ada hasil evaluasi."
            ),
        }

    metrics = results["metrics"]

    return {
        "status": "running" if _eval_running else "completed",
        "train_size": results["train_size"],
        "test_size": results["test_size"],
        "top_n": results["top_n"],

        "accuracy": metrics["accuracy"],
        "precision": metrics["precision"],
        "recall": metrics["recall"],
        "f1_score": metrics["f1_score"],

        "confusion_matrix": {
            "tp": metrics["tp"],
            "tn": metrics["tn"],
            "fp": metrics["fp"],
            "fn": metrics["fn"],
        }
    }

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