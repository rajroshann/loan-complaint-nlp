from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.models import User, Prediction
from app.schemas.complaint import ComplaintRequest, PredictionResponse
from app.core.deps import get_current_user
from app.services.model_service import predict as run_model
from app.services.explain_service import explain as run_shap
from app.services.llm_service import explain_in_plain_english

router = APIRouter(tags=["predict"])


@router.post("/predict", response_model=PredictionResponse)
def predict_complaint(
    payload: ComplaintRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = run_model(payload.complaint_text)
    shap_result = run_shap(payload.complaint_text)

    llm_result = explain_in_plain_english(
        predicted_label=result["predicted_label"],
        probability_of_relief=result["probability_of_relief"],
        toward_relief=shap_result["top_words_toward_relief"],
        toward_no_relief=shap_result["top_words_toward_no_relief"],
    )

    db_prediction = Prediction(
        user_id=current_user.id,
        complaint_text=payload.complaint_text,
        predicted_label=result["predicted_label"],
        confidence=result["probability_of_relief"],
    )
    db.add(db_prediction)
    db.commit()

    return PredictionResponse(
        predicted_label=result["predicted_label"],
        probability_of_relief=result["probability_of_relief"],
        meaning=result["meaning"],
        explanation=llm_result["explanation"],
        tip=llm_result["tip"],
        top_words_toward_relief=shap_result["top_words_toward_relief"],
        top_words_toward_no_relief=shap_result["top_words_toward_no_relief"],
    )