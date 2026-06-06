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
    
def build_fuzzy(x_norm: float, std_norm: float) -> FuzzyTrapezoid:
    """
    Membangun satu fuzzy trapezoidal number dari nilai ternormalisasi
    Parameter:
    x_norm: nilai yang sudah dinormalisasi (0-1)
    std_norm: standar deviasi dari fitur yang sudah dinormalisasi, digunakan untuk menentukan spread
    """

    # validasi nilai normalisasi
    if not 0.0 <= x_norm <= 1.0:
        raise ValueError(
            f"x_norm harus berada pada rentang [0,1], dapat {x_norm}"
        )
    if std_norm <= 0:
        raise ValueError(
            f"std_norm harus lebih besar dari 0, dapat {std_norm}"
        )
    
    m1 = max(0.0, x_norm - 2*std_norm)
    m2 = max(0.0, x_norm - std_norm)
    m3 = min(1.0, x_norm + std_norm)
    m4 = min(1.0, x_norm + 2*std_norm)
    return FuzzyTrapezoid(m1, m2, m3, m4, w=1.0)

def fuzzify_case(
        normalized_case: dict,
        normalization_params: dict,
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
        fuzzy_result[col] = build_fuzzy(x_norm, std_norm)

    return fuzzy_result

def fuzzify_dataframe_row(
        row: dict,
        normalization_params: dict,
) -> dict[str, FuzzyTrapezoid]:
    """Fuzzifikasi satu baris DataFrame (dict) untuk fitur numerik."""
    return fuzzify_case(row, normalization_params)