


import numpy as np
import shap

from app.services.model_service import _model, _tfidf, _preprocess

# Every TF-IDF feature name, in the same order the model's coefficients are
# stored in - index 0 here corresponds to _model.coef_[0][0], and so on.
_feature_names = np.array(_tfidf.get_feature_names_out())

# The "baseline" SHAP compares every complaint against. For TF-IDF, an
# all-zero vector is the natural baseline - it represents "a document
# containing none of the vocabulary," which is what a word's TF-IDF value
# is measured relative to anyway. max_samples=1 because there's only one
# baseline point (an all-zero vector), not a real sample to draw many from.
_background = shap.maskers.Independent(np.zeros((1, len(_feature_names))), max_samples=1)
_explainer = shap.LinearExplainer(_model, _background)


def explain(complaint_text: str, top_n: int = 5) -> dict:
    """
    Returns the top words pushing toward Relief, and the top words pushing
    toward No Relief, for this specific complaint - not a general importance
    list, but what mattered for THIS text.
    """
    processed = _preprocess(complaint_text)
    vector = _tfidf.transform([processed])
    dense_vector = vector.toarray()

    shap_values = _explainer.shap_values(dense_vector)[0]  # one value per feature

    # Only words that actually appear in this complaint have a nonzero
    # TF-IDF value - and therefore a nonzero SHAP contribution. No point
    # listing the other 59,000+ absent words, which all contribute exactly 0.
    present_indices = dense_vector[0].nonzero()[0]

    contributions = [
        {"word": str(_feature_names[i]), "impact": round(float(shap_values[i]), 4)}
        for i in present_indices
    ]
    contributions.sort(key=lambda c: c["impact"], reverse=True)

    toward_relief = [c for c in contributions if c["impact"] > 0][:top_n]
    toward_no_relief = sorted(
        [c for c in contributions if c["impact"] < 0], key=lambda c: c["impact"]
    )[:top_n]

    return {
        "top_words_toward_relief": toward_relief,
        "top_words_toward_no_relief": toward_no_relief,
    }


if __name__ == "__main__":
    sample = (
        "On March 3rd 2024 I was charged an unauthorized late fee of $450 even though "
        "my payment was submitted on time. I have my bank statement and payment "
        "confirmation number as proof. I have called four times and been given four "
        "different answers with no refund issued."
    )
    result = explain(sample)
    print("Toward Relief:")
    for c in result["top_words_toward_relief"]:
        print(" ", c)
    print("\nToward No Relief:")
    for c in result["top_words_toward_no_relief"]:
        print(" ", c)





# 🧱 What is the purpose of this step?
# In Step 7, your machine learning model was able to answer:"Will this customer get relief or not, and with what confidence?"
# However, standard ML models are often treated like black boxes—they provide an answer, but don't explicitly justify why.
# This step introduces SHAP (SHapley Additive exPlanations) inside app/services/explain_service.py. Its primary job is transparency and explainability:
# It inspects the exact words in a submitted complaint.
# It measures mathematically how much each individual word pushed the prediction toward Relief (positive impact) or toward No Relief (negative impact).
# This provides structured, word-level evidence that will later be handed to your LLM (Groq / LLaMA 3) to generate clear, human-readable sentences explaining the bank's likely decision.

# 🔍 How It Works Under the Hood (In Simple Math)
# Your model uses Logistic Regression with TF-IDF:
# (\text{Log-odds\ (Score)}=\text{Intercept}+\sum (\text{Word\ TF-IDF\ Value}\times \text{Learned\ Weight})\)
# Additive Breakdown: Because this is a linear model, the final probability score is simply the sum of each word's influence.
# Word Contribution:
# If a word like "unauthorized" appears and has a strong positive learned coefficient (e.g., +2.1), multiplying its TF-IDF frequency (e.g., 0.15) results in +0.315. This value pushes the prediction toward Relief.

# If a word like "statement" or "inquiry" leans toward routine administrative responses, it contributes a negative value, pulling the prediction toward No Relief.
# 
# Any word from your 80,000+ vocabulary that does not appear in this specific complaint has a TF-IDF score of 0, so its contribution is exactly 0.
# 
# ⚡ Why shap.LinearExplainer?
# Generic SHAP explainers (such as KernelExplainer) approximate values by running hundreds of slow simulations.
# For linear models, shap.LinearExplainer calculates the exact, closed-form mathematical contribution directly and instantly.
# Even with tens of thousands of features, it runs in milliseconds because it only evaluates the non-zero words physically present in the input text.