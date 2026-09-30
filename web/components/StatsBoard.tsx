"use client";
/** The home statistics: a graph of the chosen tile over time, with the tiles under it. Click a tile to
 *  change the graph. Count series show per day or as a running total; "level" series (a streak, the number of
 *  players) are what they are on each day. Every graph is a line. The numbers come from /me/stats/series or /catalog/stats/series. */
import { useEffect, useMemo, useState, type ReactNode } from "react";
import { useT } from "./I18n";

export type Tile = {
  key: string;             // which series of the reply (me.* or guild.*)
  id?: string;             // when two tiles share a series (this week / all time), tells them apart
  n: number | string;      // the big number on the tile (already computed by the server)
  label: string;           // under the number, already translated
  icon?: ReactNode;
  mode?: "daily" | "total"; // the graph the tile opens with (count series only)
};
type Series = { base: number; values: number[]; level?: boolean };
type Reply = { days: string[]; me?: Record<string, Series>; guild: Record<string, Series> };

const RANGES = [30, 90, 365] as const;

export default function StatsBoard({ tiles, scope, endpoint }: { tiles: Tile[]; scope: "me" | "guild"; endpoint: string }) {
  const t = useT();
  const tid = (x: Tile) => x.id ?? x.key;
  const [pick, setPick] = useState(tiles[0] ? tid(tiles[0]) : "");
  const [days, setDays] = useState<(typeof RANGES)[number]>(30);
  const [mode, setMode] = useState<"daily" | "total">(tiles[0]?.mode ?? "daily");
  const [data, setData] = useState<Reply | null>(null);
  const [hover, setHover] = useState<number | null>(null);

  useEffect(() => {
    let live = true;
    fetch(`/api${endpoint}?days=${days}`).then((r) => (r.ok ? r.json() : null)).then((j) => { if (live) setData(j); }).catch(() => { if (live) setData(null); });
    return () => { live = false; };
  }, [endpoint, days]);

  const tile = tiles.find((x) => tid(x) === pick) ?? tiles[0];
  const series = data?.[scope]?.[tile?.key ?? ""] ?? null;
  const level = !!series?.level;
  const points = useMemo(() => {
    if (!series) return [];
    if (level || mode === "daily") return series.values;
    let run = series.base;
    return series.values.map((v) => (run += v));
  }, [series, level, mode]);

  function choose(x: Tile) { setPick(tid(x)); setMode(x.mode ?? "daily"); setHover(null); }

  return (
    <div className="stats-board">
      {tile && (
        <div className="card stats-chart">
          <div className="stats-chart-head">
            <b className="stats-chart-title">{tile.label}</b>
            <span className="spacer" />
            {!level && (
              <span className="seg" role="group" aria-label={t("Show")}>
                <button type="button" className={`bare ${mode === "daily" ? "on" : ""}`} aria-pressed={mode === "daily"} onClick={() => setMode("daily")}>{t("Per day")}</button>
                <button type="button" className={`bare ${mode === "total" ? "on" : ""}`} aria-pressed={mode === "total"} onClick={() => setMode("total")}>{t("Running total")}</button>
              </span>
            )}
            <span className="seg" role="group" aria-label={t("Range")}>
              {RANGES.map((d) => <button key={d} type="button" className={`bare ${days === d ? "on" : ""}`} aria-pressed={days === d} onClick={() => { setDays(d); setHover(null); }}>{d === 365 ? t("1 year") : t("{n} days", { n: d })}</button>)}
            </span>
          </div>
          {data && series ? <Chart days={data.days} values={points} hover={hover} setHover={setHover} /> : <div className="muted small stats-chart-empty">{t("Loading…")}</div>}
        </div>
      )}
      <div className="stats-grid">
        {tiles.map((x) => (
          <button key={tid(x)} type="button" className={`card stat ${pick === tid(x) ? "on" : ""}`} aria-pressed={pick === tid(x)} onClick={() => choose(x)}>
            {x.icon}<b>{x.n}</b><span className="muted small">{x.label}</span>
          </button>
        ))}
      </div>
    </div>
  );
}

/** One graph: a line with the area under it, a baseline, a few date marks, the top value, and a reading on hover. */
function Chart({ days, values, hover, setHover }: { days: string[]; values: number[]; hover: number | null; setHover: (i: number | null) => void }) {
  const W = 720, H = 190, L = 8, R = 8, T = 18, B = 26;
  const n = values.length;
  const max = Math.max(1, ...values);
  const iw = W - L - R, ih = H - T - B;
  const x = (i: number) => L + (n <= 1 ? iw / 2 : (i / (n - 1)) * iw);
  const y = (v: number) => T + ih - (v / max) * ih;
  const line = values.map((v, i) => `${i ? "L" : "M"}${x(i).toFixed(1)},${y(v).toFixed(1)}`).join(" ");
  const area = `${line} L${x(n - 1).toFixed(1)},${(T + ih).toFixed(1)} L${x(0).toFixed(1)},${(T + ih).toFixed(1)} Z`;
  // date marks: about six, evenly spread, always the first and the last
  const marks = useMemo(() => {
    const step = Math.max(1, Math.round((n - 1) / 5));
    const out: number[] = [];
    for (let i = 0; i < n; i += step) out.push(i);
    if (out[out.length - 1] !== n - 1) out.push(n - 1);
    return out;
  }, [n]);
  const label = (d: string) => { const [, m, dd] = d.split("-"); return `${Number(m)}/${Number(dd)}`; };
  function onMove(e: React.MouseEvent<SVGSVGElement>) {
    const box = e.currentTarget.getBoundingClientRect();
    const px = ((e.clientX - box.left) / box.width) * W;
    const i = Math.round(((px - L) / iw) * (n - 1));
    setHover(i >= 0 && i < n ? i : null);
  }
  const hv = hover !== null && hover < n ? hover : null;
  const tipX = hv === null ? 0 : x(hv);
  const tipW = 120, tipLeft = Math.min(W - R - tipW, Math.max(L, tipX - tipW / 2));
  return (
    <svg className="chart" viewBox={`0 0 ${W} ${H}`} width="100%" role="img" aria-label={`${values[n - 1] ?? 0}`} onMouseMove={onMove} onMouseLeave={() => setHover(null)}>
      {/* the grid: the baseline and three faint lines */}
      {[0.25, 0.5, 0.75, 1].map((f) => <line key={f} x1={L} x2={W - R} y1={y(max * f)} y2={y(max * f)} className="chart-grid" />)}
      <line x1={L} x2={W - R} y1={T + ih} y2={T + ih} className="chart-base" />
      <text x={L + 2} y={T - 6} className="chart-max">{max}</text>
      <path d={area} className="chart-area" />
      <path d={line} className="chart-line" />
      {hv !== null && <circle cx={x(hv)} cy={y(values[hv])} r={4} className="chart-dot" />}
      {marks.map((i) => <text key={i} x={x(i)} y={H - 8} className="chart-date" textAnchor={i === 0 ? "start" : i === n - 1 ? "end" : "middle"}>{label(days[i])}</text>)}
      {hv !== null && (
        <g className="chart-tip">
          <line x1={tipX} x2={tipX} y1={T} y2={T + ih} className="chart-cursor" />
          <rect x={tipLeft} y={T - 16} width={tipW} height={20} rx={2} />
          <text x={tipLeft + tipW / 2} y={T - 2} textAnchor="middle">{label(days[hv])} · {values[hv]}</text>
        </g>
      )}
    </svg>
  );
}
