# ⚡ Grid Ghost

**AI-assisted smart-meter intelligence for non-technical loss detection.**

Grid Ghost is a prototype for Problem Statement 3. It converts large smart-meter consumption histories into two investigation signals:

- **WHO?** → risk score
- **WHEN?** → estimated anomaly/theft-start date

## Architecture

```text
Smart-meter history
      ↓
Preprocessing
      ↓
Feature engineering
      ↓
ML risk scoring
   ↙       ↘
WHO?      WHEN?
Risk      Anomaly date
   ↘       ↙
Inspection priority
      ↓
Grid Ghost dashboard
```

## Files

- `train.csv` — original training data
- `improved_risk_scores.csv` — improved model output
- `improved_theft_dates.csv` — temporal output
- `meter_risk_scores.csv` — baseline output
- `model.py` — reproducible baseline model
- `app.py` — Streamlit UI
- `requirements.txt` — dependencies

## Run

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Run the baseline model

```bash
python model.py
```

The model reports ROC-AUC, precision, recall and F1 and writes `model_risk_scores.csv` and `model_theft_dates.csv`.

## Dashboard

The UI includes:

1. Command Center — overall risk analytics
2. Consumer Search — individual risk and estimated date
3. Inspection Queue — filter and download high-risk meters
4. Timeline — anomaly-start trend
5. About — project explanation

Risk categories used for the prototype:

- HIGH: >= 0.70
- MEDIUM: 0.40–0.69
- LOW: < 0.40

## Important

A model score is a screening signal, not proof of electricity theft. Field verification and appropriate due process are required before enforcement or revenue recovery.

Before making this GitHub repository public, confirm that the hackathon data may be publicly shared. If not, keep the repository private or remove the raw CSVs and use the organizer's approved submission method.
