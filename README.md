# Firebreak: stop a rumor by protecting the right accounts

An interactive simulator and optimizer for misinformation spread. It generates a
social network, simulates a rumor spreading (independent cascade model), and finds
the few accounts whose protection (fact-check, inoculation) stops the rumor most.
It compares five plans side by side: do nothing, random accounts, most-followed
accounts, bridge accounts (betweenness), and a lazy-greedy (CELF) optimizer.

Rigor: plans are chosen on one set of simulated worlds and scored on a separate,
held-out set, and every plan is scored on identical worlds, so comparisons are fair.
Simulated networks only: it demonstrates a method, not a prediction for a real platform.

## Run on your PC
```bash
cd firebreak
python -m venv .venv
# Windows: .venv\Scripts\activate      macOS/Linux: source .venv/bin/activate
pip install -r requirements-dev.txt
pytest -q
uvicorn app.main:app --reload
```
Open http://127.0.0.1:8000

## Push to GitHub
Create an empty repo named `firebreak` on github.com, then:
```bash
git init
git add .
git commit -m "Initial commit: Firebreak"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/firebreak.git
git push -u origin main
```

## Deploy to Vercel (free)
Dashboard: vercel.com > Add New > Project > import the repo > Deploy (no settings).
CLI: `npm i -g vercel && vercel login && vercel --prod`

## Layout
```
api/index.py       Vercel entry point
app/graphs.py      network generators (scale-free, small-world, echo chambers)
app/cascade.py     live-edge worlds, spread, betweenness, CELF optimizer
app/experiment.py  train/test experiment and summary
app/main.py        FastAPI: POST /api/simulate
public/index.html  interactive visualization
tests/             pytest suite
```

## Ideas to extend
Real graph data (e.g. SNAP datasets), time-varying spread, a recommended-links
"prebunking" mode, cost per account, comparing against reinforcement learning,
and a written evaluation across many seeds with confidence intervals.
