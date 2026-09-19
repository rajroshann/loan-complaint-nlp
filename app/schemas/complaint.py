from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


class ComplaintRequest(BaseModel):
    """What /predict expects."""
    complaint_text: str = Field(
        ..., min_length=10,
        description="The consumer complaint narrative text"
    )
    # min_length=10 blocks empty/near-empty submissions (e.g. someone submitting
    # just "hi") with an automatic 422, before it ever reaches your ML model.


class PredictionResponse(BaseModel):
    """What /predict returns."""
    predicted_label: str          # e.g. "Relief" or "No Relief"
    probability_of_relief: float  # e.g. 0.3885 — renamed from `confidence`, per earlier discussion
    meaning: str                  # plain-English explanation of what this label means
    explanation: str
    tip : str 
    top_words_toward_relief: list[dict]
    top_words_toward_no_relief: list[dict]


class HistoryItem(BaseModel):
    """One row in a user's /history list - built from a Prediction DB row."""
    id: int
    complaint_text: str
    predicted_label: str
    confidence: float
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)



# Schemas alone don't run as scripts (same as database.py/models.py last time — these are [CREATE], not [RUN]). Test by validating them directly in a throwaway script: