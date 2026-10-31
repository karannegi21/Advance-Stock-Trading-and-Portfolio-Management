import { useQuery } from '@tanstack/react-query';
import { api } from '../lib/api';
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from 'recharts';

export default function Analytics() {
  const { data: metrics } = useQuery({ queryKey: ['analytics'], queryFn: async () => (await api.get('/analytics')).data });
  const { data: curve } = useQuery({ queryKey: ['equity-curve'], queryFn: async () => (await api.get('/analytics/equity-curve')).data });

  const points = (curve?.points || []).map((p: any) => ({ date: p.date, value: Number(p.total_value) }));

  return (
    <div>
      <h1 className="text-2xl font-bold text-emerald-400 mb-4">Analytics</h1>
      {metrics && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
          <div className="bg-slate-900 border border-slate-800 rounded p-4"><p className="text-xs text-slate-400">Total Return</p><p className="text-lg font-semibold">{Number(metrics.total_return_pct).toFixed(2)}%</p></div>
          <div className="bg-slate-900 border border-slate-800 rounded p-4"><p className="text-xs text-slate-400">Annualized</p><p className="text-lg font-semibold">{Number(metrics.annualized_return_pct).toFixed(2)}%</p></div>
          <div className="bg-slate-900 border border-slate-800 rounded p-4"><p className="text-xs text-slate-400">Sharpe</p><p className="text-lg font-semibold">{Number(metrics.sharpe_ratio).toFixed(2)}</p></div>
          <div className="bg-slate-900 border border-slate-800 rounded p-4"><p className="text-xs text-slate-400">Max Drawdown</p><p className="text-lg font-semibold">{Number(metrics.max_drawdown_pct).toFixed(2)}%</p></div>
        </div>
      )}
      <div className="bg-slate-900 border border-slate-800 rounded p-4 mb-6">
        <h2 className="font-bold mb-3">Equity Curve</h2>
        {points.length > 0 ? (
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={points}>
              <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
              <XAxis dataKey="date" tick={{ fontSize: 10 }} />
              <YAxis tick={{ fontSize: 10 }} />
              <Tooltip />
              <Line type="monotone" dataKey="value" stroke="#10b981" dot={false} />
            </LineChart>
          </ResponsiveContainer>
        ) : <p className="text-slate-500 text-sm">No snapshots yet. Create one from Portfolio.</p>}
      </div>
      {metrics?.sector_allocation?.length > 0 && (
        <div className="bg-slate-900 border border-slate-800 rounded p-4">
          <h2 className="font-bold mb-3">Sector Allocation</h2>
          <ul className="space-y-1 text-sm">
            {metrics.sector_allocation.map((s: any) => (
              <li key={s.sector} className="flex justify-between"><span>{s.sector}</span><span>{Number(s.percentage).toFixed(2)}%</span></li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
