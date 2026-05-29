"""
Tahap menghitung Similarity antara kasus baru dengan kasus lama dalam basis
"""

import math

max_COG_distance = math.sqrt(1.25)  # Jarak maksimum antara dua COG dalam unit normalisasi

from backend.modules.fuzzification import FuzzyTrapezoid
from backend.modules.preprocessing import numerical_features, categorical_features


# Hitung COG (Centre of Gravity)

def _cog(ft: FuzzyTrapezoid) -> tuple[float, float]:
    x_star = (ft.m1 + ft.m2 + ft.m3 + ft.m4) / 4.0

    denominator = ft.m4 + ft.m3 - ft.m2 - ft.m1
    if math.isclose(denominator, 0.0):
        y_star = ft.w / 3.0
    else:
        y_star = (ft.w / 3.0) * (1.0 + (ft.m3 - ft.m2) / denominator)

    return x_star, y_star


# Hitung Jarak COG antara dua fuzzy trapezoidal number

def _distance_cog(m: FuzzyTrapezoid, n: FuzzyTrapezoid) -> float:
    x_m, y_m = _cog(m)
    x_n, y_n = _cog(n)
    numerator = math.hypot(x_m - x_n, y_m - y_n)
    return numerator / max_COG_distance


# Hitung Similarity satu pasang fuzzy number

def fuzzy_similarity_xu(m: FuzzyTrapezoid, n: FuzzyTrapezoid) -> float:
    """
    Xu et al. (2010) — Method 1:
      S(M, N) = 1 - Σ|mᵢ - nᵢ| / 8  -  d(M,N) / 2

    Hasil di-clip ke [0, 1] sebagai pengaman numerik.
    """

    # validasi trapezoid M
    if not (m.m1 <= m.m2 <= m.m3 <= m.m4):
        raise ValueError(
            f"Fuzzy trapezoid M tidak valid: {m}"
        )

    # validasi trapezoid N
    if not (n.m1 <= n.m2 <= n.m3 <= n.m4):
        raise ValueError(
            f"Fuzzy trapezoid N tidak valid: {n}"
        )
    
    sum_abs = sum(abs(a - b) for a, b in zip(m.to_tuple(), n.to_tuple()))
    d = _distance_cog(m, n)
    s = 1.0 - (sum_abs / 8.0) - (d / 2.0)
    return float(max(0.0, min(1.0, s)))


# Hitung Similarity fitur kategorikal

def categorical_similarity(val_new: int, val_old: int) -> float:
    """Exact match: 1.0 jika sama, 0.0 jika berbeda."""
    return 1.0 if val_new == val_old else 0.0


# Hitung Similarity total antar dua kasus

def case_similarity(
    fuzzy_new: dict[str, FuzzyTrapezoid],
    fuzzy_old: dict[str, FuzzyTrapezoid],
    encoded_new: dict,
    encoded_old: dict,
) -> dict:
    
    per_feature = {}

    # Fitur numerikal (Fuzzy similarity)
    for col in numerical_features:
        if col in fuzzy_new and col in fuzzy_old:
            per_feature[col] = fuzzy_similarity_xu(fuzzy_new[col], fuzzy_old[col])

    # Fitur kategorikal (exact match)
    for col in categorical_features:
        if col in encoded_new and col in encoded_old:
            per_feature[col] = categorical_similarity(
                int(encoded_new[col]), int(encoded_old[col])
            )

    # Total: rata-rata semua fitur (bobot sama)
    if not per_feature:
        total = 0.0
    else:
        total = sum(per_feature.values()) / len(per_feature)

    return {
        "total": round(total, 6),
        "per_feature": {k: round(v, 6) for k, v in per_feature.items()},
    }