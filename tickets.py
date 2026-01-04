from fastapi import APIRouter, HTTPException
from datetime import datetime
import uuid
from db import tickets_ref

router = APIRouter()


@router.post("/tickets")
def create_ticket(payload: dict):
    waste_id = f"WT-{uuid.uuid4().hex[:6].upper()}"

    ticket = {
        "wasteId": waste_id,
        "citizenId": payload.get("citizenId", "demo-citizen"),
        "classification": payload.get("classification", "unknown"),
        "status": "pending",
        "location": payload.get("location"),
        "ecoPointsAwarded": 0,

        # 🔽 ADDED (non-breaking)
        "collectorId": None,
        "proofImageUrl": None,
        "timestamps": {
            "created": datetime.utcnow().isoformat(),
            "collected": None,
            "recycled": None,
        },

        # existing fields (kept as-is)
        "createdAt": datetime.utcnow().isoformat(),
        "updatedAt": datetime.utcnow().isoformat(),
    }

    tickets_ref.document(waste_id).set(ticket)
    return ticket


@router.get("/tickets")
def get_tickets():
    docs = tickets_ref.stream()
    return [doc.to_dict() for doc in docs]


# 🔥 NEW ENDPOINT (CRITICAL FIX)
@router.put("/tickets/{waste_id}/status")
def update_ticket_status(waste_id: str, payload: dict):
    doc_ref = tickets_ref.document(waste_id)
    doc = doc_ref.get()

    if not doc.exists:
        raise HTTPException(status_code=404, detail="Ticket not found")

    ticket = doc.to_dict()
    now = datetime.utcnow().isoformat()

    status = payload.get("status")
    collector_id = payload.get("collectorId")
    proof_image = payload.get("proofImageUrl")

    if status:
        ticket["status"] = status

        if status == "collected":
            ticket["timestamps"]["collected"] = now

        if status == "recycled":
            ticket["timestamps"]["recycled"] = now
            ticket["ecoPointsAwarded"] = 15

    if collector_id:
        ticket["collectorId"] = collector_id

    if proof_image:
        ticket["proofImageUrl"] = proof_image

    ticket["updatedAt"] = now

    doc_ref.set(ticket)
    return ticket
