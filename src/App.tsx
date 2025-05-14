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

const queryClient = new QueryClient();

const App = () => {
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  
  const toggleSidebar = () => {
    setSidebarCollapsed(prev => !prev);
  };

  return (
    <QueryClientProvider client={queryClient}>
      <TooltipProvider>
        <Toaster />
        <Sonner />
        <BrowserRouter>
          <div className="min-h-screen bg-background">
            <Sidebar collapsed={sidebarCollapsed} toggleSidebar={toggleSidebar} />
            
            <main className={`transition-all duration-300 ${sidebarCollapsed ? 'main-content-expanded' : 'main-content'}`}>
              <Routes>
                <Route path="/" element={<Index />} />
                <Route path="/bot/:id" element={<BotDetail />} />
                <Route path="/library" element={<Library />} />
                <Route path="/installation-tutorial" element={<InstallationTutorial />} />
                <Route path="/mejores-horarios" element={<BestHours />} />
                <Route path="/analytics" element={<Analytics />} />
                <Route path="/settings" element={<SettingsPage />} />
                <Route path="*" element={<NotFound />} />
              </Routes>
            </main>
          </div>
        </BrowserRouter>
      </TooltipProvider>
    </QueryClientProvider>
  );
};

export default App;
