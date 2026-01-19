"use client"

import mapboxgl from "mapbox-gl"
import { useEffect, useMemo, useRef, useState } from "react"
import { getFrames, getHeat, rebuild } from "../lib/api"
import { valueToColor } from "../lib/colors"

mapboxgl.accessToken = process.env.NEXT_PUBLIC_MAPBOX_TOKEN || ""

type FramesResp = {
  years: number[]
  frames: { year: number; metrics: Record<string, number> }[]
}

export default function Page() {
  const mapRef = useRef<mapboxgl.Map | null>(null)
  const mapContainerRef = useRef<HTMLDivElement | null>(null)
  const [frames, setFrames] = useState<FramesResp | null>(null)
  const [idx, setIdx] = useState(0)
  const [playing, setPlaying] = useState(true)
  const [loading, setLoading] = useState(true)

  const year = useMemo(() => frames?.years?.[idx], [frames, idx])
  const metrics = useMemo(() => frames?.frames?.find(f => f.year === year)?.metrics, [frames, year])

  useEffect(() => {
    ;(async () => {
      setLoading(true)
      await rebuild()
      const f = await getFrames()
      setFrames(f)
      setIdx(Math.max(0, f.years.length - 1))
      setLoading(false)
    })()
  }, [])

  useEffect(() => {
    if (!mapContainerRef.current) return
    if (mapRef.current) return
    const m = new mapboxgl.Map({
      container: mapContainerRef.current,
      style: "mapbox://styles/mapbox/dark-v11",
      center: [90.35, 23.8],
      zoom: 5.4,
      pitch: 0,
      bearing: 0
    })
    mapRef.current = m
    m.on("load", async () => {
      m.addSource("heat", {
        type: "geojson",
        data: { type: "FeatureCollection", features: [] }
      })
      m.addLayer({
        id: "heat-layer",
        type: "heatmap",
        source: "heat",
        paint: {
          "heatmap-weight": ["interpolate", ["linear"], ["get", "v"], -0.5, 0, 0.5, 1],
          "heatmap-intensity": ["interpolate", ["linear"], ["zoom"], 4, 0.6, 7, 1.35],
          "heatmap-radius": ["interpolate", ["linear"], ["zoom"], 4, 18, 7, 34],
          "heatmap-opacity": 0.92,
          "heatmap-color": [
            "interpolate",
            ["linear"],
            ["heatmap-density"],
            0, "rgba(0,0,0,0)",
            0.2, "#39c6d6",
            0.45, "#63d86b",
            0.7, "#f0e64f",
            1.0, "#e04a3a"
          ]
        }
      })
    })
    return () => {
      m.remove()
      mapRef.current = null
    }
  }, [])

  useEffect(() => {
    let t: any = null
    if (playing && frames?.years?.length) {
      t = setInterval(() => {
        setIdx(i => (i + 1) % frames.years.length)
      }, 1200)
    }
    return () => {
      if (t) clearInterval(t)
    }
  }, [playing, frames])

  useEffect(() => {
    ;(async () => {
      if (!mapRef.current) return
      if (!year) return
      const geo = await getHeat(year)
      const src = mapRef.current.getSource("heat") as mapboxgl.GeoJSONSource | undefined
      if (src) src.setData(geo)
    })()
  }, [year])

  const adequacy = metrics?.adequacy_index ?? 0
  const adequacyPct = Math.round(adequacy * 100)
  const badgeColor = valueToColor(adequacy)

  return (
    <div style={{ width: "100vw", height: "100vh", position: "relative" }}>
      <div ref={mapContainerRef} style={{ position: "absolute", inset: 0 }} />

      <div className="panel" style={{ position: "absolute", left: 26, right: 26, top: 20, bottom: 22, padding: 18, display: "grid", gridTemplateRows: "auto 1fr auto", gap: 14 }}>
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", gap: 14 }}>
          <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
            <button onClick={() => setPlaying(p => !p)} style={{ borderRadius: 999, padding: "8px 12px", border: "1px solid rgba(255,255,255,0.14)", background: "rgba(0,0,0,0.25)", color: "rgba(255,255,255,0.9)", cursor: "pointer" }}>
              {playing ? "Pause" : "Play"}
            </button>
            <div style={{ width: 360, maxWidth: "50vw" }}>
              <input
                className="slider"
                type="range"
                min={0}
                max={(frames?.years?.length ?? 1) - 1}
                value={idx}
                onChange={(e) => { setIdx(parseInt(e.target.value, 10)); setPlaying(false) }}
                style={{ width: "100%" }}
              />
              <div className="small" style={{ display: "flex", justifyContent: "space-between", marginTop: 6 }}>
                <span>{frames?.years?.[0] ?? ""}</span>
                <span>{frames?.years?.[Math.max(0, (frames?.years?.length ?? 1) - 1)] ?? ""}</span>
              </div>
            </div>
          </div>

          <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
            <div className="small">Year</div>
            <div style={{ fontSize: 18, fontWeight: 650 }}>{year ?? ""}</div>
            <div style={{ width: 10 }} />
            <div className="small">Adequacy</div>
            <div style={{ padding: "6px 10px", borderRadius: 999, background: badgeColor, color: "#071018", fontWeight: 800 }}>
              {adequacyPct}%
            </div>
          </div>
        </div>

        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 22, alignItems: "center", justifyItems: "center" }}>
          <MiniMapCard title="Projection A" />
          <MiniMapCard title="Projection B" />
          <MiniMapCard title="Projection C" />
        </div>

        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-end", gap: 16 }}>
          <div style={{ minWidth: 260 }}>
            <div className="small" style={{ marginBottom: 8 }}>Grid Supply–Demand Adequacy</div>
            <div className="legendbar" />
            <div className="small" style={{ display: "flex", justifyContent: "space-between", marginTop: 6 }}>
              <span>Deficit</span>
              <span>Surplus</span>
            </div>
            <div className="small" style={{ display: "flex", justifyContent: "space-between", marginTop: 4 }}>
              <span>−50%</span>
              <span>−30%</span>
              <span>−10%</span>
              <span>0%</span>
              <span>+20%</span>
              <span>+50%</span>
            </div>
          </div>

          <div style={{ width: 420, maxWidth: "45vw" }}>
            <div className="kpi">
              <div className="kpiCard">
                <div className="small">Available Supply</div>
                <div style={{ fontSize: 18, fontWeight: 700 }}>{fmt(metrics?.available_supply)}</div>
              </div>
              <div className="kpiCard">
                <div className="small">Peak Demand</div>
                <div style={{ fontSize: 18, fontWeight: 700 }}>{fmt(metrics?.peak_demand)}</div>
              </div>
              <div className="kpiCard">
                <div className="small">Total Generation</div>
                <div style={{ fontSize: 18, fontWeight: 700 }}>{fmt(metrics?.total_generation)}</div>
              </div>
              <div className="kpiCard">
                <div className="small">Status</div>
                <div style={{ fontSize: 18, fontWeight: 700 }}>{loading ? "Loading" : adequacy < -0.1 ? "Stressed" : adequacy < 0.05 ? "Balanced" : "Surplus"}</div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {loading ? (
        <div style={{ position: "absolute", inset: 0, display: "grid", placeItems: "center", pointerEvents: "none" }}>
          <div className="panel" style={{ padding: 18, borderRadius: 16 }}>
            <div style={{ fontWeight: 700 }}>Building dataset…</div>
            <div className="small" style={{ marginTop: 6 }}>OWID → forecast → map frames</div>
          </div>
        </div>
      ) : null}
    </div>
  )
}

function MiniMapCard({ title }: { title: string }) {
  return (
    <div style={{ width: 250, height: 250, borderRadius: 18, border: "1px solid rgba(255,255,255,0.08)", background: "rgba(0,0,0,0.22)", position: "relative", overflow: "hidden" }}>
      <div style={{ position: "absolute", inset: 0, background: "radial-gradient(circle at 30% 20%, rgba(240,230,79,0.22), rgba(0,0,0,0) 55%), radial-gradient(circle at 60% 70%, rgba(99,216,107,0.16), rgba(0,0,0,0) 60%)" }} />
      <div style={{ position: "absolute", left: 12, top: 12, fontSize: 12, opacity: 0.85 }}>{title}</div>
      <div style={{ position: "absolute", left: 12, bottom: 12, right: 12, height: 2, background: "rgba(255,255,255,0.08)" }} />
    </div>
  )
}

function fmt(x: any) {
  const n = typeof x === "number" ? x : 0
  if (!isFinite(n)) return "-"
  if (n >= 1e12) return `${(n / 1e12).toFixed(2)}T`
  if (n >= 1e9) return `${(n / 1e9).toFixed(2)}B`
  if (n >= 1e6) return `${(n / 1e6).toFixed(2)}M`
  if (n >= 1e3) return `${(n / 1e3).toFixed(2)}K`
  return n.toFixed(2)
}
