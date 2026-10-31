import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '../lib/api';

export default function Orders() {
  const [status, setStatus] = useState('');
  const qc = useQueryClient();

  const { data: orders } = useQuery({
    queryKey: ['orders', status],
    queryFn: async () => (await api.get('/orders', { params: status ? { status } : {} })).data,
  });

  const cancelMutation = useMutation({
    mutationFn: async (id: number) => (await api.delete(`/orders/${id}`)).data,
    onSuccess: () => qc.invalidateQueries({ queryKey: ['orders'] }),
  });

  const exportCSV = () => {
    if (!orders) return;
    const header = 'id,symbol,side,type,quantity,status,filled_price,created_at\n';
    const rows = orders.map((o: any) => `${o.id},${o.symbol},${o.side},${o.type},${o.quantity},${o.status},${o.filled_price ?? ''},${o.created_at}`).join('\n');
    const blob = new Blob([header + rows], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url; a.download = 'orders.csv'; a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <h1 className="text-2xl font-bold text-emerald-400">Orders</h1>
        <div className="flex gap-2">
          <select value={status} onChange={(e) => setStatus(e.target.value)} className="bg-slate-800 border border-slate-700 rounded px-3 py-2">
            <option value="">All</option>
            <option value="PENDING">Pending</option>
            <option value="FILLED">Filled</option>
            <option value="CANCELLED">Cancelled</option>
            <option value="REJECTED">Rejected</option>
          </select>
          <button onClick={exportCSV} className="bg-slate-800 px-3 py-2 rounded hover:bg-slate-700">Export CSV</button>
        </div>
      </div>
      <div className="bg-slate-900 border border-slate-800 rounded overflow-x-auto">
        <table className="w-full text-sm">
          <thead className="text-slate-400">
            <tr><th className="text-left p-3">ID</th><th>Symbol</th><th>Side</th><th>Type</th><th>Qty</th><th>Status</th><th>Filled</th><th>Created</th><th></th></tr>
          </thead>
          <tbody>
            {(orders || []).map((o: any) => (
              <tr key={o.id} className="border-t border-slate-800">
                <td className="p-3">{o.id}</td>
                <td className="text-center">{o.symbol}</td>
                <td className={`text-center ${o.side === 'BUY' ? 'text-emerald-400' : 'text-red-400'}`}>{o.side}</td>
                <td className="text-center">{o.type}</td>
                <td className="text-center">{o.quantity}</td>
                <td className="text-center">{o.status}</td>
                <td className="text-center">{o.filled_price ?? '—'}</td>
                <td className="text-center text-xs">{new Date(o.created_at).toLocaleString()}</td>
                <td className="text-center">
                  {o.status === 'PENDING' && (
                    <button onClick={() => cancelMutation.mutate(o.id)} className="text-xs bg-red-600 px-2 py-1 rounded">Cancel</button>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {(!orders || orders.length === 0) && <p className="p-4 text-slate-500">No orders.</p>}
      </div>
    </div>
  );
}
