import { useState } from "react";
import { Toaster } from "@/components/ui/toaster";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import Sidebar from "./components/Sidebar";
import Index from "./pages/Index";
import BotDetail from "./pages/BotDetail";
import NotFound from "./pages/NotFound";
import InstallationTutorial from "./pages/InstallationTutorial";
import BestHours from "./pages/BestHours";
import Analytics from "./pages/Analytics";
import Library from "./pages/Library";
import SettingsPage from "./pages/Settings";
import Auth from "./pages/Auth";
import AuthCallback from "./pages/AuthCallback";
import DerivCallback from "./pages/DerivCallback";
import DerivIntegration from "./pages/DerivIntegration";
import PendingApprovalPage from "./pages/PendingApprovalPage";
import VerificandoAcessoPage from "./pages/VerificandoAcessoPage";
import BotsApalancamiento from "./pages/BotsApalancamiento";
import RiskManagement from "./pages/RiskManagement";
import { AuthProvider } from "./contexts/AuthContext";
import ProtectedRoute from "./components/ProtectedRoute";
import SecurityGate from "./components/SecurityGate";
import PaginaDeTeste from "./pages/PaginaDeTeste";
import PaginaBloqueada from "./pages/PaginaBloqueada";

const queryClient = new QueryClient();

const App = () => {
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  
  const toggleSidebar = () => {
    setSidebarCollapsed(prev => !prev);
  };

  return (
    <BrowserRouter>
      <QueryClientProvider client={queryClient}>
        <TooltipProvider>
          <AuthProvider>
            <Toaster />
            <Sonner />
            <div className="min-h-screen bg-background">
              <Routes>
                <Route path="/login" element={<Auth />} />
                <Route path="/auth/callback" element={<AuthCallback />} />
                <Route path="/deriv/callback" element={<DerivCallback />} />
                <Route path="/pending-approval" element={<PendingApprovalPage />} />
                <Route path="/verificando-acesso" element={<VerificandoAcessoPage />} />
                
                {/* Rota raiz com Portão de Segurança */}
                <Route path="/" element={<SecurityGate><Index /></SecurityGate>} />
                
                {/* Rotas protegidas */}
                <Route element={<ProtectedRoute />}>
                  <Route path="/dashboard" element={
                    <>
                      <Sidebar collapsed={sidebarCollapsed} toggleSidebar={toggleSidebar} />
                      <main className={`transition-all duration-300 ${sidebarCollapsed ? 'main-content-expanded' : 'main-content'}`}>
                        <Index />
                      </main>
                    </>
                  } />
                  
                  <Route path="/bot/:id" element={
                    <>
                      <Sidebar collapsed={sidebarCollapsed} toggleSidebar={toggleSidebar} />
                      <main className={`transition-all duration-300 ${sidebarCollapsed ? 'main-content-expanded' : 'main-content'}`}>
                        <BotDetail />
                      </main>
                    </>
                  } />
                  
                  <Route path="/library" element={
                    <>
                      <Sidebar collapsed={sidebarCollapsed} toggleSidebar={toggleSidebar} />
                      <main className={`transition-all duration-300 ${sidebarCollapsed ? 'main-content-expanded' : 'main-content'}`}>
                        <Library />
                      </main>
                    </>
                  } />
                  
                  <Route path="/installation-tutorial" element={
                    <>
                      <Sidebar collapsed={sidebarCollapsed} toggleSidebar={toggleSidebar} />
                      <main className={`transition-all duration-300 ${sidebarCollapsed ? 'main-content-expanded' : 'main-content'}`}>
                        <InstallationTutorial />
                      </main>
                    </>
                  } />
                  
                  <Route path="/mejores-horarios" element={
                    <>
                      <Sidebar collapsed={sidebarCollapsed} toggleSidebar={toggleSidebar} />
                      <main className={`transition-all duration-300 ${sidebarCollapsed ? 'main-content-expanded' : 'main-content'}`}>
                        <BestHours />
                      </main>
                    </>
                  } />
                  
                  <Route path="/analytics" element={
                    <>
                      <Sidebar collapsed={sidebarCollapsed} toggleSidebar={toggleSidebar} />
                      <main className={`transition-all duration-300 ${sidebarCollapsed ? 'main-content-expanded' : 'main-content'}`}>
                        <Analytics />
                      </main>
                    </>
                  } />
                  
                  <Route path="/settings" element={
                    <>
                      <Sidebar collapsed={sidebarCollapsed} toggleSidebar={toggleSidebar} />
                      <main className={`transition-all duration-300 ${sidebarCollapsed ? 'main-content-expanded' : 'main-content'}`}>
                        <SettingsPage />
                      </main>
                    </>
                  } />
                  
                  <Route path="/bots-apalancamiento" element={
                    <>
                      <Sidebar collapsed={sidebarCollapsed} toggleSidebar={toggleSidebar} />
                      <main className={`transition-all duration-300 ${sidebarCollapsed ? 'main-content-expanded' : 'main-content'}`}>
                        <BotsApalancamiento />
                      </main>
                    </>
                  } />
                  
                  <Route path="/risk-management" element={
                    <>
                      <Sidebar collapsed={sidebarCollapsed} toggleSidebar={toggleSidebar} />
                      <main className={`transition-all duration-300 ${sidebarCollapsed ? 'main-content-expanded' : 'main-content'}`}>
                        <RiskManagement />
                      </main>
                    </>
                  } />
                  
                  <Route path="/deriv-integration" element={
                    <>
                      <Sidebar collapsed={sidebarCollapsed} toggleSidebar={toggleSidebar} />
                      <main className={`transition-all duration-300 ${sidebarCollapsed ? 'main-content-expanded' : 'main-content'}`}>
                        <DerivIntegration />
                      </main>
                    </>
                  } />
                </Route>
                
                <Route path="/pagina-de-teste" element={<PaginaDeTeste />} />
                <Route path="/PaginaBloqueada" element={<PaginaBloqueada />} />
                <Route path="*" element={<NotFound />} />
              </Routes>
            </div>
          </AuthProvider>
        </TooltipProvider>
      </QueryClientProvider>
    </BrowserRouter>
  );
};

export default App;
