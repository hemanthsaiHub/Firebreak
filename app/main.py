import os
from pathlib import Path
from typing import Literal

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from .experiment import run

app = FastAPI(title="Firebreak API", version="1.0.0")


class SimIn(BaseModel):
    network: Literal["scale_free", "small_world", "communities"] = "scale_free"
    n: int = Field(150, ge=40, le=300)
    seeds: int = Field(2, ge=1, le=5)
    seed_mode: Literal["random", "influencer"] = "random"
    p: float = Field(0.25, ge=0.05, le=0.6)
    budget: int = Field(8, ge=1, le=20)
    sims: int = Field(80, ge=20, le=200)
    seed: int = Field(7, ge=0, le=1_000_000)


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.post("/api/simulate")
def simulate(b: SimIn):
    return run(b.network, b.n, b.seeds, b.seed_mode, b.p, b.budget, b.sims, b.seed)


if not os.getenv("VERCEL"):  # local dev; on Vercel public/ is served by the CDN
    app.mount("/", StaticFiles(directory=Path(__file__).resolve().parent.parent / "public", html=True), name="site")
