"""
Tahap Fuzzifikasi
Mengkonstruksi Fuzzy Trapezoidal Numbers dari nilai yang sudah dinormalisasi.
"""
from dataclasses import dataclass
from backend.modules.preprocessing import numerical_features

@dataclass
class FuzzyTrapezoid:
    m1: float
    m2: float
    m3: float
    m4: float
    w: float = 1.0

    def to_tuple(self) -> tuple:
        return (self.m1, self.m2, self.m3, self.m4) 
    
    def __repr__(self):
        return f"FuzzyTrapezoid({self.m1:.4f}, {self.m2:.4f}, {self.m3:.4f}, {self.m4:.4f}, w={self.w})"
    
def build_fuzzy(x_norm: float, spread: float) -> FuzzyTrapezoid:
    """
    Membangun satu fuzzy trapezoidal number dari nilai ternormalisasi
    Parameter:
    x_norm: nilai yang sudah dinormalisasi (0-1)
    spread: lebar toleransi fuzzy trapesium (k x std)
    """

    # validasi nilai normalisasi
    if not 0.0 <= x_norm <= 1.0:
        raise ValueError(
            f"x_norm harus berada pada rentang [0,1], dapat {x_norm}"
        )
    
    if spread < 0:
        raise ValueError(
            f"spread tidak boleh negatif, dapat {spread}"
        )
    
    m1 = max(0.0, x_norm - spread)
    m2 = max(0.0, x_norm - spread/2)
    m3 = min(1.0, x_norm + spread/2)
    m4 = min(1.0, x_norm + spread)
    return FuzzyTrapezoid(m1, m2, m3, m4, w=1.0)

def fuzzify_case(
        normalized_case: dict,
        normalization_params: dict,
        k: float,
) -> dict[str, FuzzyTrapezoid]:
    """
    Fuzzifikasi satu kasus (dict) untuk fitur numerik
    """
    fuzzy_result = {}
    for col in numerical_features:
        if col not in normalized_case:
            continue

        x_norm = float(normalized_case[col])

        std_norm = normalization_params[col]["std"]
        spread = k * std_norm
        fuzzy_result[col] = build_fuzzy(x_norm, spread)

    return fuzzy_result

def fuzzify_dataframe_row(
        row: dict,
        normalization_params: dict,
        k: float,
) -> dict[str, FuzzyTrapezoid]:
    """Fuzzifikasi satu baris DataFrame (dict) untuk fitur numerik."""
    return fuzzify_case(row, normalization_params, k)