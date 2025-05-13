
import React from 'react';
import { Search } from 'lucide-react';

interface SearchInputProps {
  placeholder?: string;
  onChange?: (e: React.ChangeEvent<HTMLInputElement>) => void;
}

const SearchInput = ({ placeholder = "Search bots...", onChange }: SearchInputProps) => {
  return (
    <div className="relative w-full max-w-md">
      <div className="absolute inset-y-0 left-0 flex items-center pl-3">
        <Search size={18} className="text-muted-foreground" />
      </div>
      <input
        type="text"
        className="w-full py-2 pl-10 pr-4 bg-secondary rounded-lg border border-border/50 focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary transition-colors"
        placeholder={placeholder}
        onChange={onChange}
      />
    </div>
  );
};

export default SearchInput;
