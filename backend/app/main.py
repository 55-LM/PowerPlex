from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import select
from .db import get_db, engine
from .models import Base, Frame, HeatPoint
from .seeds import rebuild

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

Base.metadata.create_all(bind=engine)

@app.get("/health")
def health():
    return {"ok": True}

@app.post("/admin/rebuild")
def admin_rebuild(
    horizon: int = 15,
    step_deg: float = 0.12,
    demand_growth: float = 0.045,
    reserve_margin: float = 0.15,
    db: Session = Depends(get_db),
):
    rebuild(db, horizon=horizon, step_deg=step_deg, demand_growth=demand_growth, reserve_margin=reserve_margin)
    return {"ok": True}

@app.get("/frames")
def frames(db: Session = Depends(get_db)):
    rows = db.execute(select(Frame)).scalars().all()
    by_year = {}
    for r in rows:
        by_year.setdefault(r.year, {})[r.metric] = r.value
    years = sorted(by_year.keys())
    return {"years": years, "frames": [{"year": y, "metrics": by_year[y]} for y in years]}

@app.get("/heat/{year}")
def heat(year: int, db: Session = Depends(get_db)):
    pts = db.execute(select(HeatPoint).where(HeatPoint.year == year)).scalars().all()
    features = []
    for p in pts:
        features.append({
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [p.lon, p.lat]},
            "properties": {"v": p.value}
        })
    return {"type": "FeatureCollection", "features": features}
