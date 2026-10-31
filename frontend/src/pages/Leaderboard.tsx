import { useQuery } from '@tanstack/react-query';
import { api } from '../lib/api';

export default function Leaderboard() {
  const { data } = useQuery({ queryKey: ['leaderboard'], queryFn: async () => (await api.get('/leaderboard')).data });
  return (
    <div>
      <h1 className="text-2xl font-bold text-emerald-400 mb-4">Leaderboard</h1>
      <div className="bg-slate-900 border border-slate-800 rounded">
        <table className="w-full text-sm">
          <thead className="text-slate-400"><tr><th className="text-left p-3">Rank</th><th>Name</th><th>Total Value</th><th>Return %</th></tr></thead>
          <tbody>
            {(data || []).map((r: any, i: number) => (
              <tr key={r.user_id} className="border-t border-slate-800">
                <td className="p-3">{i + 1}</td>
                <td className="text-center">{r.name}</td>
                <td className="text-center">{Number(r.total_value).toFixed(2)}</td>
                <td className={`text-center ${r.return_pct >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>{r.return_pct}%</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
