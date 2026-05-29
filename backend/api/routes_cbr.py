from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Literal
 
from backend.modules.retrieve import retrieve
from backend.modules.reuse import reuse
from backend.modules.database import add_to_revise_queue, count_cases
 
router = APIRouter(prefix="/cbr", tags=["CBR - Retrieve & Reuse"])
 
 
# Schema input
 
class NewCaseInput(BaseModel):
    no_of_dependents      : float = Field(..., ge=0, description="Jumlah tanggungan (0-5)")
    education             : Literal["Graduate", "Not Graduate"]   = Field(..., description="'Graduate' atau 'Not Graduate'")
    self_employed         : Literal["Yes", "No"]   = Field(..., description="'Yes' atau 'No'")
    income_annum          : float = Field(..., gt=0, description="Pendapatan tahunan")
    loan_amount           : float = Field(..., gt=0, description="Jumlah pinjaman")
    loan_term             : float = Field(..., gt=0, description="Tenor pinjaman (tahun)")
    cibil_score           : float = Field(..., ge=300, le=900, description="Skor CIBIL (300-900)")
    residential_assets_value : float = Field(..., description="Nilai aset properti")
    commercial_assets_value  : float = Field(..., ge=0, description="Nilai aset komersial")
    luxury_assets_value      : float = Field(..., gt=0, description="Nilai aset mewah")
    bank_asset_value         : float = Field(..., ge=0, description="Nilai aset bank")
 
 
# Endpoint retrieve + reuse
 
@router.post("/retrieve-reuse")
def retrieve_and_reuse(body: NewCaseInput):
    # Konversi input ke dict (tanpa field kontrol)
    new_case = {
        "no_of_dependents"        : body.no_of_dependents,
        "education"               : body.education,
        "self_employed"           : body.self_employed,
        "income_annum"            : body.income_annum,
        "loan_amount"             : body.loan_amount,
        "loan_term"               : body.loan_term,
        "cibil_score"             : body.cibil_score,
        "residential_assets_value": body.residential_assets_value,
        "commercial_assets_value" : body.commercial_assets_value,
        "luxury_assets_value"     : body.luxury_assets_value,
        "bank_asset_value"        : body.bank_asset_value,
    }
 
    # 1. Retrieve
    try:
        top_cases = retrieve(
            new_case_raw=new_case,
        )
    except FileNotFoundError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
 
    # 2. Reuse
    reuse_result = reuse(top_cases)
 
    # 3. Simpan ke revise_queue
    queue_id = add_to_revise_queue(
        input_case      = new_case,
        top_cases       = top_cases,
        recommendation  = reuse_result["recommendation"],
        majority_vote   = reuse_result["majority_vote"],
        similarity_score= reuse_result["similarity_score"],
    )
 
    return {
        "queue_id"   : queue_id,
        "input_case" : new_case,
        "top_cases"  : top_cases,
        "reuse"      : reuse_result,
    }
 
 
# Endpoint info basis kasus
 
@router.get("/cases/count")
def get_cases_count():
    """Kembalikan jumlah total kasus di basis kasus."""
    return {"total_cases": count_cases()}