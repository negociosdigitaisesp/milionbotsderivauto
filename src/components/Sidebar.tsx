
import React, { useState, useEffect } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { Menu, X, Home, BookOpen, ChartLine, Settings, FileText, Clock, LogOut, Zap } from 'lucide-react';
import { cn } from '../lib/utils';
import { useAuth } from '../contexts/AuthContext';

interface SidebarProps {
  collapsed: boolean;
  toggleSidebar: () => void;
}

const Sidebar = ({ collapsed, toggleSidebar }: SidebarProps) => {
  const location = useLocation();
  const navigate = useNavigate();
  const { user, signOut } = useAuth();
  const [profileInitial, setProfileInitial] = useState('U');

  // Obter a inicial do nome ou email do usuário
  useEffect(() => {
    if (user) {
      // Tentar obter o nome do usuário dos metadados
      const userName = user.user_metadata?.name || 
                     user.user_metadata?.full_name || 
                     user.email?.split('@')[0] || '';
      
      // Definir a inicial (primeira letra do nome ou email)
      if (userName) {
        setProfileInitial(userName.charAt(0).toUpperCase());
      }
    }
  }, [user]);

  // Função para obter o nome de exibição do usuário
  const getDisplayName = () => {
    if (!user) return 'Usuário';
    
    // Tentar obter o nome dos metadados do usuário
    const userName = user.user_metadata?.name || 
                   user.user_metadata?.full_name;
    
    // Retornar o nome se existir, ou o email sem o domínio
    return userName || (user.email ? user.email.split('@')[0] : 'Usuário');
  };

  // Função para fazer logout
  const handleLogout = async () => {
    try {
      await signOut();
      navigate('/login');
    } catch (error) {
      console.error('Erro ao fazer logout:', error);
    }
  };

  const navItems = [
    { name: 'Inicio', icon: <Home size={20} />, path: '/' },
    { name: 'Biblioteca', icon: <BookOpen size={20} />, path: '/library' },
    { name: 'Bots de Apalancamiento', icon: <Zap size={20} />, path: '/bots-apalancamiento' },

    { name: 'Analítica', icon: <ChartLine size={20} />, path: '/analytics' },
    { name: 'Mejores Horarios', icon: <Clock size={20} />, path: '/mejores-horarios' },
    { name: 'Tutorial de Instalación', icon: <FileText size={20} />, path: '/installation-tutorial' },
    { name: 'Configuración', icon: <Settings size={20} />, path: '/settings' }
  ];

  return (
    <div className={cn('sidebar-wrapper bg-sidebar shadow-md', collapsed ? 'sidebar-collapsed' : '')}>
      <div className="flex h-full flex-col">
        <div className="flex items-center justify-between p-4 border-b border-border/50">
          <div className={cn("flex items-center gap-3", collapsed && "justify-center")}>
            <img src="/lovable-uploads/65acdf4d-abfd-4e5a-b2c2-27c297ceb7c6.png" alt="Million Bots Logo" className="w-6 h-6" />
            {!collapsed && <span className="font-bold text-lg text-[#40E0D0]">Million Bots</span>}
          </div>
          <button 
            onClick={toggleSidebar} 
            className="p-1 rounded-md hover:bg-sidebar-accent text-sidebar-foreground/80"
          >
            {collapsed ? <Menu size={20} /> : <X size={20} />}
          </button>
        </div>

        <nav className="flex-1 p-2 space-y-1">
          {navItems.map((item) => (
            <Link
              key={item.name}
              to={item.path}
              className={cn(
                "flex items-center gap-3 px-3 py-2 rounded-md transition-colors",
                location.pathname === item.path 
                  ? "bg-sidebar-accent text-primary" 
                  : "text-sidebar-foreground/70 hover:bg-sidebar-accent/80 hover:text-sidebar-foreground",
                collapsed && "justify-center p-2"
              )}
            >
              <span>{item.icon}</span>
              {!collapsed && <span>{item.name}</span>}
            </Link>
          ))}
        </nav>

        <div className="p-4 border-t border-border/50 space-y-3">
          <div className={cn(
            "flex items-center gap-3",
            collapsed && "justify-center"
          )}>
            <div className="h-8 w-8 rounded-full bg-primary flex items-center justify-center text-primary-foreground font-semibold">
              {profileInitial}
            </div>
            {!collapsed && (
              <div className="flex flex-col">
                <span className="text-sm font-medium">{getDisplayName()}</span>
                <span className="text-xs text-muted-foreground">{user?.email}</span>
              </div>
            )}
          </div>
          
          <button
            onClick={handleLogout}
            className={cn(
              "flex items-center gap-2 w-full px-3 py-2 rounded-md text-sidebar-foreground/70 hover:bg-sidebar-accent/80 hover:text-sidebar-foreground transition-colors",
              collapsed && "justify-center"
            )}
          >
            <LogOut size={18} />
            {!collapsed && <span className="text-sm">Sair</span>}
          </button>
        </div>
      </div>
    </div>
  );
};

export default Sidebar;
