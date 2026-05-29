from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Literal
from backend.modules.database import get_pending_revisions, get_revision_history
from backend.modules.retain import retain
 
router = APIRouter(prefix="/revise", tags=["CBR - Revise & Retain"])
 
 
# Schema input
 
class ReviseDecision(BaseModel):
    expert_decision: Literal["Approved", "Rejected"] = Field(
        ...,
        description="Keputusan final pakar"
    )
 
 
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