
import React, { useState } from 'react';
import { Bot, ChartLine, Clock, User } from 'lucide-react';
import SearchInput from '../components/SearchInput';
import StatCard from '../components/StatCard';
import BotCard from '../components/BotCard';
import FilterBar from '../components/FilterBar';
import PerformanceChart from '../components/PerformanceChart';
import { bots, dashboardStats, performanceData, filterOptions } from '../lib/mockData';
import BestHoursExplanation from '../components/BestHoursExplanation';

const Index = () => {
  const [filteredBots, setFilteredBots] = useState(bots);
  const [searchTerm, setSearchTerm] = useState('');
  const [currentStrategy, setCurrentStrategy] = useState('');
  const [currentAsset, setCurrentAsset] = useState('');
  const [sortBy, setSortBy] = useState('performance');
  const [showRanking, setShowRanking] = useState(true);

  const handleSearch = (e: React.ChangeEvent<HTMLInputElement>) => {
    const term = e.target.value;
    setSearchTerm(term);
    
    filterBots(term, currentStrategy, currentAsset, sortBy);
  };

  const handleStrategyChange = (strategy: string) => {
    setCurrentStrategy(strategy);
    filterBots(searchTerm, strategy, currentAsset, sortBy);
  };

  const handleAssetChange = (asset: string) => {
    setCurrentAsset(asset);
    filterBots(searchTerm, currentStrategy, asset, sortBy);
  };

  const handleSortChange = (sort: string) => {
    setSortBy(sort);
    filterBots(searchTerm, currentStrategy, currentAsset, sort);
  };

  const filterBots = (term: string, strategy: string, asset: string, sort: string) => {
    let result = bots.filter(bot => {
      return (
        (term === '' || bot.name.toLowerCase().includes(term.toLowerCase()) || 
         bot.description.toLowerCase().includes(term.toLowerCase())) &&
        (strategy === '' || bot.strategy === strategy) &&
        (asset === '' || bot.tradedAssets.includes(asset))
      );
    });
    
    // Sort the results
    switch (sort) {
      case 'performance':
        result = result.sort((a, b) => b.accuracy - a.accuracy);
        break;
      case 'newest':
        result = result.sort((a, b) => 
          new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime()
        );
        break;
      case 'operations':
        result = result.sort((a, b) => b.operations - a.operations);
        break;
      default:
        break;
    }
    
    // Update rankings based on accuracy after filtering
    if (showRanking) {
      result = [...result].map((bot, index) => ({
        ...bot,
        ranking: index + 1
      }));
    }
    
    setFilteredBots(result);
  };

  return (
    <div className="min-h-screen bg-background animate-fade-in">
      {/* Header Section */}
      <section className="px-6 pt-6 pb-4">
        <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
          <div>
            <h1 className="text-2xl font-bold">Dashboard de Bots de Trading</h1>
            <p className="text-muted-foreground">Gerencie e analise bots de trading</p>
          </div>
          <SearchInput onChange={handleSearch} />
        </div>
      </section>
      
      {/* Stats Cards Section */}
      <section className="px-6 py-4">
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
          <StatCard 
            title="Total de Bots"
            value={dashboardStats.totalBots}
            icon={<Bot size={24} />}
            trend={{ value: 8.3, isPositive: true }}
          />
          <StatCard 
            title="Operações"
            value={dashboardStats.totalOperations}
            icon={<Clock size={24} />}
            trend={{ value: 12.5, isPositive: true }}
          />
          <StatCard 
            title="Assertividade Média"
            value={`${dashboardStats.averageAccuracy}%`}
            icon={<ChartLine size={24} />}
            trend={{ value: 3.2, isPositive: true }}
          />
          <StatCard 
            title="Usuários Ativos"
            value={dashboardStats.activeUsers}
            icon={<User size={24} />}
            trend={{ value: 5.1, isPositive: true }}
          />
        </div>
      </section>
      
      {/* Charts Section */}
      <section className="px-6 py-4">
        <h2 className="text-xl font-semibold mb-4">Analytics</h2>
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-6">
          <PerformanceChart 
            data={performanceData.profitLoss} 
            isPositive={true}
            title="Performance (P&L)"
            yAxisLabel="Valor ($)"
          />
          <PerformanceChart 
            data={performanceData.accuracy} 
            isPositive={true}
            title="Assertividade"
            yAxisLabel="%"
          />
          <PerformanceChart 
            data={performanceData.volatility} 
            isPositive={false}
            title="Volatilidade"
            yAxisLabel="Índice"
          />
        </div>
      </section>
      
      {/* Best Hours Explanation */}
      <section className="px-6 py-4">
        <BestHoursExplanation />
      </section>
      
      {/* Bots Library Section */}
      <section className="px-6 py-4">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-xl font-semibold">Ranking de Bots</h2>
          <div className="flex items-center gap-2">
            <label htmlFor="show-ranking" className="text-sm">
              Mostrar Ranking
            </label>
            <input 
              type="checkbox" 
              id="show-ranking" 
              checked={showRanking} 
              onChange={() => setShowRanking(!showRanking)} 
              className="rounded border-gray-300 text-primary focus:ring-primary"
            />
          </div>
        </div>
        
        <FilterBar 
          strategies={filterOptions.strategies}
          assets={filterOptions.assets}
          onStrategyChange={handleStrategyChange}
          onAssetChange={handleAssetChange}
          onSortChange={handleSortChange}
        />
        
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-6">
          {filteredBots.length > 0 ? (
            filteredBots.map(bot => (
              <BotCard 
                key={bot.id}
                id={bot.id}
                name={bot.name}
                description={bot.description}
                strategy={bot.strategy}
                accuracy={bot.accuracy}
                operations={bot.operations}
                imageUrl={bot.imageUrl}
                ranking={showRanking ? bot.ranking : undefined}
                isFavorite={bot.isFavorite}
              />
            ))
          ) : (
            <div className="col-span-full py-12 text-center text-muted-foreground">
              <p>Nenhum bot encontrado com os filtros atuais.</p>
              <p className="mt-2">Tente ajustar os filtros ou pesquisar por outros termos.</p>
            </div>
          )}
        </div>
      </section>
    </div>
  );
};

export default Index;
