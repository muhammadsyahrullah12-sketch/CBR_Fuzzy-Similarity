import json
import numpy as np
import pandas as pd
from pathlib import Path

categorical_features = ["education", "self_employed"]
numerical_features = [
    "no_of_dependents",
    "income_annum",
    "loan_amount",
    "loan_term",
    "cibil_score",
    "residential_assets_value",
    "commercial_assets_value",
    "luxury_assets_value",
    "bank_asset_value",
]

target = "loan_status"
id_col = "loan_id"

# mapping kategorikal fitur ke angka (biner)
categorical_map = {
    "education": {"Graduate": 1, "Not Graduate": 0},
    "self_employed": {"Yes": 1, "No": 0},
}

params_path = Path(__file__).parent.parent / "data" / "norm_params.json"

def encode_categorical(df: pd.DataFrame) -> pd.DataFrame:
    """Encode kolom kategorikal menjadi angka biner 0/1."""
    df = df.copy()

    for col, mapping in categorical_map.items():
        if col in df.columns:

            original_values = df[col].astype(str).str.strip()

            invalid = ~original_values.isin(mapping.keys())

            if invalid.any():
                unknown = original_values[invalid].unique()
                raise ValueError(
                    f"Nilai tidak dikenal pada kolom '{col}': {unknown}. "
                    f"Nilai valid: {list(mapping.keys())}"
                )

            df[col] = original_values.map(mapping)

    return df

def encode_single(case: dict) -> dict:
    """Encode satu kasus (dict) kategorikal ke biner."""
    encoded_case = case.copy()
    for col, mapping in categorical_map.items():
        if col in encoded_case:
            value = str(encoded_case[col]).strip()
            if value not in mapping:
                raise ValueError(
                    f"Nilai '{value}' tidak valid untuk '{col}'. "
                    f"Pilihan: {list(mapping.keys())}"
                )
            encoded_case[col] = mapping[value]
    return encoded_case

# Normalisasi fitur numerik menggunakan min-max scaling

def compute_normalization_params(df: pd.DataFrame) -> dict:
    """Hitung min, max, dan std dari setiap fitur numerik untuk normalisasi Min-Max dan parameter toleransi fuzzy."""

    params = {}
    for col in numerical_features:
        if col in df.columns:
            vals = df[col].dropna()
            min_val = float(vals.min())
            max_val = float(vals.max())

            range_val = max_val - min_val
            if range_val == 0:
                vals_norm = vals * 0.0
            else:
                vals_norm = (vals - min_val) / range_val

            params[col] = {
                "min": min_val,
                "max": max_val,
                "std": float(vals_norm.std(ddof=0)),
            }
    return params

def save_normalization_params(params: dict, path: Path = params_path) -> None:
    """Simpan parameter normalisasi ke file JSON."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump(params, f, indent=2)

def load_normalization_params(path: Path = params_path) -> dict:
    """Muat parameter normalisasi dari file JSON."""
    if not path.exists():
        raise FileNotFoundError(
            f"File parameter normalisasi tidak ditemukan: {path}.\n"
            "Jalankan `init_db()` di database.py terlebih dahulu"
            )
    with open(path, "r") as f:
        return json.load(f)
    
# Normalisasi Min-Max

def minmax_normalize(value: float, col: str, params: dict) -> float:

    if pd.isna(value):
        raise ValueError(f"Nilai '{col}' tidak boleh kosong")

    col_params = params[col]
    min_val = col_params["min"]
    max_val = col_params["max"]

    if max_val == min_val:
        return 0.0

    normalized = (value - min_val) / (max_val - min_val)

    return float(np.clip(normalized, 0.0, 1.0))

def normalize_dataframe(df: pd.DataFrame, params: dict) -> pd.DataFrame:
    """Normalisasi seluruh DataFrame numerikal."""
    df = df.copy()
    for col in numerical_features:
        if col in df.columns:
            df[col] = df[col].apply(lambda x: minmax_normalize(x, col, params))
    return df

def normalize_single(case: dict, params: dict) -> dict:
    """Normalisasi satu kasus (dict) untuk fitur numerik."""
    case = case.copy()
    for col in numerical_features:
        if col in case:
            case[col] = minmax_normalize(case[col], col, params)
    return case

# Fungsi preprocessing utama

def preprocess_dataframe(df: pd.DataFrame, params: dict) -> pd.DataFrame:
    """Preprocessing utama untuk DataFrame: encode kategorikal -> normalisasi numerik."""

    df = encode_categorical(df)
    df = normalize_dataframe(df, params)
    return df

def preprocess_single(case: dict, params: dict) -> dict:
    """Preprocessing utama untuk satu kasus (dict): encode kategorikal -> normalisasi numerik."""
    case = encode_single(case)
    case = normalize_single(case, params)
    return case