
import React from 'react';
import { Filter } from 'lucide-react';

export interface FilterOption {
  id: string;
  label: string;
  active: boolean;
}

interface FilterBarProps {
  filters: FilterOption[];
  onFilterChange: (filters: FilterOption[]) => void;
}

const FilterBar = ({ filters = [], onFilterChange }: FilterBarProps) => {
  const handleFilterClick = (id: string) => {
    if (!filters || !Array.isArray(filters)) return;
    
    const updatedFilters = filters.map(filter => ({
      ...filter,
      active: filter.id === id ? !filter.active : filter.active
    }));
    onFilterChange(updatedFilters);
  };

  if (!filters || !Array.isArray(filters) || filters.length === 0) {
    return null;
  }

  return (
    <div className="flex flex-wrap gap-2">
      {filters.map(filter => (
        <button
          key={filter.id}
          onClick={() => handleFilterClick(filter.id)}
          className={`px-3 py-1 text-sm rounded-full transition-colors ${
            filter.active 
              ? 'bg-primary text-primary-foreground' 
              : 'bg-muted hover:bg-muted/80'
          }`}
        >
          {filter.label}
        </button>
      ))}
    </div>
  );
};

export default FilterBar;
