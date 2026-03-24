import { Outlet, Navigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import Sidebar from "./Sidebar";
import Header from "./Header";

export default function AppLayout() {
  const { isAuthenticated } = useAuth();

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  return (
    <div className="flex min-h-screen relative overflow-hidden bg-bg">
      <Sidebar />
      <div className="ml-64 flex flex-1 flex-col relative z-10 transition-all duration-300">
        <Header />
        <main className="flex-1 p-8 animate-fade-in">
          <div className="mx-auto max-w-[1600px]">
            <Outlet />
          </div>
        </main>
      </div>
    </div>
  );
}
