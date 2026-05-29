import json
import random
import pandas as pd
from pathlib import Path
from sklearn.model_selection import train_test_split

from backend.modules.preprocessing import (
    numerical_features, categorical_features, target, id_col,
    compute_normalization_params, preprocess_single,
)
from backend.modules.fuzzification import fuzzify_case
from backend.modules.similarity import case_similarity
from backend.modules.reuse import reuse

# Path
csv_path = Path(__file__).parent.parent / "data" / "loan_approval_dataset.csv"
split_path = Path(__file__).parent.parent / "data" / "eval_split.json"
eval_results_path = Path(__file__).parent.parent / "data" / "eval_results.json"

k_values = [round(k * 0.1, 1) for k in range(1, 11)] # 0.1, 0.2, ..., 1.0
# random_state = 42
test_size = 0.2

# Load dan Split Data
def load_and_split_data(force: bool = False) -> dict:
    """
    Load dataset dari CSV dan buat split train/test. Simpan split ke JSON untuk konsistensi.
    """

    if split_path.exists() and not force:
        print("[Eval] Split sudah ada. Memuat dari JSON...")
        with open(split_path, "r") as f:
            return json.load(f)
        
    print("[Eval] Membaca dataset dan melakukan split 80/20...")
    df = pd.read_csv(csv_path, sep=",")
    df.columns = df.columns.str.strip()
    for col in df.select_dtypes(include="object").columns:
        df[col] = df[col].str.strip()

    # Generate seed
    random_state = random.randint(0, 10000) if force else 42
    print(f"[Eval] Menggunakan random_state={random_state} untuk split.")

    # Stratified split berdasarkan loan_status
    train_df, test_df = train_test_split(
        df,
        test_size=test_size,
        random_state=random_state,
        stratify=df[target],
    )

    train_records = train_df.to_dict(orient="records")
    test_records = test_df.to_dict(orient="records")

    split_data = {"train": train_records, "test": test_records}

    split_path.parent.mkdir(parents=True, exist_ok=True)
    with open(split_path, "w") as f:
        json.dump(split_data, f, indent=4)

    print(f"[Eval] Split selesai. Train: {len(train_records)} kasus, Test: {len(test_records)} kasus.")
    print(f"[Eval] Split disimpan ke {split_path}.")
    return split_data

# Retrieve untuk evaluasi
def _retrieve_for_evaluation(
    new_case_raw: dict,
    train_cases: list[dict],
    norm_params: dict,
    k: float,
    top_n: int = 5,
) -> list[dict]:
    """
    Retrieve kasus dari basis kasus evaluasi (train_cases)
    dengan proses yang sama seperti retrieve biasa, tapi hanya menggunakan train_cases.
    """

    # Preprocess kasus baru
    case_input = {
        col: new_case_raw[col]
        for col in numerical_features + categorical_features
        if col in new_case_raw
    }
    processed_new = preprocess_single(case_input, norm_params)
    fuzzy_new = fuzzify_case(processed_new, norm_params, k)

    results = []
    for case in train_cases:
        case_input_old = {
            col: case[col]
            for col in numerical_features + categorical_features
            if col in case
        }
        processed_old = preprocess_single(case_input_old, norm_params)
        fuzzy_old = fuzzify_case(processed_old, norm_params, k)

        sim_result = case_similarity(
            fuzzy_new=fuzzy_new,
            fuzzy_old=fuzzy_old,
            encoded_new=processed_new,
            encoded_old=processed_old,
        )

        results.append({
            "loan_id": case.get(id_col),
            "similarity": sim_result["total"],
            "decision": str(case.get(target)).strip(),
        })

    results.sort(key=lambda x: x["similarity"], reverse=True)
    top = results[:top_n]
    for i, r in enumerate(top):
        r["rank"] = i + 1
    return top

# Metrik Evaluasi
def _compute_metrics(y_true: list[str], y_pred: list[str]) -> dict:
    """
    Hitung metrik evaluasi: accuracy, precision, recall, f1-score.
    Positive class dianggap "Approved".
    """
    tp = sum(1 for t, p in zip(y_true, y_pred) if t == "Approved" and p == "Approved")
    tn = sum(1 for t, p in zip(y_true, y_pred) if t == "Rejected" and p == "Rejected")
    fp = sum(1 for t, p in zip(y_true, y_pred) if t == "Rejected" and p == "Approved")
    fn = sum(1 for t, p in zip(y_true, y_pred) if t == "Approved" and p == "Rejected")

    total = len(y_true)
    accuracy = (tp + tn) / total if total > 0 else 0.0
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1_score = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0

    return {
        "accuracy": round(accuracy * 100, 2),
        "precision": round(precision * 100, 2),
        "recall": round(recall * 100, 2),
        "f1_score": round(f1_score * 100, 2),
        "tp": tp, "tn": tn, "fp": fp, "fn": fn,
        "total": total,
    }

# Evaluasi satu nilai k
def evaluate_k(
    k: float,
    train_cases: list[dict],
    test_cases: list[dict],
    norm_params: dict,
    top_n: int = 5,
) -> dict:
    """
    Evaluasi performa CBR untuk satu nilai k tertentu.
    """
    y_true = []
    y_pred = []
    details = []

    for i, test_case in enumerate(test_cases):
        true_label = str(test_case.get(target, "")).strip()

        # Retrieve
        top_cases = _retrieve_for_evaluation(test_case, train_cases, norm_params, k, top_n)

        # Reuse
        reuse_result = reuse(top_cases)
        predicted = reuse_result["recommendation"]

        y_true.append(true_label)
        y_pred.append(predicted)

        details.append({
            "index": i,
            "loan_id": test_case.get(id_col),
            "true_label": true_label,
            "predicted": predicted,
            "correct": true_label == predicted,
            "similarity_top1": top_cases[0]["similarity"] if top_cases else 0,
        })

        if (i + 1) % 100 == 0:
            print(f" [k={k}] {i+1}/{len(test_cases)} selesai...")

    metrics = _compute_metrics(y_true, y_pred)
    return {
        "k": k,
        "metrics": metrics,
        "details": details,
    }

# Sensitivity analysis untuk semua nilai k

def run_sensitivity_analysis(
    force_split: bool = False,
    top_n: int = 5,
) -> dict:
    """
    Jalankan evaluasi untuk semua nilai k (0.1 - 1.0)
    """
    # Load split data
    split_data = load_and_split_data(force=force_split)
    train_cases = split_data["train"]
    test_cases = split_data["test"]

    print(f"Basis kasus untuk evaluasi: {len(train_cases)} kasus.")
    print(f"Kasus uji untuk evaluasi: {len(test_cases)} kasus.")

    # Hitung parameter normalisasi dari train_cases
    train_df = pd.DataFrame(train_cases)
    for col in numerical_features:
        if col in train_df.columns:
            train_df[col] = pd.to_numeric(train_df[col], errors="coerce")
    norm_params = compute_normalization_params(train_df)

    # Evaluasi untuk setiap nilai k
    all_results = []
    for k in k_values:
        print(f"\nEvaluasi untuk k={k}...")
        result = evaluate_k(k, train_cases, test_cases, norm_params, top_n)
        all_results.append(result)
        print(f" Akurasi: {result['metrics']['accuracy']}% | "
              f"F1-Score: {result['metrics']['f1_score']}%")
        
    summary = [
        {
            "k": r["k"],
            "accuracy": r["metrics"]["accuracy"],
            "precision": r["metrics"]["precision"],
            "recall": r["metrics"]["recall"],
            "f1_score": r["metrics"]["f1_score"],
        }
        for r in all_results
    ]

    # K terbaik berdasarkan F1-Score
    best = max(all_results, key=lambda x: x["metrics"]["f1_score"])
    best_k = {"k": best["k"], "metrics": best["metrics"]}

    # Simpan hasil evaluasi ke JSON
    output = {
        "train_size": len(train_cases),
        "test_size": len(test_cases),
        "top_n": top_n,
        "k_values": k_values,
        "summary": summary,
        "best_k": best_k,
        "details": {str(r["k"]): r["details"] for r in all_results},
    }

    with open(eval_results_path, "w") as f:
        json.dump(output, f, indent=2)

    print(f"\nEvaluasi selesai! K terbaik : {best_k['k']} "
          f"(Akurasi : {best_k['metrics']['accuracy']}%, "
          f"F1-Score : {best_k['metrics']['f1_score']}%)")
    print(f"Hasil evaluasi disimpan ke {eval_results_path}.")
    return output

def get_evaluation_results() -> dict:
    """
    Ambil hasil evaluasi dari JSON. Jika belum ada, jalankan evaluasi.
    """
    if eval_results_path.exists():
        print("[Eval] Memuat hasil evaluasi dari JSON...")
        with open(eval_results_path, "r") as f:
            return json.load(f)
    else:
        print("[Eval] Hasil evaluasi belum ditemukan. Menjalankan evaluasi...")
        return run_sensitivity_analysis()