import re
import joblib
from pathlib import Path

from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
from nltk.tokenize import word_tokenize

# Path(__file__).resolve() gets THIS file's absolute location, then .parent
# walks up folders - this makes the path work no matter what directory you
# run `uvicorn` from (your terminal's "current folder" isn't reliable to
# assume - this is).
BASE_DIR = Path(__file__).resolve().parent.parent.parent
ARTIFACTS_DIR = BASE_DIR / "ml_artifacts"

# Loaded ONCE, at import time (i.e. once when the server starts) - not
# inside the predict function below, which would reload from disk on
# every single request.
_model = joblib.load(ARTIFACTS_DIR / "final_model.pkl")
_tfidf = joblib.load(ARTIFACTS_DIR / "final_tfidf.pkl")
_threshold = joblib.load(ARTIFACTS_DIR / "classification_threshold.pkl")

_stop_words = set(stopwords.words("english"))
_lemmatizer = WordNetLemmatizer()


def _clean_text(text: str) -> str:
    """MUST exactly match the cleaning used when the model was trained -
    any difference here silently produces wrong predictions, since the
    model has never seen text processed a different way."""
    text = str(text).lower()
    text = re.sub(r"x{2,}", " ", text)
    text = re.sub(r"[^a-z\s]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _preprocess(text: str) -> str:
    cleaned = _clean_text(text)
    tokens = word_tokenize(cleaned)
    tokens = [w for w in tokens if w not in _stop_words and len(w) > 1]
    tokens = [_lemmatizer.lemmatize(w) for w in tokens]
    return " ".join(tokens)


def predict(complaint_text: str) -> dict:
    processed = _preprocess(complaint_text)
    vector = _tfidf.transform([processed])

    probability_of_relief = _model.predict_proba(vector)[0][1]
    label = "Relief" if probability_of_relief >= _threshold else "No Relief"

    meaning = (
        "Historically, complaints like this were resolved with a monetary refund/credit "
        "or a non-monetary correction (e.g. fixing a credit report error, reversing a fee)."
        if label == "Relief" else
        "Historically, complaints like this were closed with a written explanation from "
        "the company, without a refund or account correction."
    )

    return {
        "predicted_label": label,
        "probability_of_relief": round(float(probability_of_relief), 4),
        "meaning": meaning,
    }


if __name__ == "__main__":
    # A spread of realistic complaint styles, to see the score actually move
    # with the language used - not just two fixed inputs.

    sample_1 = "I have been trying to modify my mortgage for months and the company keeps ignoring my calls and refuses to help."

    sample_2 = "Thank you for resolving my issue quickly, everything was explained clearly and I have no complaints."

    sample_3 = (
        "On March 3rd 2024 I was charged an unauthorized late fee of $450 even though "
        "my payment was submitted on time. I have my bank statement and payment "
        "confirmation number as proof. I have called four times and been given four "
        "different answers with no refund issued."
    )

    sample_4 = (
        "My loan servicer reported my account as delinquent to the credit bureau even "
        "though I was enrolled in an approved forbearance plan. This has damaged my "
        "credit score and I have documentation from the forbearance agreement showing "
        "this was reported in error."
    )

    sample_5 = (
        "I disagree with the interest rate calculation on my statement. I would like "
        "someone to explain how it was calculated."
    )

    samples = {
        "Sample 1 (vague frustration, no evidence)": sample_1,
        "Sample 2 (satisfied, closed)": sample_2,
        "Sample 3 (specific date, dollar amount, proof, repeated contact)": sample_3,
        "Sample 4 (documented error, credit bureau harm)": sample_4,
        "Sample 5 (mild, just asking for clarification)": sample_5,
    }

    for description, text in samples.items():
        print(description)
        print(predict(text))
        print()