from backend.modules.preprocessing import (
    preprocess_single, load_normalization_params,
    numerical_features, categorical_features, target, id_col,
)
from backend.modules.fuzzification import fuzzify_case
from backend.modules.similarity import case_similarity
from backend.modules.database import get_all_cases
 
 
def retrieve(
    new_case_raw: dict,
    k: float = 1.0, #ini harus masukin nilai k nya
    top_n: int = 5,
    threshold: float = 0.0,
) -> list[dict]:
    
    # validasi parameter retrieve
    if top_n <= 0:
        raise ValueError(
            "top_n harus lebih dari 0"
        )

    if not 0.0 <= threshold <= 1.0:
        raise ValueError(
            "threshold harus berada pada rentang [0,1]"
        )

    if k < 0:
        raise ValueError(
            "k tidak boleh negatif"
        )
    
    # 1. Load parameter normalisasi
    norm_params = load_normalization_params()
 
    # 2. Preprocess kasus baru
    processed_new = preprocess_single(new_case_raw, norm_params)
 
    # 3. Fuzzifikasi kasus baru
    fuzzy_new = fuzzify_case(processed_new, norm_params, k)
 
    # 4. Ambil semua kasus dari basis
    all_cases = get_all_cases()

    if not all_cases:
        return []
 
    # 5. Hitung similarity ke semua kasus
    results = []
    for case in all_cases:
        # Preprocess kasus lama
        case_raw = {
            col: case[col]
            for col in numerical_features + categorical_features + [target, id_col]
            if col in case
        }
        processed_old = preprocess_single(
            {
                col: value
                for col, value in case_raw.items()
                if col != target and col != id_col
            },
            norm_params,
        )
        fuzzy_old = fuzzify_case(processed_old, norm_params, k)
 
        # Hitung similarity
        sim_result = case_similarity(
            fuzzy_new=fuzzy_new,
            fuzzy_old=fuzzy_old,
            encoded_new=processed_new,
            encoded_old=processed_old,
        )
 
        if sim_result["total"] >= threshold:
            results.append({
                "loan_id": case.get(id_col),
                "similarity": sim_result["total"],
                "per_feature_similarity": sim_result["per_feature"],
                "case_data": case_raw,
                "decision": str(case.get(target, "")).strip(),
            })
 
    # 6. Urutkan descending berdasarkan similarity
    results.sort(key=lambda x: x["similarity"], reverse=True)
 
    # 7. Ambil top-N dan tambahkan rank
    top_results = results[:top_n]
    for i, r in enumerate(top_results):
        r["rank"] = i + 1
 
    return top_results