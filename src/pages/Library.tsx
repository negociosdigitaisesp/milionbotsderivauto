import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { Bot, ChartLine, Clock, Filter, Search, Sliders, Star, LayoutGrid, LayoutList, Info, ArrowUpDown, Award, Gauge, TrendingUp, BarChart3, X, User, AlertTriangle } from 'lucide-react';
import SearchInput from '../components/SearchInput';
import BotCard from '../components/BotCard';
import FilterBar from '../components/FilterBar';
import { bots, filterOptions } from '../lib/mockData';
import { cn } from '../lib/utils';

// Constants for assertiveness levels
const ASSERTIVENESS_LEVELS = {
  HIGH: { 
    min: 60, 
    label: 'Alta', 
    color: 'emerald',
    description: 'Bots con alta tasa de acierto en sus operaciones'
  },
  MEDIUM: { 
    min: 45, 
    max: 60, 
    label: 'Media', 
    color: 'blue',
    description: 'Bots con tasa de acierto moderada'
  },
  LOW: { 
    max: 45, 
    label: 'Baja', 
    color: 'rose',
    description: 'Bots que necesitan optimización'
  }
};

const Library = () => {
  const [filteredBots, setFilteredBots] = useState(bots);
  const [searchTerm, setSearchTerm] = useState('');
  const [currentStrategy, setCurrentStrategy] = useState('');
  const [currentAsset, setCurrentAsset] = useState('');
  const [sortBy, setSortBy] = useState('performance');
  const [showFavoritesOnly, setShowFavoritesOnly] = useState(false);
  const [isFilterOpen, setIsFilterOpen] = useState(false);
  const [activeTab, setActiveTab] = useState<'all' | 'popular' | 'newest'>('all');

  useEffect(() => {
    filterBots(searchTerm, currentStrategy, currentAsset, sortBy);
  }, [showFavoritesOnly]);

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
      // Apply basic filters
      const matchesSearch = 
        term === '' || 
        bot.name.toLowerCase().includes(term.toLowerCase()) || 
        bot.description.toLowerCase().includes(term.toLowerCase());
      
      const matchesStrategy = strategy === '' || bot.strategy === strategy;
      const matchesAsset = asset === '' || bot.tradedAssets.includes(asset);
      const matchesFavorites = !showFavoritesOnly || bot.isFavorite;
      
      return matchesSearch && matchesStrategy && matchesAsset && matchesFavorites;
    });
    
    // Apply tab filtering
    if (activeTab === 'popular') {
      result = result.sort((a, b) => b.operations - a.operations).slice(0, 8);
    } else if (activeTab === 'newest') {
      result = result.sort((a, b) => 
        new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime()
      ).slice(0, 8);
    }
    
    // Apply sorting
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
    result = [...result].map((bot, index) => ({
      ...bot,
      ranking: index + 1
    }));
    
    setFilteredBots(result);
  };

  // Stats based on the filtered bots
  const libraryStats = {
    totalBots: filteredBots.length,
    averageAccuracy: Math.round(filteredBots.reduce((sum, bot) => sum + bot.accuracy, 0) / filteredBots.length || 0),
    highestAccuracy: Math.max(...filteredBots.map(bot => bot.accuracy), 0),
    totalOperations: filteredBots.reduce((sum, bot) => sum + bot.operations, 0)
  };

  const accuracyDistribution = {
    high: filteredBots.filter(bot => bot.accuracy >= ASSERTIVENESS_LEVELS.HIGH.min).length,
    medium: filteredBots.filter(bot => bot.accuracy >= ASSERTIVENESS_LEVELS.MEDIUM.min && bot.accuracy < ASSERTIVENESS_LEVELS.MEDIUM.max).length,
    low: filteredBots.filter(bot => bot.accuracy < ASSERTIVENESS_LEVELS.LOW.max).length
  };

  return (
    <div className="container max-w-7xl mx-auto py-8 px-4 animate-in fade-in duration-500">
      {/* Hero Section - Enhanced with more professional design elements */}
      <section className="mb-12">
        <div className="relative overflow-hidden rounded-2xl shadow-xl">
          <div className="absolute inset-0 bg-gradient-to-br from-primary/25 via-primary/15 to-background"></div>
          
          {/* Decorative elements */}
          <div className="absolute inset-0 w-full h-full overflow-hidden opacity-70">
            <div className="absolute w-[600px] h-[600px] rounded-full bg-gradient-to-br from-primary/20 to-transparent -top-[350px] -right-[100px] blur-md"></div>
            <div className="absolute w-[500px] h-[500px] rounded-full bg-gradient-to-br from-primary/15 to-transparent top-[50%] -left-[200px] blur-md"></div>
            <div className="absolute top-0 right-0 w-full h-full bg-grid-white/[0.05] [mask-image:linear-gradient(to_bottom,transparent,black)]"></div>
            <svg className="absolute right-0 bottom-0 text-primary/10 w-64 h-64" viewBox="0 0 200 200" xmlns="http://www.w3.org/2000/svg">
              <path fill="currentColor" d="M47.1,-57.8C58.6,-47.6,63.6,-30.8,66.8,-13.5C70,3.8,71.5,21.6,64.6,35.5C57.6,49.4,42.2,59.5,25.7,65.1C9.1,70.7,-8.5,72,-23.9,66.3C-39.3,60.7,-52.5,48.1,-63.1,32.5C-73.7,16.9,-81.7,-1.7,-77.9,-17.7C-74.1,-33.7,-58.5,-47.1,-42.2,-56.5C-25.9,-65.9,-8.9,-71.4,6.8,-79.5C22.6,-87.6,39.4,-98.5,47.1,-57.8Z" transform="translate(120 130)" />
            </svg>
          </div>
          
          <div className="relative z-10 py-12 px-8 flex flex-col md:flex-row items-start gap-10">
            <div className="flex-1 max-w-3xl">
              <div className="inline-block mb-3 bg-primary/10 backdrop-blur-sm rounded-full px-4 py-1.5 border border-primary/20">
                <span className="text-primary font-medium text-sm flex items-center gap-2">
                  <Bot size={14} className="text-primary" />
                  Explora nuestro catálogo completo
                </span>
              </div>
              <h1 className="text-4xl md:text-5xl font-bold mb-4 text-foreground leading-tight">
                Biblioteca de <span className="text-primary relative z-10">Bots 
                  <svg className="absolute -bottom-2 -z-10 left-0 w-full opacity-20" viewBox="0 0 200 20" xmlns="http://www.w3.org/2000/svg">
                    <path fill="currentColor" d="M0,0 Q50,40 100,0 Q150,40 200,0 Z" />
                  </svg>
                </span>
              </h1>
              <p className="text-xl mb-6 text-muted-foreground leading-relaxed max-w-2xl">
                Explora nuestra colección completa de bots de trading. Encuentra el bot perfecto para tu estrategia
                y comienza a operar con más eficiencia.
              </p>
              <div className="w-full max-w-md">
                <SearchInput onChange={handleSearch} placeholder="Busca bots por nombre, estrategia o descripción..." />
              </div>
              <div className="mt-8 hidden md:flex items-center gap-4">
                <span className="text-sm text-muted-foreground">Filtros rápidos:</span>
                <button 
                  onClick={() => handleStrategyChange("Martingale")}
                  className="inline-flex items-center gap-1 px-3 py-1 bg-card hover:bg-primary/5 text-xs rounded-full border border-border"
                >
                  <TrendingUp size={12} /> Martingale
                </button>
                <button 
                  onClick={() => handleStrategyChange("Seguidor de Tendência")}
                  className="inline-flex items-center gap-1 px-3 py-1 bg-card hover:bg-primary/5 text-xs rounded-full border border-border"
                >
                  <TrendingUp size={12} /> Seguidor de Tendencia
                </button>
                <button 
                  onClick={() => handleSortChange("newest")}
                  className="inline-flex items-center gap-1 px-3 py-1 bg-card hover:bg-primary/5 text-xs rounded-full border border-border"
                >
                  <Clock size={12} /> Más recientes
                </button>
              </div>
            </div>
            
            <div className="grid grid-cols-2 gap-4 bg-card/80 backdrop-blur-sm rounded-lg p-6 border border-border/50 shadow-sm min-w-[300px]">
              <div className="flex flex-col">
                <span className="text-xs text-muted-foreground">Total de Bots</span>
                <div className="flex items-baseline gap-1">
                  <span className="text-3xl font-bold">{libraryStats.totalBots}</span>
                  <Bot size={16} className="text-primary" />
                </div>
              </div>
              
              <div className="flex flex-col">
                <span className="text-xs text-muted-foreground">Asertividad Media</span>
                <div className="flex items-baseline gap-1">
                  <span className="text-3xl font-bold">{libraryStats.averageAccuracy}%</span>
                  <ChartLine size={16} className="text-primary" />
                </div>
              </div>
              
              <div className="flex flex-col">
                <span className="text-xs text-muted-foreground">Mejor Asertividad</span>
                <div className="flex items-baseline gap-1">
                  <span className="text-3xl font-bold">{libraryStats.highestAccuracy}%</span>
                  <Award size={16} className="text-emerald-500" />
                </div>
              </div>
              
              <div className="flex flex-col">
                <span className="text-xs text-muted-foreground">Total de Operaciones</span>
                <div className="flex items-baseline gap-1">
                  <span className="text-3xl font-bold">{libraryStats.totalOperations.toLocaleString()}</span>
                  <Clock size={16} className="text-primary" />
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>
      
      {/* Investment Risk Warning Banner */}
      <section className="mb-8">
        <div className="bg-red-500/10 border border-red-500/30 rounded-lg p-4">
          <div className="flex items-center gap-3">
            <AlertTriangle className="text-red-500 flex-shrink-0" size={20} />
            <div className="text-sm">
              <p className="font-medium text-red-700 dark:text-red-400 mb-1">
                 AVISO SOBRE RIESGOS DE INVERSIÓN
               </p>
               <p className="text-red-600 dark:text-red-300">
                  Los retornos pasados no garantizan retornos futuros. La negociación de productos financieros complejos, como opciones y derivados, implica un elevado nivel de riesgo y puede resultar en la pérdida de todo el capital invertido. Asegúrese de comprender plenamente los riesgos antes de invertir y nunca arriesgue más dinero del que pueda permitirse perder.
                </p>
            </div>
          </div>
        </div>
      </section>
      
      {/* Filter and Display Controls - Enhanced with more professional and intuitive UI */}
      <section className="mb-8">
        <div className="bg-card/50 rounded-xl border border-border shadow-sm p-4">
          <div className="flex flex-col lg:flex-row justify-between items-start lg:items-center gap-4">
            <div className="flex flex-wrap items-center gap-2 md:gap-3">
              <span className="text-sm font-medium text-muted-foreground mr-2">Ver:</span>
              <button 
                onClick={() => setActiveTab('all')} 
                className={cn(
                  "rounded-md px-3 py-1.5 text-sm font-medium transition-all",
                  activeTab === 'all' 
                    ? "bg-primary text-primary-foreground shadow-sm" 
                    : "bg-card border border-border hover:bg-muted hover:border-primary/30"
                )}
              >
                <span className="flex items-center gap-1.5">
                  <Bot size={15} />
                  Todos los Bots
                </span>
              </button>
              
              <button 
                onClick={() => setActiveTab('popular')} 
                className={cn(
                  "rounded-md px-3 py-1.5 text-sm font-medium transition-all",
                  activeTab === 'popular' 
                    ? "bg-primary text-primary-foreground shadow-sm" 
                    : "bg-card border border-border hover:bg-muted hover:border-primary/30"
                )}
              >
                <span className="flex items-center gap-1.5">
                  <TrendingUp size={15} />
                  Más Populares
                </span>
              </button>
              
              <button 
                onClick={() => setActiveTab('newest')} 
                className={cn(
                  "rounded-md px-3 py-1.5 text-sm font-medium transition-all",
                  activeTab === 'newest' 
                    ? "bg-primary text-primary-foreground shadow-sm" 
                    : "bg-card border border-border hover:bg-muted hover:border-primary/30"
                )}
              >
                <span className="flex items-center gap-1.5">
                  <Clock size={15} />
                  Nuevos Bots
                </span>
              </button>
            </div>
            
            <div className="flex items-center gap-3 w-full lg:w-auto justify-between lg:justify-end">
              <div className="flex items-center gap-2">
                <button 
                  onClick={() => setShowFavoritesOnly(!showFavoritesOnly)}
                  className={cn(
                    "flex items-center gap-1.5 px-3 py-1.5 text-sm font-medium rounded-md border transition-all",
                    showFavoritesOnly 
                      ? "bg-yellow-500/10 text-yellow-600 border-yellow-200" 
                      : "bg-card border-border hover:bg-muted"
                  )}
                >
                  <Star size={16} className={showFavoritesOnly ? "fill-yellow-500 text-yellow-500" : ""} />
                  <span className="hidden sm:inline">Favoritos</span>
                </button>
                
                <button 
                  onClick={() => setIsFilterOpen(!isFilterOpen)}
                  className={cn(
                    "flex items-center gap-1.5 px-3 py-1.5 text-sm font-medium rounded-md border transition-all",
                    isFilterOpen
                      ? "bg-primary/10 text-primary border-primary/20"
                      : "bg-card border-border hover:bg-muted"
                  )}
                >
                  <Filter size={16} />
                  <span className="hidden sm:inline">Filtros</span>
                  {(currentStrategy || currentAsset || sortBy !== 'performance') && (
                    <span className="inline-flex items-center justify-center w-5 h-5 text-xs bg-primary text-white rounded-full">
                      {(currentStrategy ? 1 : 0) + (currentAsset ? 1 : 0) + (sortBy !== 'performance' ? 1 : 0)}
                    </span>
                  )}
                </button>
              </div>
            </div>
          </div>
          
          {/* Expanded Filter Bar - Enhanced with animation and better organization */}
          {isFilterOpen && (
            <div className="mt-4 p-4 bg-background rounded-lg border border-border animate-in fade-in slide-in-from-top-4 duration-300">
              <div className="flex flex-col lg:flex-row justify-between gap-6">
                <div className="space-y-4 flex-1">
                  <div>
                    <h3 className="text-sm font-medium mb-3 flex items-center gap-1 border-b pb-2">
                      <Sliders size={14} className="text-primary" />
                      Filtrar por Estrategia
                    </h3>
                    <div className="flex flex-wrap gap-2">
                      <button 
                        onClick={() => handleStrategyChange('')}
                        className={cn(
                          "px-3 py-1.5 text-xs rounded-full transition-all",
                          currentStrategy === '' 
                            ? "bg-primary text-white" 
                            : "bg-background border border-border hover:bg-muted hover:border-primary/30"
                        )}
                      >
                        Todas
                      </button>
                      {filterOptions.strategies.map(strategy => (
                        <button 
                          key={strategy.value}
                          onClick={() => handleStrategyChange(strategy.value)}
                          className={cn(
                            "px-3 py-1.5 text-xs rounded-full transition-all",
                            currentStrategy === strategy.value 
                              ? "bg-primary text-white" 
                              : "bg-background border border-border hover:bg-muted hover:border-primary/30"
                          )}
                        >
                          {strategy.label}
                        </button>
                      ))}
                    </div>
                  </div>
                  
                  <div>
                    <h3 className="text-sm font-medium mb-2 flex items-center gap-1">
                      <TrendingUp size={14} className="text-primary" />
                      Activos Operados
                    </h3>
                    <div className="flex flex-wrap gap-2">
                      <button 
                        onClick={() => handleAssetChange('')}
                        className={cn(
                          "px-3 py-1 text-xs rounded-full transition-colors",
                          currentAsset === '' 
                            ? "bg-primary text-white" 
                            : "bg-muted hover:bg-muted/80"
                        )}
                      >
                        Todos
                      </button>
                      {filterOptions.assets.map(asset => (
                        <button 
                          key={asset.value}
                          onClick={() => handleAssetChange(asset.value)}
                          className={cn(
                            "px-3 py-1 text-xs rounded-full transition-colors",
                            currentAsset === asset.value 
                              ? "bg-primary text-white" 
                              : "bg-muted hover:bg-muted/80"
                          )}
                        >
                          {asset.label}
                        </button>
                      ))}
                    </div>
                  </div>
                </div>
                
                <div className="flex flex-col">
                  <h3 className="text-sm font-medium mb-2 flex items-center gap-1">
                    <ArrowUpDown size={14} className="text-primary" />
                    Ordenar Por
                  </h3>
                  <div className="flex flex-wrap gap-2">
                    <button 
                      onClick={() => handleSortChange('performance')}
                      className={cn(
                        "px-3 py-1 text-xs rounded-full transition-colors",
                        sortBy === 'performance' 
                          ? "bg-primary text-white" 
                          : "bg-muted hover:bg-muted/80"
                      )}
                    >
                      Asertividad
                    </button>
                    <button 
                      onClick={() => handleSortChange('newest')}
                      className={cn(
                        "px-3 py-1 text-xs rounded-full transition-colors",
                        sortBy === 'newest' 
                          ? "bg-primary text-white" 
                          : "bg-muted hover:bg-muted/80"
                      )}
                    >
                      Más Recientes
                    </button>
                    <button 
                      onClick={() => handleSortChange('operations')}
                      className={cn(
                        "px-3 py-1 text-xs rounded-full transition-colors",
                        sortBy === 'operations' 
                          ? "bg-primary text-white" 
                          : "bg-muted hover:bg-muted/80"
                      )}
                    >
                      Más Operaciones
                    </button>
                  </div>
                  
                  {/* Assertiveness distribution - Redesigned with better visuals */}
                  <div className="rounded-xl border shadow-sm bg-card overflow-hidden mt-4">
                    <div className="p-5 border-b bg-muted/40 flex items-center gap-2">
                      <Gauge className="text-primary" size={18} />
                      <h2 className="text-lg font-semibold">Distribución de Asertividad</h2>
                    </div>
                    
                    <div className="p-6">
                      <div className="space-y-5">
                        {/* High assertiveness */}
                        <div className="space-y-2">
                          <div className="flex justify-between items-center">
                            <div className="flex items-center gap-2">
                              <div className={`w-3 h-3 rounded-full bg-emerald-500`}></div>
                              <h3 className="font-medium text-sm">Alta Asertividad ({ASSERTIVENESS_LEVELS.HIGH.min}%+)</h3>
                            </div>
                            <div className="font-medium text-sm">{accuracyDistribution.high} bots</div>
                          </div>
                          
                          <div className="relative w-full h-4 bg-muted rounded-full overflow-hidden">
                            <div 
                              className="absolute top-0 left-0 h-full bg-emerald-500 rounded-full transition-all" 
                              style={{ 
                                width: `${(accuracyDistribution.high / filteredBots.length) * 100}%`,
                              }}
                            ></div>
                          </div>
                          
                          <p className="text-xs text-muted-foreground">
                            {Math.round((accuracyDistribution.high / filteredBots.length) * 100)}% del total • {ASSERTIVENESS_LEVELS.HIGH.description}
                          </p>
                        </div>
                        
                        {/* Medium assertiveness */}
                        <div className="space-y-2">
                          <div className="flex justify-between items-center">
                            <div className="flex items-center gap-2">
                              <div className={`w-3 h-3 rounded-full bg-blue-500`}></div>
                              <h3 className="font-medium text-sm">Media Asertividad ({ASSERTIVENESS_LEVELS.MEDIUM.min}-{ASSERTIVENESS_LEVELS.MEDIUM.max}%)</h3>
                            </div>
                            <div className="font-medium text-sm">{accuracyDistribution.medium} bots</div>
                          </div>
                          
                          <div className="relative w-full h-4 bg-muted rounded-full overflow-hidden">
                            <div 
                              className="absolute top-0 left-0 h-full bg-blue-500 rounded-full transition-all" 
                              style={{ 
                                width: `${(accuracyDistribution.medium / filteredBots.length) * 100}%`,
                              }}
                            ></div>
                          </div>
                          
                          <p className="text-xs text-muted-foreground">
                            {Math.round((accuracyDistribution.medium / filteredBots.length) * 100)}% del total • {ASSERTIVENESS_LEVELS.MEDIUM.description}
                          </p>
                        </div>
                        
                        {/* Low assertiveness */}
                        <div className="space-y-2">
                          <div className="flex justify-between items-center">
                            <div className="flex items-center gap-2">
                              <div className={`w-3 h-3 rounded-full bg-rose-500`}></div>
                              <h3 className="font-medium text-sm">Baja Asertividad (Debajo de {ASSERTIVENESS_LEVELS.LOW.max}%)</h3>
                            </div>
                            <div className="font-medium text-sm">{accuracyDistribution.low} bots</div>
                          </div>
                          
                          <div className="relative w-full h-4 bg-muted rounded-full overflow-hidden">
                            <div 
                              className="absolute top-0 left-0 h-full bg-rose-500 rounded-full transition-all" 
                              style={{ 
                                width: `${(accuracyDistribution.low / filteredBots.length) * 100}%`,
                              }}
                            ></div>
                          </div>
                          
                          <p className="text-xs text-muted-foreground">
                            {Math.round((accuracyDistribution.low / filteredBots.length) * 100)}% del total • {ASSERTIVENESS_LEVELS.LOW.description}
                          </p>
                        </div>
                        
                        {/* Summary card */}
                        <div className="mt-5 p-4 bg-primary/5 rounded-lg border border-primary/20 flex items-start gap-3">
                          <Info size={18} className="text-primary mt-0.5" />
                          <div>
                            <h4 className="text-sm font-medium mb-1">Análisis de Asertividad</h4>
                            <p className="text-sm text-muted-foreground">
                              La mayoría de los bots ({Math.max(accuracyDistribution.high, accuracyDistribution.medium, accuracyDistribution.low)} de {filteredBots.length}) 
                              tienen asertividad <span className="font-medium text-foreground">
                                {accuracyDistribution.high >= accuracyDistribution.medium && accuracyDistribution.high >= accuracyDistribution.low ? 'alta' : 
                                 accuracyDistribution.medium >= accuracyDistribution.high && accuracyDistribution.medium >= accuracyDistribution.low ? 'media' : 'baja'}
                              </span>.
                              {accuracyDistribution.high > 0 && 
                                ` ${accuracyDistribution.high} ${accuracyDistribution.high === 1 ? 'bot tiene' : 'bots tienen'} asertividad por encima de ${ASSERTIVENESS_LEVELS.HIGH.min}%.`
                              }
                            </p>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      </section>
      
      {/* Bots Display - List view only */}
      <section className="mb-6">
        {filteredBots.length > 0 ? (
          <>
            {/* Results count and current filter info */}
            <div className="flex justify-between items-center mb-4 px-2">
              <div className="text-sm text-muted-foreground">
                Mostrando <span className="font-medium text-foreground">{filteredBots.length}</span> {filteredBots.length === 1 ? 'bot' : 'bots'}
                {currentStrategy && <span> con estrategia <span className="font-medium text-primary">{currentStrategy}</span></span>}
                {currentAsset && <span> para el activo <span className="font-medium text-primary">{currentAsset}</span></span>}
              </div>
              
              {(currentStrategy || currentAsset) && (
                <button 
                  onClick={() => {
                    setCurrentStrategy('');
                    setCurrentAsset('');
                    filterBots('', '', '', sortBy);
                  }}
                  className="text-xs text-primary hover:text-primary/80 flex items-center gap-1"
                >
                  Limpiar filtros <X size={12} />
                </button>
              )}
            </div>
          
            <div className="space-y-4">
              {filteredBots.map(bot => (
                <Link 
                  to={`/bot/${bot.id}`}
                  key={bot.id} 
                  className="group flex flex-col md:flex-row gap-4 p-5 bg-card rounded-xl border border-border hover:bg-card/70 hover:border-primary/20 transition-all duration-300 relative"
                >
                  {/* Ranking badge */}
                  {activeTab === 'all' && bot.ranking && (
                    <div className="absolute top-0 left-0 z-10 bg-gradient-to-r from-emerald-600 to-emerald-500 text-white px-3 py-1 rounded-br-lg font-semibold shadow-md">
                      #{bot.ranking}
                    </div>
                  )}
                  
                  {/* Bot Image/Logo */}
                  <div className="md:w-48 h-28 md:h-auto bg-gradient-to-br from-slate-900 via-slate-700 to-zinc-600 rounded-lg flex items-center justify-center overflow-hidden relative group-hover:shadow-md transition-all">
                    <div className="absolute inset-0 opacity-30">
                      <div className="absolute w-32 h-32 rounded-full bg-primary/30 blur-2xl -top-10 -right-10"></div>
                      <div className="absolute w-24 h-24 rounded-full bg-primary/20 blur-xl bottom-5 -left-10"></div>
                    </div>
                    <h3 className="text-xl font-bold text-white relative z-10 px-4 text-center">
                      {bot.name}
                      <div className="mt-1 text-xs text-blue-100/80 font-medium uppercase tracking-wider">{bot.strategy}</div>
                    </h3>
                  </div>
                  
                  {/* Bot Info */}
                  <div className="flex-1 flex flex-col justify-between">
                    <div className="flex flex-col md:flex-row justify-between items-start gap-3">
                      <div>
                        <h3 className="font-semibold text-lg group-hover:text-primary transition-colors">{bot.name}</h3>
                        <p className="text-sm text-muted-foreground mb-3 line-clamp-2">{bot.description}</p>
                      </div>
                      
                      <div className="flex items-center gap-3">
                        <span className={cn(
                          "text-xs px-3 py-1.5 rounded-full border shadow-sm flex items-center gap-1.5", 
                          bot.accuracy >= 60 ? "bg-emerald-50 text-emerald-700 border-emerald-200" : 
                          bot.accuracy >= 40 ? "bg-blue-50 text-blue-700 border-blue-200" : 
                          "bg-rose-50 text-rose-700 border-rose-200"
                        )}>
                          <span className={cn(
                            "w-2 h-2 rounded-full",
                            bot.accuracy >= 60 ? "bg-emerald-500" : 
                            bot.accuracy >= 40 ? "bg-blue-500" : 
                            "bg-rose-500"
                          )}></span>
                          <span>
                            <span className="font-semibold">{bot.accuracy}%</span> asertivo
                          </span>
                        </span>
                        
                        <button 
                          onClick={(e) => {
                            e.preventDefault();
                            e.stopPropagation();
                            // Here you would toggle the favorite state
                          }}
                          className="p-2 rounded-full hover:bg-primary/5 transition-colors"
                          aria-label={bot.isFavorite ? "Eliminar de favoritos" : "Añadir a favoritos"}
                        >
                          <Star 
                            size={18} 
                            className={bot.isFavorite ? "fill-yellow-400 text-yellow-400" : "text-muted-foreground"} 
                          />
                        </button>
                      </div>
                    </div>
                    
                    <div className="flex flex-wrap items-center gap-3 mt-2">
                      <div className="text-xs py-1 px-2.5 bg-primary/10 text-primary rounded-full flex items-center gap-1">
                        <Gauge size={12} />
                        {bot.strategy}
                      </div>
                      
                      <div className="text-xs py-1 px-2.5 bg-card border border-border rounded-full flex items-center gap-1">
                        <Clock size={12} />
                        {bot.operations.toLocaleString()} operaciones
                      </div>
                      
                      <div className="text-xs py-1 px-2.5 bg-card border border-border rounded-full flex items-center gap-1">
                        <Info size={12} />
                        v{bot.version}
                      </div>
                      
                      {bot.tradedAssets.map((asset, i) => (
                        <div key={i} className="text-xs py-1 px-2.5 bg-card border border-border rounded-full">
                          {asset}
                        </div>
                      ))}
                      
                      <div className="text-xs py-1 px-2.5 bg-card border border-border rounded-full flex items-center gap-1 ml-auto">
                        <User size={12} />
                        {bot.author}
                      </div>
                    </div>
                  </div>
                </Link>
              ))}
            </div>
          </>
        ) : (
          <div className="py-16 text-center">
            <div className="bg-muted/50 mx-auto w-20 h-20 rounded-full flex items-center justify-center mb-4">
              <Bot size={40} className="text-muted-foreground" />
            </div>
            <h3 className="text-xl font-medium mb-2">Ningún bot encontrado</h3>
            <p className="text-muted-foreground max-w-md mx-auto mb-6">
              Ningún bot corresponde a los filtros actuales. Intenta ajustar los filtros o limpiar la búsqueda.
            </p>
            <button 
              onClick={() => {
                setSearchTerm('');
                setCurrentStrategy('');
                setCurrentAsset('');
                setShowFavoritesOnly(false);
                filterBots('', '', '', sortBy);
              }}
              className="px-4 py-2 bg-primary hover:bg-primary/90 text-white rounded-md text-sm font-medium transition-colors"
            >
              Limpiar Filtros
            </button>
          </div>
        )}
      </section>
      
      {/* Footer Section - Adding professional footer */}
      <section className="mt-16 border-t border-border pt-8 pb-12">
        <div className="flex flex-col md:flex-row justify-between items-center">
          <div className="flex items-center gap-3 mb-4 md:mb-0">
            <Bot size={24} className="text-primary" />
            <span className="text-lg font-semibold">Million Bots Library</span>
          </div>
          
          <div className="flex items-center gap-6">
            <div className="text-sm text-muted-foreground">
              Total de <span className="font-medium text-foreground">{bots.length}</span> bots disponibles
            </div>
            
            <div className="h-6 w-px bg-border mx-2"></div>
            
            <div className="flex items-center gap-4">
              <a href="#" className="text-sm text-muted-foreground hover:text-primary transition-colors">
                Documentación
              </a>
              <a href="#" className="text-sm text-muted-foreground hover:text-primary transition-colors">
                Soporte
              </a>
              <a href="#" className="text-sm text-muted-foreground hover:text-primary transition-colors">
                Términos de Uso
              </a>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
};

export default Library;