import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useMutation } from '@tanstack/react-query';
import { api } from '../lib/api';
import { useAuthStore } from '../store/authStore';

export default function Login() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const navigate = useNavigate();
  const setAuth = useAuthStore((s) => s.setAuth);

  const mutation = useMutation({
    mutationFn: async () => {
      const r = await api.post('/auth/login', { email, password });
      return r.data;
    },
    onSuccess: (data) => {
      setAuth(data.user, data.access_token, data.refresh_token);
      navigate('/market');
    },
    onError: (e: any) => setError(e.response?.data?.detail || 'Login failed'),
  });

  return (
    <div className="max-w-md mx-auto mt-16 bg-slate-900 border border-slate-800 rounded-xl p-8">
      <h2 className="text-2xl font-bold mb-6 text-emerald-400">Login</h2>
      {error && <p className="text-red-400 text-sm mb-4">{error}</p>}
      <form onSubmit={(e) => { e.preventDefault(); mutation.mutate(); }} className="space-y-4">
        <input className="w-full bg-slate-800 border border-slate-700 rounded px-3 py-2" placeholder="Email" value={email} onChange={(e) => setEmail(e.target.value)} />
        <input type="password" className="w-full bg-slate-800 border border-slate-700 rounded px-3 py-2" placeholder="Password" value={password} onChange={(e) => setPassword(e.target.value)} />
        <button type="submit" className="w-full bg-emerald-600 hover:bg-emerald-500 py-2 rounded font-semibold" disabled={mutation.isPending}>
          {mutation.isPending ? 'Logging in...' : 'Login'}
        </button>
      </form>
      <p className="text-sm text-slate-400 mt-4">No account? <Link to="/register" className="text-emerald-400">Register</Link></p>
    </div>
  );
}
