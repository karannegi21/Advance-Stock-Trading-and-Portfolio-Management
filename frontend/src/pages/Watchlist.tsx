import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '../lib/api';
import { Link } from 'react-router-dom';

export default function Watchlist() {
  const qc = useQueryClient();
  const { data } = useQuery({ queryKey: ['watchlist'], queryFn: async () => (await api.get('/watchlist')).data });

  const removeMutation = useMutation({
    mutationFn: async (symbol: string) => (await api.delete(`/watchlist/${symbol}`)).data,
    onSuccess: () => qc.invalidateQueries({ queryKey: ['watchlist'] }),
  });

  return (
    <div>
      <h1 className="text-2xl font-bold text-emerald-400 mb-4">Watchlist</h1>
      <div className="bg-slate-900 border border-slate-800 rounded">
        <table className="w-full text-sm">
          <thead className="text-slate-400"><tr><th className="text-left p-3">Symbol</th><th>Name</th><th></th></tr></thead>
          <tbody>
            {(data || []).map((w: any) => (
              <tr key={w.id} className="border-t border-slate-800">
                <td className="p-3 font-semibold"><Link to={`/stocks/${w.symbol}`} className="hover:text-emerald-400">{w.symbol}</Link></td>
                <td className="text-center">{w.name}</td>
                <td className="text-center">
                  <button onClick={() => removeMutation.mutate(w.symbol)} className="text-xs bg-red-600 px-2 py-1 rounded">Remove</button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {(!data || data.length === 0) && <p className="p-4 text-slate-500">Empty watchlist. Add from Market.</p>}
      </div>
    </div>
  );
}
