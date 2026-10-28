import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Legend,
  Line,
  LineChart,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'

const TOKEN = {
  accent: 'var(--accent)',
  muted: 'var(--text-muted)',
  border: 'var(--border)',
  text: 'var(--text)',
  surface2: 'var(--surface-2)',
  danger: 'var(--danger)',
  warning: 'var(--warning, #a86a12)',
}

const PIE = [
  'var(--accent)',
  'var(--text-muted)',
  'var(--warning, #a86a12)',
  'var(--danger)',
  'var(--surface-3)',
]

export function VelocityChart({ data }) {
  return (
    <ResponsiveContainer width="100%" height={220}>
      <BarChart data={data}>
        <CartesianGrid stroke={TOKEN.border} strokeDasharray="3 3" />
        <XAxis dataKey="sprint_name" tick={{ fill: TOKEN.muted, fontSize: 11 }} />
        <YAxis tick={{ fill: TOKEN.muted, fontSize: 11 }} />
        <Tooltip />
        <Legend />
        <Bar dataKey="committed" name="Committed" fill={TOKEN.muted} />
        <Bar dataKey="completed" name="Completed" fill={TOKEN.accent} />
      </BarChart>
    </ResponsiveContainer>
  )
}

export function CreatedResolvedChart({ data }) {
  return (
    <ResponsiveContainer width="100%" height={220}>
      <LineChart data={data}>
        <CartesianGrid stroke={TOKEN.border} strokeDasharray="3 3" />
        <XAxis dataKey="week" tick={{ fill: TOKEN.muted, fontSize: 10 }} />
        <YAxis tick={{ fill: TOKEN.muted, fontSize: 11 }} />
        <Tooltip />
        <Legend />
        <Line type="monotone" dataKey="created" stroke={TOKEN.muted} strokeWidth={2} />
        <Line type="monotone" dataKey="resolved" stroke={TOKEN.accent} strokeWidth={2} />
      </LineChart>
    </ResponsiveContainer>
  )
}

export function CfdChart({ series, statuses }) {
  return (
    <ResponsiveContainer width="100%" height={220}>
      <AreaChart data={series}>
        <CartesianGrid stroke={TOKEN.border} strokeDasharray="3 3" />
        <XAxis dataKey="date" tick={{ fill: TOKEN.muted, fontSize: 10 }} />
        <YAxis tick={{ fill: TOKEN.muted, fontSize: 11 }} />
        <Tooltip />
        <Legend />
        {(statuses || []).map((s, idx) => (
          <Area
            key={s.key}
            type="monotone"
            dataKey={s.key}
            name={s.name}
            stackId="1"
            stroke={PIE[idx % PIE.length]}
            fill={PIE[idx % PIE.length]}
            fillOpacity={0.55}
          />
        ))}
      </AreaChart>
    </ResponsiveContainer>
  )
}

export function BreakdownChart({ data }) {
  return (
    <ResponsiveContainer width="100%" height={200}>
      <PieChart>
        <Pie
          data={data}
          dataKey="count"
          nameKey="label"
          cx="50%"
          cy="50%"
          outerRadius={80}
          label={({ label, count }) => `${label} (${count})`}
        >
          {data.map((_, idx) => (
            <Cell key={idx} fill={PIE[idx % PIE.length]} />
          ))}
        </Pie>
        <Tooltip />
      </PieChart>
    </ResponsiveContainer>
  )
}

export function BurndownChart({ data }) {
  return (
    <ResponsiveContainer width="100%" height={220}>
      <LineChart data={data}>
        <CartesianGrid stroke={TOKEN.border} strokeDasharray="3 3" />
        <XAxis dataKey="date" tick={{ fill: TOKEN.muted, fontSize: 10 }} />
        <YAxis tick={{ fill: TOKEN.muted, fontSize: 11 }} />
        <Tooltip />
        <Legend />
        <Line
          type="monotone"
          dataKey="remaining"
          name="Remaining"
          stroke={TOKEN.accent}
          strokeWidth={2}
        />
        <Line
          type="monotone"
          dataKey="ideal"
          name="Ideal"
          stroke={TOKEN.muted}
          strokeDasharray="4 4"
        />
      </LineChart>
    </ResponsiveContainer>
  )
}

const Charts = {
  VelocityChart,
  CreatedResolvedChart,
  CfdChart,
  BreakdownChart,
  BurndownChart,
}

export default Charts
