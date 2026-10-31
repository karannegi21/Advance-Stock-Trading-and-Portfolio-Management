import { useQuery } from '@tanstack/react-query';
import { api } from '../lib/api';
import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer } from 'recharts';

const COLORS = ['#10b981', '#3b82f6', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899'];

export default function Portfolio() {
  const { data, isLoading } = useQuery({
    queryKey: ['portfolio'],
    queryFn: async () => (await api.get('/portfolio')).data,
  });

  if (isLoading) return <p>Loading...</p>;
  if (!data) return <p>No data</p>;

  const pieData = data.holdings.map((h: any) => ({ name: h.symbol, value: Number(h.market_value) }));

  return (
    <div>
      <h1 className="text-2xl font-bold text-emerald-400 mb-4">Portfolio</h1>
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
        <div className="bg-slate-900 border border-slate-800 rounded p-4">
          <p className="text-xs text-slate-400">Cash</p>
          <p className="text-lg font-semibold">{Number(data.cash_balance).toFixed(2)}</p>
        </div>
        <div className="bg-slate-900 border border-slate-800 rounded p-4">
          <p className="text-xs text-slate-400">Invested</p>
          <p className="text-lg font-semibold">{Number(data.invested_value).toFixed(2)}</p>
        </div>
        <div className="bg-slate-900 border border-slate-800 rounded p-4">
          <p className="text-xs text-slate-400">Total Value</p>
          <p className="text-lg font-semibold">{Number(data.total_value).toFixed(2)}</p>
        </div>
        <div className="bg-slate-900 border border-slate-800 rounded p-4">
          <p className="text-xs text-slate-400">P&L</p>
          <p className={`text-lg font-semibold ${Number(data.total_pnl) >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>
            {Number(data.total_pnl).toFixed(2)} ({Number(data.total_pnl_pct).toFixed(2)}%)
          </p>
        </div>
      </div>
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-slate-900 border border-slate-800 rounded p-4">
          <h2 className="font-bold mb-3">Holdings</h2>
          <table className="w-full text-sm">
            <thead className="text-slate-400">
              <tr><th className="text-left">Symbol</th><th>Qty</th><th>Avg</th><th>Price</th><th>P&L</th></tr>
            </thead>
            <tbody>
              {data.holdings.map((h: any) => (
                <tr key={h.symbol} className="border-t border-slate-800">
                  <td className="py-2 font-semibold">{h.symbol}</td>
                  <td className="text-center">{h.quantity}</td>
                  <td className="text-center">{Number(h.avg_cost).toFixed(2)}</td>
                  <td className="text-center">{Number(h.current_price).toFixed(2)}</td>
                  <td className={`text-center ${Number(h.unrealized_pnl) >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>{Number(h.unrealized_pnl).toFixed(2)}</td>
                </tr>
              ))}
            </tbody>
          </table>
          {data.holdings.length === 0 && <p className="text-slate-500 text-sm mt-2">No holdings yet.</p>}
        </div>
        <div className="bg-slate-900 border border-slate-800 rounded p-4">
          <h2 className="font-bold mb-3">Allocation</h2>
          {pieData.length > 0 ? (
            <ResponsiveContainer width="100%" height={260}>
              <PieChart>
                <Pie data={pieData} dataKey="value" nameKey="name" outerRadius={90} label>
                  {pieData.map((_: any, i: number) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          ) : <p className="text-slate-500 text-sm">No holdings.</p>}
        </div>
      </div>
    </div>
  );
}
