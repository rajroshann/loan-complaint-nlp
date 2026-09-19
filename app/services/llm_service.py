from groq import Groq

from app.core.config import settings

_client = Groq(api_key=settings.LLM_API_KEY)


def explain_in_plain_english(
    predicted_label: str,
    probability_of_relief: float,
    toward_relief: list[dict],
    toward_no_relief: list[dict],
) -> dict:
    relief_words = ", ".join(c["word"] for c in toward_relief) or "none"
    no_relief_words = ", ".join(c["word"] for c in toward_no_relief) or "none"

    if predicted_label == "Relief":
        tone_instructions = (
            "This person's complaint scored ABOVE the threshold — historically, complaints "
            "like this tended to get a real resolution. Open with a warm, genuine compliment "
            "on how they wrote it — be specific, not generic. Then, still positively, suggest "
            "one or two small additions that could make an already-strong complaint even "
            "stronger. Tone: proud mentor congratulating good work, not a formal report."
        )
    else:
        tone_instructions = (
            "This person's complaint scored BELOW the threshold — historically, complaints "
            "like this tended to just get a written explanation, not a refund or correction. "
            "This is disappointing news, so open with genuine empathy — acknowledge that's "
            "frustrating. NEVER say the complaint was 'ignored' or imply they did something "
            "wrong. Gently explain what kind of detail similar-but-successful complaints "
            "usually include, framed as 'complaints that got resolved usually included...' — "
            "never as 'you failed to include...'. Tone: patient, calm, encouraging — like "
            "someone helping a friend fix a mistake, not pointing out a failure."
        )

    prompt = (
        f"A machine learning model estimated a {probability_of_relief:.0%} probability of "
        f"relief for a consumer's loan/mortgage complaint (predicted: '{predicted_label}').\n\n"
        f"The model's own explanation method found these words pushed the prediction TOWARD "
        f"relief: {relief_words}\n"
        f"These words pushed it TOWARD no relief: {no_relief_words}\n\n"
        f"{tone_instructions}\n\n"
        f"IMPORTANT FORMATTING RULE: Write in plain text only. Do NOT use markdown — no "
        f"asterisks, no bold, no italics, no bullet symbols. The markers below must appear "
        f"exactly as plain text with nothing around them.\n\n"
        f"Write two sections using these EXACT markers:\n\n"
        f"EXPLANATION:\n"
        f"3-5 warm, simple, plain-English sentences. Weave the words above naturally into "
        f"real sentences — NEVER just list them like 'word1, word2, word3'. A person with no "
        f"technical background should read this and feel understood, not analyzed. Do not "
        f"invent reasons beyond the words given. End with one gentle sentence noting this "
        f"reflects historical patterns, not a guarantee.\n\n"
        f"TIP:\n"
        f"2-3 concrete, specific, actionable next steps — things they could add or do next "
        f"(e.g. specific dates, dollar amounts, documentation, proof of prior contact, who to "
        f"follow up with). Written warmly, like encouragement from someone on their side, "
        f"not a checklist. Write as plain sentences, not a bulleted list."
    )

    try:
        response = _client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.4,
            max_tokens=600,
            reasoning_effort="low",
        )
        raw = response.choices[0].message.content.strip()
        if not raw:
            print(f"[llm_service] Empty content — finish_reason: {response.choices[0].finish_reason}")
        return _parse_response(raw, relief_words, no_relief_words)
    except Exception as e:
        print(f"[llm_service] Groq API call failed: {e}")
        return {
            "explanation": (
                f"Words associated with relief: {relief_words}. "
                f"Words associated with no relief: {no_relief_words}. "
                f"(AI explanation temporarily unavailable.)"
            ),
            "tip": (
                "Tip: including specific dates, dollar amounts, and any proof "
                "of prior contact with the company tends to strengthen a complaint."
            ),
        }


def _parse_response(raw: str, relief_words: str, no_relief_words: str) -> dict:
    raw = raw.replace("**", "").replace("*", "")  # strip stray markdown, belt-and-suspenders

    explanation, tip = "", ""
    if "TIP:" in raw:
        before, after = raw.split("TIP:", 1)
        explanation = before.replace("EXPLANATION:", "").strip()
        tip = after.strip()
    else:
        explanation = raw.replace("EXPLANATION:", "").strip()
        tip = (
            "Tip: including specific dates, dollar amounts, and any proof "
            "of prior contact with the company tends to strengthen a complaint."
        )
    return {"explanation": explanation, "tip": tip}


if __name__ == "__main__":
    from app.services.explain_service import explain

    print("=" * 60)
    print("TEST 1: A complaint likely to score ABOVE threshold (Relief)")
    print("=" * 60)
    relief_sample = (
        "On March 3rd 2024 I was charged an unauthorized late fee of $450 even though "
        "my payment was submitted on time. I have my bank statement and payment "
        "confirmation number as proof. I have called four times and been given four "
        "different answers with no refund issued."
    )
    shap_result = explain(relief_sample)
    result = explain_in_plain_english(
        predicted_label="Relief",
        probability_of_relief=0.60,
        toward_relief=shap_result["top_words_toward_relief"],
        toward_no_relief=shap_result["top_words_toward_no_relief"],
    )
    print("\nEXPLANATION:\n", result["explanation"])
    print("\nTIP:\n", result["tip"])

    print("\n\n" + "=" * 60)
    print("TEST 2: A complaint likely to score BELOW threshold (No Relief)")
    print("=" * 60)
    no_relief_sample = (
        "I disagree with the interest rate calculation on my statement. I would like "
        "someone to explain how it was calculated."
    )
    shap_result_2 = explain(no_relief_sample)
    result_2 = explain_in_plain_english(
        predicted_label="No Relief",
        probability_of_relief=0.15,
        toward_relief=shap_result_2["top_words_toward_relief"],
        toward_no_relief=shap_result_2["top_words_toward_no_relief"],
    )
    print("\nEXPLANATION:\n", result_2["explanation"])
    print("\nTIP:\n", result_2["tip"])