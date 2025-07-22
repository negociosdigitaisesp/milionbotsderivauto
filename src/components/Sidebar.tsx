
import React, { useState, useEffect } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { 
  Menu, 
  X, 
  Home, 
  BookOpen, 
  ChartLine, 
  Settings, 
  FileText, 
  Clock, 
  LogOut, 
  Zap,
  User,
  ChevronRight,
  Sparkles,
  TrendingUp,
  Crown
} from 'lucide-react';
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
  const [isMobile, setIsMobile] = useState(false);

  // Detectar se é mobile
  useEffect(() => {
    const checkMobile = () => {
      setIsMobile(window.innerWidth < 768);
    };
    
    checkMobile();
    window.addEventListener('resize', checkMobile);
    return () => window.removeEventListener('resize', checkMobile);
  }, []);

  // Obter a inicial do nome ou email do usuário
  useEffect(() => {
    if (user) {
      const userName = user.user_metadata?.name || 
                     user.user_metadata?.full_name || 
                     user.email?.split('@')[0] || '';
      
      if (userName) {
        setProfileInitial(userName.charAt(0).toUpperCase());
      }
    }
  }, [user]);

  // Função para obter o nome de exibição do usuário
  const getDisplayName = () => {
    if (!user) return 'Usuário';
    
    const userName = user.user_metadata?.name || 
                   user.user_metadata?.full_name;
    
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
    { 
      name: 'Ranking del Asertividad', 
      icon: <BookOpen size={20} />, 
      path: '/',
      badge: null,
      description: 'Robots disponibles'
    },
    { 
      name: 'Bots de Apalancamiento', 
      icon: <Zap size={20} />, 
      path: '/bots-apalancamiento',
      badge: null,
      description: 'Trading avanzado'
    },
    { 
      name: 'Analítica', 
      icon: <ChartLine size={20} />, 
      path: '/analytics',
      badge: null,
      description: 'Métricas y estadísticas'
    },
    { 
      name: 'Mejores Horarios', 
      icon: <Clock size={20} />, 
      path: '/mejores-horarios',
      badge: null,
      description: 'Optimización temporal'
    },
    { 
      name: 'Tutorial de Instalación', 
      icon: <FileText size={20} />, 
      path: '/installation-tutorial',
      badge: null,
      description: 'Guía paso a paso'
    },
    { 
      name: 'Configuración', 
      icon: <Settings size={20} />, 
      path: '/settings',
      badge: null,
      description: 'Ajustes del sistema'
    }
  ];

  return (
    <>
      {/* Overlay para mobile */}
      {isMobile && !collapsed && (
        <div 
          className="fixed inset-0 bg-black/50 backdrop-blur-sm z-30 md:hidden"
          onClick={toggleSidebar}
        />
      )}

      {/* Sidebar */}
      <div className={cn(
        'sidebar-wrapper bg-gradient-to-b from-sidebar to-sidebar/95 shadow-2xl border-r border-sidebar-border/20',
        'transition-all duration-300 ease-in-out z-40',
        isMobile ? (
          collapsed 
            ? '-translate-x-full' 
            : 'translate-x-0'
        ) : (
          collapsed ? 'sidebar-collapsed' : ''
        )
      )}>
        <div className="flex h-full flex-col relative">
          {/* Header com gradiente */}
          <div className="relative">
            <div className="absolute inset-0 bg-gradient-to-r from-primary/10 to-transparent opacity-50" />
            <div className="relative flex items-center justify-between p-4 border-b border-sidebar-border/30 backdrop-blur-sm">
              <div className={cn(
                "flex items-center gap-3 transition-all duration-300",
                collapsed && !isMobile && "justify-center"
              )}>
                <div className="relative">
                  <div className="absolute inset-0 bg-primary/20 rounded-full blur-md" />
                  <img 
                    src="/lovable-uploads/65acdf4d-abfd-4e5a-b2c2-27c297ceb7c6.png" 
                    alt="Million Bots Logo" 
                    className="relative w-8 h-8 rounded-full border border-primary/30" 
                  />
                </div>
                {(!collapsed || isMobile) && (
                  <div className="flex flex-col">
                    <span className="font-bold text-lg bg-gradient-to-r from-primary to-primary/80 bg-clip-text text-transparent">
                      Million Bots
                    </span>
                    <span className="text-xs text-sidebar-foreground/60 font-medium">
                      Trading Intelligence
                    </span>
                  </div>
                )}
              </div>
              
              <button 
                onClick={toggleSidebar} 
                className={cn(
                  "group relative p-2 rounded-lg transition-all duration-200",
                  "hover:bg-sidebar-accent/50 text-sidebar-foreground/80 hover:text-sidebar-foreground",
                  "border border-transparent hover:border-sidebar-border/30"
                )}
              >
                <div className="absolute inset-0 bg-gradient-to-r from-primary/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity rounded-lg" />
                {collapsed && !isMobile ? (
                  <Menu size={20} className="relative z-10" />
                ) : (
                  <X size={20} className="relative z-10" />
                )}
              </button>
            </div>
          </div>

          {/* Navigation */}
          <nav className="flex-1 p-3 space-y-1 overflow-y-auto scrollbar-thin scrollbar-thumb-sidebar-accent scrollbar-track-transparent">
            {navItems.map((item, index) => {
              const isActive = location.pathname === item.path;
              
              return (
                <Link
                  key={item.name}
                  to={item.path}
                  className={cn(
                    "group relative flex items-center gap-3 px-3 py-3 rounded-xl transition-all duration-200",
                    "hover:bg-sidebar-accent/60 hover:shadow-lg hover:shadow-primary/5",
                    "border border-transparent hover:border-sidebar-border/20",
                    isActive && "bg-gradient-to-r from-primary/15 to-primary/5 border-primary/20 shadow-lg shadow-primary/10",
                    collapsed && !isMobile && "justify-center px-2"
                  )}
                >
                  {/* Background gradient para item ativo */}
                  {isActive && (
                    <div className="absolute inset-0 bg-gradient-to-r from-primary/10 to-transparent rounded-xl" />
                  )}
                  
                  {/* Indicador lateral para item ativo */}
                  {isActive && (
                    <div className="absolute left-0 top-1/2 -translate-y-1/2 w-1 h-8 bg-gradient-to-b from-primary to-primary/60 rounded-r-full" />
                  )}
                  
                  <div className={cn(
                    "relative flex items-center justify-center w-10 h-10 rounded-lg transition-all duration-200",
                    isActive 
                      ? "bg-primary/20 text-primary shadow-lg shadow-primary/20" 
                      : "bg-sidebar-accent/30 text-sidebar-foreground/70 group-hover:bg-primary/10 group-hover:text-primary/80"
                  )}>
                    {item.icon}
                  </div>
                  
                  {(!collapsed || isMobile) && (
                    <div className="relative flex-1 min-w-0">
                      <div className="flex items-center justify-between">
                        <div>
                          <span className={cn(
                            "font-medium text-sm transition-colors",
                            isActive 
                              ? "text-primary" 
                              : "text-sidebar-foreground group-hover:text-sidebar-foreground"
                          )}>
                            {item.name}
                          </span>
                          <p className="text-xs text-sidebar-foreground/50 mt-0.5 truncate">
                            {item.description}
                          </p>
                        </div>
                      </div>
                    </div>
                  )}
                  
                  {(!collapsed || isMobile) && (
                    <ChevronRight 
                      size={16} 
                      className={cn(
                        "text-sidebar-foreground/30 transition-all duration-200",
                        "group-hover:text-sidebar-foreground/60 group-hover:translate-x-1",
                        isActive && "text-primary/60"
                      )} 
                    />
                  )}
                </Link>
              );
            })}
          </nav>

          {/* User Profile Section */}
          <div className="relative">
            <div className="absolute inset-0 bg-gradient-to-t from-sidebar-accent/20 to-transparent" />
            <div className="relative p-4 border-t border-sidebar-border/30 space-y-3">
              {/* User Info */}
              <div className={cn(
                "flex items-center gap-3 p-3 rounded-xl bg-sidebar-accent/30 border border-sidebar-border/20",
                "hover:bg-sidebar-accent/50 transition-all duration-200",
                collapsed && !isMobile && "justify-center"
              )}>
                <div className="relative">
                  <div className="absolute inset-0 bg-primary/20 rounded-full blur-sm" />
                  <div className="relative h-10 w-10 rounded-full bg-gradient-to-br from-primary to-primary/80 flex items-center justify-center text-primary-foreground font-bold shadow-lg">
                    {profileInitial}
                  </div>
                  <div className="absolute -top-1 -right-1 w-5 h-5 bg-gradient-to-br from-amber-400 to-amber-600 rounded-full border-2 border-sidebar shadow-lg flex items-center justify-center">
                    <Crown size={10} className="text-amber-100" />
                  </div>
                  <div className="absolute -bottom-1 -right-1 w-4 h-4 bg-green-500 rounded-full border-2 border-sidebar shadow-sm" />
                </div>
                
                {(!collapsed || isMobile) && (
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <span className="text-sm font-semibold text-sidebar-foreground truncate">
                        {getDisplayName()}
                      </span>
                      <Sparkles size={14} className="text-primary/60 flex-shrink-0" />
                    </div>
                    <span className="text-xs text-sidebar-foreground/60 truncate block">
                      {user?.email}
                    </span>
                  </div>
                )}
              </div>
              
              {/* Logout Button */}
              <button
                onClick={handleLogout}
                className={cn(
                  "group flex items-center gap-3 w-full px-3 py-3 rounded-xl transition-all duration-200",
                  "text-sidebar-foreground/70 hover:text-red-400 hover:bg-red-500/10",
                  "border border-transparent hover:border-red-500/20",
                  collapsed && !isMobile && "justify-center"
                )}
              >
                <div className="flex items-center justify-center w-10 h-10 rounded-lg bg-sidebar-accent/30 group-hover:bg-red-500/20 transition-all duration-200">
                  <LogOut size={18} className="group-hover:scale-110 transition-transform" />
                </div>
                {(!collapsed || isMobile) && (
                  <span className="text-sm font-medium">Cerrar Sesión</span>
                )}
              </button>
            </div>
          </div>
        </div>
      </div>
    </>
  );
};

export default Sidebar;
