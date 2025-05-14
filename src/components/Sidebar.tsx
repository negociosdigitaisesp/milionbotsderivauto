import React, { useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { Menu, X, Home, BookOpen, ChartLine, Settings, Bot, FileText, Clock } from 'lucide-react';
import { cn } from '../lib/utils';

interface SidebarProps {
  collapsed: boolean;
  toggleSidebar: () => void;
}

const Sidebar = ({ collapsed, toggleSidebar }: SidebarProps) => {
  const location = useLocation();

  const navItems = [
    { name: 'Inicio', icon: <Home size={20} />, path: '/' },
    { name: 'Biblioteca', icon: <BookOpen size={20} />, path: '/library' },
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
            <Bot size={24} className="text-primary" />
            {!collapsed && <span className="font-bold text-lg text-primary">Million Bots</span>}
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

        <div className="p-4 border-t border-border/50">
          <div className={cn(
            "flex items-center gap-3",
            collapsed && "justify-center"
          )}>
            <div className="h-8 w-8 rounded-full bg-primary flex items-center justify-center text-primary-foreground font-semibold">
              U
            </div>
            {!collapsed && (
              <div className="flex flex-col">
                <span className="text-sm font-medium">Usuario</span>
                <span className="text-xs text-muted-foreground">Admin</span>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default Sidebar;
