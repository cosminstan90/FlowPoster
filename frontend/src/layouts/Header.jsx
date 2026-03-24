import { LogOut, Bell, User } from "lucide-react";
import { useAuth } from "../context/AuthContext";

export default function Header() {
  const { logout } = useAuth();

  return (
    <header className="sticky top-0 z-20 flex h-20 items-center justify-between px-8 backdrop-blur-md bg-bg/60 border-b border-border transition-all">
      <div className="flex items-center gap-4">
        <h2 className="text-xl font-display font-semibold text-white/90 tracking-tight">
          Panou de control
        </h2>
      </div>
      
      <div className="flex items-center gap-5">
        <button className="relative p-2 text-muted hover:text-white transition-colors rounded-full hover:bg-white/5">
          <Bell className="h-5 w-5" />
          <span className="absolute top-1.5 right-1.5 h-2 w-2 rounded-full bg-accent animate-pulse"></span>
        </button>
        
        <div className="h-6 w-[1px] bg-border mx-1"></div>

        <div className="flex items-center gap-4">
          <div className="h-9 w-9 rounded-full bg-gradient-to-tr from-accent to-cyan-500 p-[2px] shadow-lg shadow-accent/20">
            <div className="h-full w-full rounded-full bg-bg-card flex items-center justify-center">
              <User className="h-4 w-4 text-white/80" />
            </div>
          </div>
          <button
            onClick={logout}
            className="flex items-center gap-2 rounded-lg px-4 py-2 text-sm font-medium text-muted transition-all hover:bg-red-500/10 hover:text-red-400 border border-transparent hover:border-red-500/20"
          >
            <LogOut className="h-4 w-4" />
            Deconectare
          </button>
        </div>
      </div>
    </header>
  );
}
