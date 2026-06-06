from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Literal
from backend.modules.database import (
    get_pending_revisions, get_revision_history,
    get_queue_by_id, update_queue,
)
from backend.modules.retain import retain
from backend.modules.retrieve import retrieve
from backend.modules.reuse import reuse
from backend.modules.preprocessing import load_normalization_params
 
router = APIRouter(prefix="/revise", tags=["CBR - Revise & Retain"])
 
 
# Schema input
 
class ReviseDecision(BaseModel):
    expert_decision: Literal["Approved", "Rejected"] = Field(
        ...,
        description="Keputusan final pakar"
    )

class EditQueueInput(BaseModel):
    no_of_dependents      : float = Field(..., ge=0)
    education             : Literal["Graduate", "Not Graduate"]
    self_employed         : Literal["Yes", "No"]
    income_annum          : float = Field(..., gt=0)
    loan_amount           : float = Field(..., gt=0)
    loan_term             : float = Field(..., gt=0)
    cibil_score           : float = Field(..., ge=300, le=900)
    residential_assets_value : float
    commercial_assets_value  : float = Field(..., ge=0)
    luxury_assets_value      : float = Field(..., ge=0)
    bank_asset_value         : float = Field(..., ge=0)
 
 
# Endpoint revise
 
@router.get("/pending")
def get_pending():
    """
    Ambil semua kasus yang sedang menunggu revisi pakar.
    Ditampilkan di sidebar menu aplikasi.
    """
    pending = get_pending_revisions()
    return {
        "total"  : len(pending),
        "items"  : pending,
    }
 
 
@router.get("/history")
def get_history():
    """
    Ambil riwayat kasus yang sudah direvisi dan di-retain.
    """
    history = get_revision_history()
    return {
        "total" : len(history),
        "items" : history,
    }
 
 
# Endpoint edit antrian revisi
@router.put("/{queue_id}/edit")
def edit_queue(queue_id: int, body: EditQueueInput):
    """Edit input_case pada antrian revisi yang masih pending.
    Berguna untuk memperbaiki input_case yang salah input atau kurang lengkap sebelum direvisi pakar.
    """

    # Cek apakah queue_id valid dan masih pending
    queue = get_queue_by_id(queue_id)
    if not queue:
        raise HTTPException(
            status_code=404, 
            detail=f"Queue ID {queue_id} tidak ditemukan."
        )
    
    if queue["status"] != "pending":
        raise HTTPException(
            status_code=400, 
            detail=f"Queue ID {queue_id} sudah direvisi pakar, tidak bisa diedit."
        )
    
    # Update input_case dengan data baru
    new_input_case = {
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

    # retrieve dan reuse ulang dengan input_case yang baru
    try:
        top_cases = retrieve(
            new_case_raw=new_input_case,
            top_n=5,
        )
    except (FileNotFoundError, ValueError) as e:
        raise HTTPException(status_code=500, detail=str(e))
    
    # reuse ulang
    reuse_result = reuse(top_cases)

    # update queue dengan input_case, top_cases, dan reuse_result yang baru
    success = update_queue(
        queue_id=queue_id,
        input_case=new_input_case,
        top_cases=top_cases,
        recommendation=reuse_result["recommendation"],
        majority_vote=reuse_result["majority_vote"],
        similarity_score=reuse_result["similarity_score"],
        confidence=reuse_result.get("confidence"),
        note=reuse_result.get("note"),
    )

    if not success:
        raise HTTPException(
            status_code=400,
            detail=f"Gagal update queue ID {queue_id}."
        )
    
    return {
        "message"       : f"Queue ID {queue_id} berhasil diupdate.",
        "queue_id"      : queue_id,
        "input_case"    : new_input_case,
        "top_cases"     : top_cases,
        "reuse"  : reuse_result,
    }

# Endpoint retain
 
@router.post("/{queue_id}/save")
def save_revision(queue_id: int, body: ReviseDecision):

    result = retain(
        queue_id=queue_id,
        expert_decision=body.expert_decision,
    )

    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["message"])

    return result