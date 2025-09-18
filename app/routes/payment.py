from fastapi import APIRouter, Body, HTTPException
from fastapi.responses import JSONResponse

router = APIRouter()

@router.post("/pay/klarna")
async def pay_with_klarna(payload: dict = Body(...)):
    try:
        service = payload.get("service")
        customer = payload.get("customer_name")
        amount = payload.get("amount")
        booking_id = payload.get("booking_id")
        if not all([service, customer, amount, booking_id]):
            raise HTTPException(status_code=400, detail="Missing fields")
        return JSONResponse({"order_id": f"ORDER-{booking_id}"})
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Klarna error: {str(e)}")
