from datetime import datetime
from backend.modules.database import (
    add_case, mark_revised, get_all_cases,
    get_connection,
)
from backend.modules.preprocessing import (
    compute_normalization_params, save_normalization_params,
    numerical_features, target,
)
import pandas as pd
import json

VALID_DECISIONS = {"Approved", "Rejected"}

def retain(queue_id: int, expert_decision: str) -> dict:

    expert_decision = str(expert_decision).strip()

    if expert_decision not in VALID_DECISIONS:
        raise ValueError(
            f"expert_decision harus salah satu dari {VALID_DECISIONS}"
        )
    
    # 1. Ambil data dari revise_queue
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM revise_queue WHERE id = ?", (queue_id,))
    row = cur.fetchone()
    conn.close()
 
    if not row:
        return {
            "success": False,
            "new_loan_id": None,
            "message": f"Queue ID {queue_id} tidak ditemukan.",
            "total_cases": None,
        }
 
    row = dict(row)
    if str(row["status"]).strip().lower() == "revised":
        return {
            "success": False,
            "new_loan_id": None,
            "message": f"Queue ID {queue_id} sudah pernah diretain.",
            "total_cases": None,
        }
 
    # 2. Siapkan kasus untuk disimpan (nilai asli)
    input_case = json.loads(row["input_case"])
    input_case[target]    = expert_decision
    input_case["retained_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
 
    # 3. Simpan ke basis kasus
    new_id = add_case(input_case, source="retained")
 
    # 4. Tandai antrian sebagai selesai
    mark_revised(queue_id, expert_decision, loan_id=new_id)
 
    # 5. Perbarui norm_params dengan seluruh basis kasus terbaru
    _update_normalization_params()
 
    # 6. Hitung jumlah kasus terkini
    all_cases = get_all_cases()
    total = len(all_cases)
 
    return {
        "success"    : True,
        "new_loan_id": new_id,
        "message"    : (
            f"Kasus berhasil disimpan ke basis kasus (loan_id={new_id}). "
            f"Keputusan pakar: {expert_decision}. "
            f"Total basis kasus sekarang: {total}."
        ),
        "total_cases": total,
    }
 
 
def _update_normalization_params() -> None:
    all_cases = get_all_cases()
    df = pd.DataFrame(all_cases)
 
    # Pastikan kolom numerikal bertipe float
    for col in numerical_features:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
 
    new_params = compute_normalization_params(df)
    save_normalization_params(new_params)