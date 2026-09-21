# ⚖️ ReliefIQ

**AI-powered insight into your loan complaint's likely outcome.**

ReliefIQ analyzes a consumer's loan or mortgage complaint against real, historical
outcomes from the CFPB (Consumer Financial Protection Bureau) complaint database,
estimates the probability it will result in relief (a refund or account correction)
versus a written explanation only, and explains *why* — in plain, empathetic
language — along with concrete tips to strengthen the complaint.

**🔗 Live demo:** [https://reliefiq-1txz.onrender.com](https://reliefiq-1txz.onrender.com)
*(hosted on Render's free tier — the app spins down after inactivity and can take
30-60 seconds to wake up on first load; 

---

## What it does

1. **Describe your complaint** — paste it in plain English, no forms or legal jargon
2. **AI analyzes it** — a model trained on real CFPB complaint outcomes estimates a
   relief probability
3. **Get a clear explanation** — SHAP identifies which words in *your specific*
   complaint pushed the prediction each way, and an LLM turns that into a warm,
   understandable explanation plus concrete next steps — tone adapts to the
   outcome (empathetic and constructive if the odds are low, encouraging if
   they're high)

Every prediction is saved to the logged-in user's private history, filterable by
outcome.

---

## Tech stack

| Layer | Technology |
|---|---|
| **ML / NLP** | scikit-learn (TF-IDF + Logistic Regression), NLTK (cleaning, tokenization, lemmatization) |
| **Explainability** | SHAP (`LinearExplainer`) + Groq LLM (`openai/gpt-oss-120b`) for natural-language explanations |
| **Backend** | FastAPI, SQLAlchemy, JWT authentication (bcrypt password hashing) |
| **Database** | SQLite (swappable to PostgreSQL via one env var) |
| **Frontend** | Jinja2 + Tailwind CSS (CDN) — server-rendered, no JS framework |
| **Testing** | pytest (12 tests: auth, prediction, history isolation, preprocessing) |
| **CI/CD** | GitHub Actions — tests run automatically on every push |
| **Containerization** | Docker + Docker Compose |
| **Deployment** | Render (Docker-based web service) |

---

## Architecture

```
Browser (Jinja2 + Tailwind, dark mode, no JS framework)
        │
        ▼
FastAPI app
 ├── /auth        signup, login (JWT issuance)
 ├── /predict     model inference → SHAP → Groq LLM explanation → save to DB
 ├── /history     per-user prediction history (with outcome filtering)
 └── /*-page      server-rendered HTML pages
        │
        ▼
SQLAlchemy ORM ──► SQLite (users, predictions)
        │
        ▼
ML artifacts (joblib): TF-IDF vectorizer + Logistic Regression model
        │
        ▼
Groq API (LLM explanation layer, free tier)
```

---

## The ML pipeline — what was actually tried

The dataset is the CFPB Consumer Complaint Database, filtered to loan/mortgage
products with a consumer-narrative, target = whether the complaint was closed with
monetary/non-monetary **relief** (1) or closed with an **explanation only** (0) — a
naturally imbalanced problem (~92.5% / 7.5%).

### Experiment 1 → Experiment 2: more data was the real fix

| | 9,000-row sample | 45,000-row sample |
|---|---|---|
| Model | Weighted Logistic Regression | Weighted Logistic Regression |
| Test F1 | 0.2581 | **0.2909** |
| Test Recall | 47.4% | 53.9% |

Scaling up training data (with the same ratio preserved) was a bigger lever than
any algorithm choice — the four candidate models (Logistic Regression, Linear SVM,
Multinomial Naive Bayes, XGBoost) all landed within a fairly narrow F1 band once
properly threshold-tuned.

### A real lesson in model selection: validation ≠ test

On the 45k-row experiment, **XGBoost won on validation** (F1 = 0.3015) but
**Logistic Regression won on the held-out test set** (0.2909 vs XGBoost's 0.2583) —
XGBoost had overfit to quirks specific to the validation split. The final model
shipped is Logistic Regression precisely because the test set (touched exactly
once, after selection) is the number that actually matters.

### An ablation that simplified the product

Before finalizing the feature set, a metadata ablation (adding `Product`/`Issue`
category features alongside the text) was tested — it produced **no measurable
gain** (0.2906 vs 0.2909 test F1). This kept the deployed app simpler: a single
free-text box, no dropdowns, no metadata-encoding pipeline to maintain.

**Final model:** Logistic Regression, TF-IDF (1-2 grams, 60,000 features,
`class_weight="balanced"`), threshold = 0.45, confirmed near-optimal via
`GridSearchCV`.

---

## Known limitations (stated honestly)

- **Digit-stripping preprocessing**: the text-cleaning regex strips all digits,
  which deletes dollar amounts and dates before the model ever sees them — real
  evidence signal is lost. Confirmed via manual testing: a complaint with
  documented harm scored *lower* than a non-complaint "thank you" message.
- **A bigram-formation ordering bug**, found via SHAP output: stopwords are
  removed before bigrams are generated, so words separated by a removed stopword
  (or even a sentence boundary) can become an adjacent, nonsensical-but-weighted
  bigram (e.g. "time bank" from unrelated sentence fragments).
- **Absolute F1 (~0.29) is modest** — the two outcome classes use largely similar
  vocabulary in this dataset, per the original EDA, making this a genuinely hard
  classification problem, not one solved by algorithm choice alone.
- **No persistent data across deploys** — the database is a container-local
  SQLite file by design (kept out of version control); every redeploy starts
  fresh. A production version would use a hosted Postgres instance or a
  persistent volume.
- **Render free-tier cold starts** — as noted above.

---

## Future work

- Real hyperparameter search (`GridSearchCV`/`RandomizedSearchCV`) across all
  model types, not just a manual sweep
- Fix the digit-stripping and bigram-ordering preprocessing bugs
- Character n-grams or embeddings/transformer-based text representations
- A larger training sample than 45,000 rows
- Redis caching for repeated LLM explanation calls
- React frontend, real-time CFPB data ingestion, and a full conversational
  chatbot — deliberately deferred as sequencing choices (this project's build
  order: FastAPI → DB → auth → SHAP/LLM → tests → CI → Docker) rather than
  stacking every first-time technology into one project at once

---

## Running locally

```bash
git clone https://github.com/rajroshann/loan-complaint-nlp.git
cd loan-complaint-nlp

python -m venv venv
venv\Scripts\Activate.ps1        # Windows
# source venv/bin/activate       # macOS/Linux

pip install -r requirements.txt

python -c "import nltk; nltk.download('stopwords'); nltk.download('wordnet'); nltk.download('omw-1.4'); nltk.download('punkt_tab')"

cp .env.example .env
# then edit .env: set JWT_SECRET_KEY (python -c "import secrets; print(secrets.token_hex(32))")
# and LLM_API_KEY (free Groq key from console.groq.com)

uvicorn app.main:app --reload
```
Visit `http://127.0.0.1:8000`.

## Running with Docker

```bash
docker compose up --build
```
Visit `http://localhost:8000`.

## Running tests

```bash
pytest -v
```

---

## Project structure

```
app/
├── core/          # config, security (JWT, hashing)
├── db/            # SQLAlchemy models + session
├── routers/        # auth, predict, history, pages
├── schemas/        # Pydantic request/response models
├── services/       # model inference, SHAP, LLM explanation
└── templates/       # Jinja2 pages (login, signup, home, predict, history)
ml_artifacts/        # trained TF-IDF vectorizer + Logistic Regression model
tests/               # pytest suite
.github/workflows/    # CI (GitHub Actions)
Dockerfile, docker-compose.yml, .dockerignore
```

---

## Academic context

Originally developed as a lab project for the **Deep Learning and Optimization
Laboratory (CS5310)** course, M.Tech in Data Science & Engineering, NIT Silchar,
then extended into a full deployed application as a portfolio piece.

---

## Author

**Raj Roshan Singh**
[GitHub](https://github.com/rajroshann) · [LinkedIn](https://linkedin.com/in/raj-roshan-singh)
