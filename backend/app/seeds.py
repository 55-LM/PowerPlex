from sqlalchemy.orm import Session
from sqlalchemy import select, delete
from .models import Frame, HeatPoint
from .pipeline import load_owid_generation_by_source, forecast_mix, compute_adequacy
from .geo import bd_bbox_polygon, grid_points_within, make_heat_values

def rebuild(db: Session, horizon=15, step_deg=0.12, demand_growth=0.045, reserve_margin=0.15):
    db.execute(delete(Frame))
    db.execute(delete(HeatPoint))
    db.commit()

    hist = load_owid_generation_by_source("BGD")
    mix = forecast_mix(hist, horizon=horizon)
    adequacy = compute_adequacy(mix, demand_growth=demand_growth, reserve_margin=reserve_margin)

    for _, r in adequacy.iterrows():
        y = int(r["year"])
        metrics = {
            "adequacy_index": float(r["adequacy_index"]),
            "available_supply": float(r["available_supply"]),
            "peak_demand": float(r["peak_demand"]),
            "total_generation": float(r["total_generation"]),
        }
        for k, v in metrics.items():
            db.add(Frame(year=y, metric=k, value=v))
    db.commit()

    poly = bd_bbox_polygon()
    pts = grid_points_within(poly, step_deg=step_deg)
    year_to_ai = {int(r["year"]): float(r["adequacy_index"]) for _, r in adequacy.iterrows()}

    for y, ai in year_to_ai.items():
        vals = make_heat_values(pts, ai, seed=7)
        for (lon, lat), v in zip(pts, vals):
            db.add(HeatPoint(year=y, lon=lon, lat=lat, value=float(v)))
    db.commit()
