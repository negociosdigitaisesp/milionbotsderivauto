
import React from 'react';
import { Filter } from 'lucide-react';

interface FilterOption {
  label: string;
  value: string;
}

interface FilterBarProps {
  strategies: FilterOption[];
  assets: FilterOption[];
  onStrategyChange: (strategy: string) => void;
  onAssetChange: (asset: string) => void;
  onSortChange: (sort: string) => void;
}

const FilterBar = ({ 
  strategies, 
  assets, 
  onStrategyChange, 
  onAssetChange, 
  onSortChange 
}: FilterBarProps) => {
  return (
    <div className="bg-secondary rounded-lg p-3 mb-6 flex flex-wrap gap-3 items-center">
      <div className="flex items-center gap-2 text-muted-foreground">
        <Filter size={16} />
        <span className="text-sm font-medium">Filtros:</span>
      </div>
      
      <div className="flex flex-wrap gap-3 items-center">
        <select 
          className="bg-background text-sm rounded-md border border-border/50 px-3 py-1.5 focus:outline-none focus:ring-1 focus:ring-primary"
          onChange={(e) => onStrategyChange(e.target.value)}
        >
          <option value="">Todas as estratégias</option>
          {strategies.map((strategy) => (
            <option key={strategy.value} value={strategy.value}>
              {strategy.label}
            </option>
          ))}
        </select>
        
        <select 
          className="bg-background text-sm rounded-md border border-border/50 px-3 py-1.5 focus:outline-none focus:ring-1 focus:ring-primary"
          onChange={(e) => onAssetChange(e.target.value)}
        >
          <option value="">Todos os ativos</option>
          {assets.map((asset) => (
            <option key={asset.value} value={asset.value}>
              {asset.label}
            </option>
          ))}
        </select>
      </div>
      
      <div className="ml-auto">
        <select 
          className="bg-background text-sm rounded-md border border-border/50 px-3 py-1.5 focus:outline-none focus:ring-1 focus:ring-primary"
          onChange={(e) => onSortChange(e.target.value)}
        >
          <option value="popularity">Mais populares</option>
          <option value="performance">Melhor performance</option>
          <option value="newest">Mais recentes</option>
        </select>
      </div>
    </div>
  );
};

export default FilterBar;
