import { Link, useNavigate } from 'react-router-dom';
import { useAuthStore } from '../store/authStore';

export default function Layout({ children }: { children: React.ReactNode }) {
  const { user, logout } = useAuthStore();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100">
      <nav className="border-b border-slate-800 bg-slate-900/80 backdrop-blur sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 py-3 flex items-center justify-between">
          <Link to="/" className="font-bold text-emerald-400 text-lg">📈 StockPlatform</Link>
          <div className="flex gap-4 text-sm items-center">
            <Link to="/market" className="hover:text-emerald-400">Market</Link>
            <Link to="/portfolio" className="hover:text-emerald-400">Portfolio</Link>
            <Link to="/orders" className="hover:text-emerald-400">Orders</Link>
            <Link to="/analytics" className="hover:text-emerald-400">Analytics</Link>
            <Link to="/watchlist" className="hover:text-emerald-400">Watchlist</Link>
            <Link to="/leaderboard" className="hover:text-emerald-400">Leaderboard</Link>
            {user?.role === 'admin' && <Link to="/admin" className="hover:text-emerald-400">Admin</Link>}
            {user ? (
              <>
                <span className="text-slate-400">{user.full_name}</span>
                <button onClick={handleLogout} className="bg-slate-800 px-3 py-1 rounded hover:bg-slate-700">Logout</button>
              </>
            ) : (
              <>
                <Link to="/login" className="hover:text-emerald-400">Login</Link>
                <Link to="/register" className="bg-emerald-600 px-3 py-1 rounded hover:bg-emerald-500">Register</Link>
              </>
            )}
          </div>
        </div>
      </nav>
      <main className="max-w-7xl mx-auto px-4 py-6">{children}</main>
    </div>
  );
}
