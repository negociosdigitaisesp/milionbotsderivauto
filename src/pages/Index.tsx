
import React, { useState, useMemo } from 'react';
import { Bot } from 'lucide-react';
import { cn } from '@/lib/utils';
import { useBots } from '@/hooks/useBots';
import BotCard from '@/components/BotCard';
import SearchInput from '@/components/SearchInput';
import FilterBar, { FilterOption } from '@/components/FilterBar';

const Index = () => {
  const { data: bots = [], isLoading } = useBots();
  const [searchQuery, setSearchQuery] = useState('');
  const [filters, setFilters] = useState<FilterOption[]>([
    { id: 'all', label: 'Todos', active: true },
    { id: 'highSuccess', label: 'Alta Assertividade', active: false },
    { id: 'favorites', label: 'Favoritos', active: false },
  ]);

  const handleFilterChange = (updatedFilters: FilterOption[]) => {
    setFilters(updatedFilters);
  };

  const handleFavoriteToggle = (botId: string) => {
    // This would typically update the server/state
    console.log(`Toggle favorite for bot ${botId}`);
  };

  const filteredBots = useMemo(() => {
    if (!bots || !Array.isArray(bots)) return [];
    
    let result = [...bots];
    
    // Apply search filter
    if (searchQuery) {
      const query = searchQuery.toLowerCase();
      result = result.filter(bot => 
        bot.name.toLowerCase().includes(query) || 
        bot.description.toLowerCase().includes(query)
      );
    }
    
    // Apply category filters
    const activeFilters = filters.filter(f => f.active).map(f => f.id);
    
    if (activeFilters.includes('highSuccess')) {
      result = result.filter(bot => bot.accuracy >= 70);
    }
    
    if (activeFilters.includes('favorites')) {
      result = result.filter(bot => bot.isFavorite);
    }
    
    return result;
  }, [bots, searchQuery, filters]);

  const topBots = useMemo(() => {
    if (!bots || !Array.isArray(bots)) return [];
    return [...bots]
      .sort((a, b) => b.accuracy - a.accuracy)
      .slice(0, 3);
  }, [bots]);

  if (isLoading) {
    return (
      <div className="container mx-auto p-6">
        <div className="mb-6 flex justify-between items-center">
          <div className="h-8 w-48 bg-muted rounded animate-pulse"></div>
          <div className="h-10 w-64 bg-muted rounded animate-pulse"></div>
        </div>
        <div className="mb-8">
          <div className="h-7 w-40 bg-muted rounded animate-pulse mb-4"></div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {[1, 2, 3].map((i) => (
              <div key={i} className="h-64 bg-muted rounded animate-pulse"></div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="container mx-auto p-6">
      <div className="mb-6 flex flex-col sm:flex-row sm:justify-between sm:items-center gap-4">
        <h1 className="text-3xl font-bold">Bots de Trading</h1>
        <div className="flex gap-2">
          <SearchInput value={searchQuery} onChange={setSearchQuery} />
          <FilterBar filters={filters} onFilterChange={handleFilterChange} />
        </div>
      </div>

      {/* Ranking section */}
      <div className="mb-8">
        <h2 className="text-2xl font-semibold mb-4">Ranking de Bots</h2>
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {topBots && topBots.length > 0 ? (
            topBots.map((bot, index) => (
              <div key={bot.id} className="relative">
                <div 
                  className={cn(
                    "absolute -top-3 -left-3 w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold",
                    index === 0 ? "bg-yellow-400 text-yellow-900" : 
                    index === 1 ? "bg-gray-300 text-gray-700" : 
                    "bg-amber-700 text-amber-100"
                  )}
                >
                  {index + 1}
                </div>
                <BotCard 
                  bot={bot} 
                  onFavoriteToggle={handleFavoriteToggle}
                />
              </div>
            ))
          ) : (
            <div className="col-span-3 text-center py-4">
              <p className="text-muted-foreground">Nenhum bot disponível para ranking</p>
            </div>
          )}
        </div>
      </div>

      <div className="mb-8">
        <h2 className="text-2xl font-semibold mb-4">Todos os Bots</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredBots && filteredBots.length > 0 ? (
            filteredBots.map(bot => (
              <BotCard 
                key={bot.id} 
                bot={bot} 
                onFavoriteToggle={handleFavoriteToggle}
              />
            ))
          ) : (
            <div className="col-span-3 text-center py-12 bg-muted/30 rounded-lg">
              <Bot className="mx-auto h-12 w-12 text-muted-foreground mb-4" />
              <h2 className="text-xl font-medium text-foreground mb-2">Nenhum bot encontrado</h2>
              <p className="text-muted-foreground">Tente ajustar seus filtros ou busca para encontrar o que procura.</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default Index;
