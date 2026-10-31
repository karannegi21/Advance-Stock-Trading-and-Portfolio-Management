import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '../lib/api';

export default function AdminPanel() {
  const qc = useQueryClient();
  const { data: status } = useQuery({ queryKey: ['sim-status'], queryFn: async () => (await api.get('/admin/simulator/status')).data, refetchInterval: 3000 });

  const act = useMutation({
    mutationFn: async (action: string) => (await api.post(`/admin/simulator/${action}`)).data,
    onSuccess: () => qc.invalidateQueries({ queryKey: ['sim-status'] }),
  });

  return (
    <div>
      <h1 className="text-2xl font-bold text-emerald-400 mb-4">Admin Panel</h1>
      <div className="bg-slate-900 border border-slate-800 rounded p-6 max-w-md">
        <p className="mb-2">Current sim date: <span className="font-semibold">{status?.current_sim_date}</span></p>
        <p className="mb-4">Running: <span className={status?.is_running ? 'text-emerald-400' : 'text-red-400'}>{String(status?.is_running)}</span></p>
        <div className="flex gap-2">
          <button onClick={() => act.mutate('start')} className="bg-emerald-600 px-3 py-2 rounded">Start</button>
          <button onClick={() => act.mutate('pause')} className="bg-slate-700 px-3 py-2 rounded">Pause</button>
          <button onClick={() => act.mutate('reset')} className="bg-red-600 px-3 py-2 rounded">Reset</button>
        </div>
      </div>
    </div>
  );
}
