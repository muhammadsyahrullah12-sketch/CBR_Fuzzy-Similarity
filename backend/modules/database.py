import sqlite3
import json
import pandas as pd
from pathlib import Path

from backend.modules.preprocessing import (
    numerical_features, categorical_features, target, id_col,
    compute_normalization_params, save_normalization_params,
)
 
DB_PATH   = Path(__file__).parent.parent / "data" / "case_base.db"
CSV_PATH  = Path(__file__).parent.parent / "data" / "loan_approval_dataset.csv"
 
 
# ── Koneksi ───────────────────────────────────────────────────────────────────
 
def get_connection() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn
 
 
# Inisialisasi DB
 
def init_db(force: bool = False) -> None:
    if DB_PATH.exists() and not force:
        print(f"[DB] Database sudah ada di {DB_PATH}. Skip init. (force=True untuk reset)")
        return
 
    print("[DB] Membaca dataset CSV...")
    df = pd.read_csv(CSV_PATH, sep=",")
    df.columns = df.columns.str.strip()
    for col in df.select_dtypes(include="object").columns:
        df[col] = df[col].str.strip()
 
    # Hitung norm_params dari data ASLI (sebelum encoding/normalisasi)
    print("[DB] Menghitung parameter normalisasi...")
    params = compute_normalization_params(df)
    save_normalization_params(params)
    print("[DB] Parameter normalisasi berhasil disimpan.")
 
    conn = get_connection()
    cur = conn.cursor()
 
    # Tabel cases
    all_cols = [id_col] + numerical_features + categorical_features + [target]
    col_defs_list = []

    for c in all_cols:
        if c == id_col:
            col_defs_list.append(f"{c} INTEGER PRIMARY KEY")
        elif c in numerical_features:
            col_defs_list.append(f"{c} REAL")
        else:
            col_defs_list.append(f"{c} TEXT")

    col_defs = ", ".join(col_defs_list)
 
    cur.execute(f"DROP TABLE IF EXISTS cases")
    cur.execute(f"""
        CREATE TABLE cases (
            {col_defs},
            source TEXT DEFAULT 'initial',
            retained_at TEXT DEFAULT NULL
        )
    """)
 
    # Tabel revise_queue
    cur.execute("DROP TABLE IF EXISTS revise_queue")
    cur.execute("""
        CREATE TABLE revise_queue (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            input_case TEXT NOT NULL,         -- JSON kasus baru (nilai asli)
            top_cases  TEXT NOT NULL,         -- JSON top-5 hasil retrieve
            recommendation TEXT NOT NULL,     -- 'Approved' atau 'Rejected'
            majority_vote TEXT NOT NULL,      -- majority dari top-5
            similarity_score REAL NOT NULL,   -- similarity kasus #1
            status TEXT DEFAULT 'pending',    -- 'pending' | 'revised'
            expert_decision TEXT DEFAULT NULL,
            created_at TEXT DEFAULT (datetime('now','localtime')),
            revised_at TEXT DEFAULT NULL
        )
    """)
 
    # Insert data CSV — gunakan loan_id dari CSV
    insert_cols = [id_col] + numerical_features + categorical_features + [target]
    placeholders = ", ".join(["?"] * len(insert_cols))
    col_names    = ", ".join(insert_cols)
 
    rows = []
    for _, row in df.iterrows():
        vals = [int(row[id_col])]  # loan_id dari CSV
        for col in numerical_features + categorical_features + [target]:
            vals.append(row[col] if col in categorical_features or col == target
                        else float(row[col]))
        rows.append(tuple(vals))
 
    cur.executemany(
        f"INSERT INTO cases ({col_names}) VALUES ({placeholders})",
        rows
    )
 
    conn.commit()
    conn.close()
    print(f"[DB] {len(rows)} kasus berhasil diinsert ke database.")
 
 
# ── Akses kasus ───────────────────────────────────────────────────────────────
 
def get_all_cases() -> list[dict]:
    """Ambil semua kasus dari basis sebagai list of dict (nilai asli)."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM cases")
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows
 
 
def get_case_by_id(case_id: int) -> dict | None:
    """Ambil satu kasus berdasarkan loan_id."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM cases WHERE loan_id = ?", (case_id,))
    row = cur.fetchone()
    conn.close()
    return dict(row) if row else None
 
 
def add_case(case: dict, source: str = "retained") -> int:
    """
    Tambah kasus baru ke basis kasus.
    case berisi nilai ASLI (belum dinormalisasi).
    Returns: loan_id baru
    """
    insert_cols = numerical_features + categorical_features + [target, "source", "retained_at"]
    placeholders = ", ".join(["?"] * len(insert_cols))
    col_names    = ", ".join(insert_cols)
 
    vals = []
    for col in numerical_features:

        if col not in case:
            raise ValueError(
                f"Field '{col}' tidak ditemukan pada case"
            )

        vals.append(float(case[col]))

    for col in categorical_features:

        if col not in case:
            raise ValueError(
                f"Field '{col}' tidak ditemukan pada case"
            )

        vals.append(str(case[col]))

    if target not in case:
        raise ValueError(
            f"Field '{target}' tidak ditemukan pada case"
        )

    vals.append(str(case[target]))

    vals.append(source)
    vals.append(case.get("retained_at", None))
 
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        f"INSERT INTO cases ({col_names}) VALUES ({placeholders})",
        tuple(vals)
    )
    new_id = cur.lastrowid
    conn.commit()
    conn.close()
    return new_id
 
 
def count_cases() -> int:
    """Jumlah total kasus di basis."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM cases")
    count = cur.fetchone()[0]
    conn.close()
    return count
 
 
# ── Revise queue ──────────────────────────────────────────────────────────────
 
def add_to_revise_queue(
    input_case: dict,
    top_cases: list,
    recommendation: str,
    majority_vote: str,
    similarity_score: float,
) -> int:
    """Tambah hasil retrieve+reuse ke antrian revisi pakar."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO revise_queue
          (input_case, top_cases, recommendation, majority_vote, similarity_score)
        VALUES (?, ?, ?, ?, ?)
    """, (
        json.dumps(input_case),
        json.dumps(top_cases),
        recommendation,
        majority_vote,
        similarity_score,
    ))
    new_id = cur.lastrowid
    conn.commit()
    conn.close()
    return new_id
 
 
def get_pending_revisions() -> list[dict]:
    """Ambil semua kasus yang belum direvisi pakar."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT * FROM revise_queue
        WHERE status = 'pending'
        ORDER BY created_at DESC
    """)
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    # Parse JSON fields
    for r in rows:
        r["input_case"] = json.loads(r["input_case"])
        r["top_cases"]  = json.loads(r["top_cases"])
    return rows
 
 
def mark_revised(queue_id: int, expert_decision: str) -> None:
    """Tandai kasus sebagai sudah direvisi."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        UPDATE revise_queue
        SET status = 'revised',
            expert_decision = ?,
            revised_at = datetime('now','localtime')
        WHERE id = ?
    """, (expert_decision, queue_id))
    conn.commit()
    conn.close()
 
 
def get_revision_history() -> list[dict]:
    """Ambil riwayat revisi yang sudah selesai."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT * FROM revise_queue
        WHERE status = 'revised'
        ORDER BY revised_at DESC
    """)
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    for r in rows:
        r["input_case"] = json.loads(r["input_case"])
        r["top_cases"]  = json.loads(r["top_cases"])
    return rows