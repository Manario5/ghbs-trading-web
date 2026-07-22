import React from 'react';

/**
 * Dependency-free, theme-consistent SVG chart primitives for the command
 * center. Read-only presentation only — no data fetching, no fake values.
 */

const AXIS = '#374151';       // gray-700
const GRID = '#1f2937';       // gray-800
const TEXT = '#9ca3af';       // gray-400

export function ChartCard({
  title, subtitle, right, children,
}: { title: string; subtitle?: string; right?: React.ReactNode; children: React.ReactNode }) {
  return (
    <div className="bg-gray-900/70 border border-gray-800 rounded-xl p-5 flex flex-col">
      <div className="flex items-start justify-between mb-3">
        <div>
          <h3 className="text-sm font-semibold text-gray-200">{title}</h3>
          {subtitle && <p className="text-xs text-gray-500 mt-0.5">{subtitle}</p>}
        </div>
        {right}
      </div>
      <div className="flex-1 min-h-[160px]">{children}</div>
    </div>
  );
}

export function EmptyState({ message }: { message: string }) {
  return (
    <div className="h-full min-h-[160px] flex flex-col items-center justify-center text-center border border-dashed border-gray-800 rounded-lg">
      <div className="text-gray-600 text-2xl mb-1">◔</div>
      <p className="text-xs text-gray-500 max-w-[220px]">{message || 'No data yet.'}</p>
    </div>
  );
}

const PALETTE = ['#3b82f6', '#22c55e', '#f59e0b', '#a855f7', '#ef4444', '#14b8a6', '#eab308', '#64748b'];

export function LineChart({ points }: { points: { day: string; score: number }[] }) {
  if (!points.length) return <EmptyState message="No history yet." />;
  const W = 520, H = 180, P = 28;
  const xs = points.map((_, i) => i);
  const ys = points.map(p => p.score);
  const minY = Math.min(-1, ...ys), maxY = Math.max(1, ...ys);
  const xScale = (i: number) => P + (xs.length === 1 ? (W - 2 * P) / 2 : (i / (xs.length - 1)) * (W - 2 * P));
  const yScale = (v: number) => H - P - ((v - minY) / (maxY - minY || 1)) * (H - 2 * P);
  const path = points.map((p, i) => `${i === 0 ? 'M' : 'L'}${xScale(i).toFixed(1)},${yScale(p.score).toFixed(1)}`).join(' ');
  const zeroY = yScale(0);
  return (
    <svg viewBox={`0 0 ${W} ${H}`} className="w-full h-auto" role="img" aria-label="Market regime trend">
      <line x1={P} y1={zeroY} x2={W - P} y2={zeroY} stroke={GRID} strokeDasharray="4 4" />
      <line x1={P} y1={P} x2={P} y2={H - P} stroke={AXIS} />
      <path d={path} fill="none" stroke="#3b82f6" strokeWidth={2} />
      {points.map((p, i) => (
        <circle key={i} cx={xScale(i)} cy={yScale(p.score)} r={2.5} fill={p.score >= 0 ? '#22c55e' : '#ef4444'} />
      ))}
      <text x={P - 6} y={yScale(maxY) + 4} fontSize="9" fill={TEXT} textAnchor="end">{maxY}</text>
      <text x={P - 6} y={zeroY + 3} fontSize="9" fill={TEXT} textAnchor="end">0</text>
      <text x={P - 6} y={yScale(minY)} fontSize="9" fill={TEXT} textAnchor="end">{minY}</text>
    </svg>
  );
}

export function BarChart({ data, color = '#3b82f6' }: { data: { label: string; value: number }[]; color?: string }) {
  if (!data.length) return <EmptyState message="No data yet." />;
  const W = 520, H = 200, P = 30;
  const max = Math.max(1, ...data.map(d => d.value));
  const bw = (W - 2 * P) / data.length;
  return (
    <svg viewBox={`0 0 ${W} ${H}`} className="w-full h-auto" role="img">
      <line x1={P} y1={H - P} x2={W - P} y2={H - P} stroke={AXIS} />
      {data.map((d, i) => {
        const h = ((d.value) / max) * (H - 2 * P);
        const x = P + i * bw + bw * 0.15;
        const w = bw * 0.7;
        return (
          <g key={i}>
            <rect x={x} y={H - P - h} width={w} height={h} rx={3} fill={PALETTE[i % PALETTE.length] || color} />
            <text x={x + w / 2} y={H - P - h - 4} fontSize="9" fill={TEXT} textAnchor="middle">{d.value}</text>
            <text x={x + w / 2} y={H - P + 12} fontSize="8" fill={TEXT} textAnchor="middle">
              {d.label.length > 9 ? d.label.slice(0, 8) + '…' : d.label}
            </text>
          </g>
        );
      })}
    </svg>
  );
}

export function HBarChart({ data }: { data: { label: string; value: number; sub?: string }[] }) {
  if (!data.length) return <EmptyState message="No data yet." />;
  const max = Math.max(1, ...data.map(d => d.value));
  return (
    <div className="space-y-2">
      {data.map((d, i) => (
        <div key={i} className="flex items-center gap-2">
          <div className="w-16 text-xs text-gray-400 font-mono truncate text-right">{d.label}</div>
          <div className="flex-1 bg-gray-800 rounded h-4 overflow-hidden">
            <div className="h-full rounded" style={{ width: `${(d.value / max) * 100}%`, background: PALETTE[i % PALETTE.length] }} />
          </div>
          <div className="w-10 text-xs text-gray-300 text-right">{d.value}</div>
        </div>
      ))}
    </div>
  );
}

export function Funnel({ stages }: { stages: { stage: string; count: number }[] }) {
  if (!stages.length) return <EmptyState message="No scout runs yet." />;
  const max = Math.max(1, ...stages.map(s => s.count));
  return (
    <div className="space-y-1.5">
      {stages.map((s, i) => (
        <div key={i} className="flex items-center gap-3">
          <div className="w-28 text-xs text-gray-400">{s.stage}</div>
          <div className="flex-1 flex justify-center">
            <div className="h-6 rounded flex items-center justify-center text-[10px] font-semibold text-white"
                 style={{ width: `${Math.max(8, (s.count / max) * 100)}%`, background: PALETTE[i % PALETTE.length] }}>
              {s.count}
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}

export function Donut({ data }: { data: { label: string; value: number }[] }) {
  const total = data.reduce((a, b) => a + b.value, 0);
  if (!total) return <EmptyState message="No signals recorded yet." />;
  const R = 60, C = 2 * Math.PI * R;
  let offset = 0;
  return (
    <div className="flex items-center gap-6">
      <svg viewBox="0 0 160 160" className="w-40 h-40 -rotate-90">
        {data.map((d, i) => {
          const frac = d.value / total;
          const dash = frac * C;
          const seg = (
            <circle key={i} cx={80} cy={80} r={R} fill="none" stroke={PALETTE[i % PALETTE.length]}
                    strokeWidth={20} strokeDasharray={`${dash} ${C - dash}`} strokeDashoffset={-offset} />
          );
          offset += dash;
          return seg;
        })}
        <circle cx={80} cy={80} r={44} fill="#0b0f17" />
      </svg>
      <div className="space-y-1">
        {data.map((d, i) => (
          <div key={i} className="flex items-center gap-2 text-xs">
            <span className="w-2.5 h-2.5 rounded-sm" style={{ background: PALETTE[i % PALETTE.length] }} />
            <span className="text-gray-400">{d.label}</span>
            <span className="text-gray-300 font-semibold ml-auto">{d.value}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
