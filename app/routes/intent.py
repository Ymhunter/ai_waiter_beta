from fastapi import APIRouter, Body
from ..config import client

router = APIRouter()

@router.post("/intent")
async def detect_intent(payload: dict = Body(...)):
    message = payload.get("message", "")
    if not message:
        return {"intent": "unknown"}
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are an intent classifier. Decide if the user wants to BOOK an appointment (haircut). Answer only 'book' or 'other'."},
                {"role": "user", "content": message}
            ]
        )
        intent = response.choices[0].message.content.strip().lower()
        if "book" in intent:
            return {"intent": "book"}
        return {"intent": "other"}
    except Exception as e:
        return {"intent": "error", "detail": str(e)}
