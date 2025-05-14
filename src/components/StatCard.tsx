import React from 'react';
import { cn } from '../lib/utils';

interface StatCardProps {
  title: string;
  value: string | number;
  icon: React.ReactNode;
  trend?: {
    value: number;
    isPositive: boolean;
  };
  className?: string;
}

const StatCard = ({ title, value, icon, trend, className }: StatCardProps) => {
  return (
    <div className={cn("stat-card", className)}>
      <div className="flex items-center gap-2 mb-4">
        <div className="p-2 rounded-full bg-primary/10 text-primary">{icon}</div>
        <h3 className="text-sm font-medium text-muted-foreground">{title}</h3>
      </div>
      
      <div className="flex items-end justify-between">
        <div>
          <p className="text-2xl font-semibold">{value}</p>
          {trend && (
            <p className={cn(
              "text-xs flex items-center gap-1 mt-1", 
              trend.isPositive ? "text-success" : "text-danger"
            )}>
              {trend.isPositive ? "↑" : "↓"} {Math.abs(trend.value)}%
              <span className="text-muted-foreground">vs. último mes</span>
            </p>
          )}
        </div>
        
        <div className="h-10 w-10 opacity-20">
          {icon}
        </div>
      </div>
    </div>
  );
};

export default StatCard;
