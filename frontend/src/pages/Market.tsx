import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { api } from '../lib/api';
import { useWebSocket } from '../hooks/useWebSocket';
import { Link } from 'react-router-dom';

export default function Market() {
  const [search, setSearch] = useState('');
  const [prices, setPrices] = useState<Record<string, number>>({});

  useWebSocket((data) => {
    if (data?.type === 'prices') {
      const map: Record<string, number> = {};
      data.prices?.forEach((p: any) => { if (p.price != null) map[p.symbol] = p.price; });
      setPrices((prev) => ({ ...prev, ...map }));
    }
  });

  const { data: stocks, isLoading } = useQuery({
    queryKey: ['stocks', search],
    queryFn: async () => {
      const r = await api.get('/stocks', { params: { q: search || undefined, limit: 100 } });
      return r.data;
    },
  });

  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <h1 className="text-2xl font-bold text-emerald-400">Market</h1>
        <input className="bg-slate-800 border border-slate-700 rounded px-3 py-2 w-64" placeholder="Search symbol/name" value={search} onChange={(e) => setSearch(e.target.value)} />
      </div>
      {isLoading && <p>Loading...</p>}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {(stocks || []).map((s: any) => {
          const live = prices[s.symbol] ?? s.current_price;
          return (
            <Link to={`/stocks/${s.symbol}`} key={s.symbol} className="bg-slate-900 border border-slate-800 rounded-lg p-4 hover:border-emerald-500 transition">
              <div className="flex justify-between items-start">
                <div>
                  <p className="font-bold text-lg">{s.symbol}</p>
                  <p className="text-xs text-slate-400">{s.name}</p>
                  <p className="text-xs text-slate-500">{s.sector}</p>
                </div>
                <div className="text-right">
                  <p className="text-lg font-semibold">{live != null ? Number(live).toFixed(2) : '—'}</p>
                  {s.change_pct != null && <p className={`text-xs ${Number(s.change_pct) >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>{Number(s.change_pct).toFixed(2)}%</p>}
                </div>
              </div>
            </Link>
          );
        })}
      </div>
    </div>
  );
}
