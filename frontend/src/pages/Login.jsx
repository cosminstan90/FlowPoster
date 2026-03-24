import { useState } from "react";
import { useNavigate, Navigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { LogIn, AlertCircle, Loader2, Sparkles } from "lucide-react";

export default function Login() {
  const { login, isAuthenticated } = useAuth();
  const navigate = useNavigate();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  if (isAuthenticated) return <Navigate to="/" replace />;

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      await login(username, password);
      navigate("/", { replace: true });
    } catch (err) {
      setError(err.response?.data?.detail || "Autentificare esuată");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="relative flex min-h-screen items-center justify-center overflow-hidden bg-bg px-4 py-12 sm:px-6 lg:px-8">
      {/* Animated Background Elements */}
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-full h-full max-w-7xl pointer-events-none">
        <div className="absolute top-20 left-20 w-96 h-96 bg-accent/20 rounded-full blur-[120px] mix-blend-screen animate-pulse-slow"></div>
        <div className="absolute bottom-20 right-20 w-[30rem] h-[30rem] bg-cyan-500/10 rounded-full blur-[150px] mix-blend-screen animate-pulse-slow" style={{ animationDelay: '2s' }}></div>
      </div>

      <div className="relative w-full max-w-md animate-fade-in z-10">
        {/* Logo Section */}
        <div className="mb-10 flex flex-col items-center animate-slide-up">
          <div className="relative flex h-16 w-16 items-center justify-center rounded-2xl bg-gradient-to-br from-accent to-cyan-500 shadow-[0_0_30px_rgba(16,185,129,0.4)] mb-6">
            <Sparkles className="h-8 w-8 text-white" />
            <div className="absolute inset-0 rounded-2xl ring-1 ring-white/20"></div>
          </div>
          <h1 className="text-3xl font-display font-bold text-white tracking-tight">SEO Publisher</h1>
          <p className="mt-2 text-base text-muted/80">Platforma AI pentru automatizare SEO</p>
        </div>

        {/* Login Card */}
        <form
          onSubmit={handleSubmit}
          className="glass-panel p-8 sm:p-10 space-y-6 rounded-3xl animate-slide-up"
          style={{ animationDelay: '100ms' }}
        >
          <div className="text-center mb-8">
            <h2 className="text-xl font-semibold text-white/90">Autentificare in cont</h2>
            <p className="text-sm text-muted mt-1">Introdu datele de acces pentru a continua</p>
          </div>

          {error && (
            <div className="flex items-center gap-3 rounded-xl bg-red-500/10 border border-red-500/20 p-4 text-sm text-red-200 animate-fade-in">
              <AlertCircle className="h-5 w-5 shrink-0 text-red-400" />
              <p>{error}</p>
            </div>
          )}

          <div className="space-y-5">
            <div>
              <label className="mb-2 block text-sm font-medium text-white/70">Utilizator</label>
              <div className="relative">
                <input
                  type="text"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  required
                  autoFocus
                  className="w-full rounded-xl border border-border/80 bg-surface/50 px-4 py-3 text-base text-white transition-all placeholder:text-muted/50 focus:border-accent focus:bg-surface focus:outline-none focus:ring-1 focus:ring-accent/50"
                  placeholder="admin"
                />
              </div>
            </div>

            <div>
              <label className="mb-2 block text-sm font-medium text-white/70">Parola</label>
              <div className="relative">
                <input
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                  className="w-full rounded-xl border border-border/80 bg-surface/50 px-4 py-3 text-base text-white transition-all placeholder:text-muted/50 focus:border-accent focus:bg-surface focus:outline-none focus:ring-1 focus:ring-accent/50"
                  placeholder="••••••••"
                />
              </div>
            </div>
          </div>

          <button
            type="submit"
            disabled={loading}
            className="glass-button mt-8 flex w-full items-center justify-center gap-2 rounded-xl bg-gradient-to-r from-accent to-cyan-500 px-4 py-3.5 text-base font-semibold text-white shadow-lg shadow-accent/25 transition-all hover:shadow-accent/40 disabled:opacity-70 disabled:grayscale-[30%]"
          >
            {loading ? (
              <Loader2 className="h-5 w-5 animate-spin" />
            ) : (
              <LogIn className="h-5 w-5" />
            )}
            Autentificare
          </button>
        </form>
        
        {/* Footer */}
        <p className="mt-8 text-center text-sm text-muted/50 animate-fade-in" style={{ animationDelay: '200ms' }}>
          &copy; {new Date().getFullYear()} SEO Publisher. Toate drepturile rezervate.
        </p>
      </div>
    </div>
  );
}
