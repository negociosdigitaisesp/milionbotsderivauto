import React, { useState, useRef, useEffect } from 'react';
import { Bot, ChartLine, Clock, User, Zap, Search, Award, ArrowRight, AlertTriangle } from 'lucide-react';
import SearchInput from '../components/SearchInput';
import StatCard from '../components/StatCard';
import BotCard from '../components/BotCard';
import FilterBar from '../components/FilterBar';
import PerformanceChart from '../components/PerformanceChart';
import { bots, dashboardStats, performanceData, filterOptions } from '../lib/mockData';
import { atualizarRankingBots, verificarAtualizacoesPendentes } from '../services/botRankingService';

const BotFinderRadar = () => {
  const [isSearching, setIsSearching] = useState(false);
  const [foundBot, setFoundBot] = useState<typeof bots[0] | null>(null);
  const [currentBotIndex, setCurrentBotIndex] = useState(0);
  const [showInitial, setShowInitial] = useState(true);
  const containerRef = useRef<HTMLDivElement>(null);
  const buttonRef = useRef<HTMLButtonElement>(null);
  const radarRef = useRef<HTMLDivElement>(null);
  const [showParticles, setShowParticles] = useState(false);

  useEffect(() => {
    if (isSearching) {
      setShowParticles(true);
    } else {
      const timer = setTimeout(() => setShowParticles(false), 1000);
      return () => clearTimeout(timer);
    }
  }, [isSearching]);

  // Função para iniciar a busca do bot
  const startDetection = () => {
    console.log("Iniciando detecção...");
    setShowInitial(false);
    setIsSearching(true);
    setCurrentBotIndex(0);
    
    setTimeout(() => {
      // Usar bots ordenados por accuracy
      const botsToUse = [...bots].sort((a, b) => b.accuracy - a.accuracy);
      console.log("Bots disponíveis:", botsToUse.length);
      setFoundBot(botsToUse[0]);
      setIsSearching(false);
    }, 1500);
  };

  // Função para o botão Download - SIMPLIFICADA
  const handleDownloadClick = (event: React.MouseEvent) => {
    event.preventDefault();
    event.stopPropagation();
    
    console.log("=== BOTÃO DOWNLOAD CLICADO ===");
    console.log("Bot encontrado:", foundBot);
    
    if (!foundBot) {
      alert("Nenhum bot selecionado!");
      return;
    }
    
    console.log("Iniciando download do bot:", foundBot.name);
    alert(`Download iniciado para o bot: ${foundBot.name}`);
    
    // Simula navegação
    try {
      const targetUrl = `/bot/${foundBot.id}`;
      console.log("URL de destino:", targetUrl);
      window.location.href = targetUrl;
    } catch (error) {
      console.error("Erro na navegação:", error);
      alert("Erro ao tentar acessar a página do bot");
    }
  };

  // Função para buscar outro bot - SIMPLIFICADA
  const handleBuscarOtroClick = (event: React.MouseEvent) => {
    event.preventDefault();
    event.stopPropagation();
    
    console.log("=== BOTÃO BUSCAR OTRO CLICADO ===");
    console.log("Índice atual:", currentBotIndex);
    
    const botsToUse = [...bots].sort((a, b) => b.accuracy - a.accuracy);
    console.log("Bots disponíveis:", botsToUse.length);
    
    if (botsToUse.length === 0) {
      alert("Não há bots disponíveis!");
      return;
    }
    
    setIsSearching(true);
    setFoundBot(null);
    
    setTimeout(() => {
      const nextIndex = (currentBotIndex + 1) % Math.min(5, botsToUse.length);
      console.log("Próximo índice:", nextIndex);
      
      setCurrentBotIndex(nextIndex);
      setFoundBot(botsToUse[nextIndex]);
      setIsSearching(false);
      
      console.log("Novo bot selecionado:", botsToUse[nextIndex]?.name);
    }, 1200);
  };

  return (
    <div className="mb-8 bg-gradient-to-r from-card to-muted rounded-xl p-3 md:p-4 shadow-xl relative overflow-hidden max-w-full" ref={containerRef}>
      {/* Background grid pattern */}
      <div className="absolute inset-0 bg-grid-white/[0.05] bg-[size:20px_20px] pointer-events-none"></div>
      {showParticles && (
        <div className="absolute inset-0 pointer-events-none">
          {[...Array(20)].map((_, i) => (
            <div 
              key={i}
              className="absolute w-1 h-1 bg-primary rounded-full"
              style={{
                left: `${Math.random() * 100}%`,
                top: `${Math.random() * 100}%`,
                opacity: Math.random() * 0.5 + 0.3,
                boxShadow: '0 0 10px 2px rgba(174, 94, 56, 0.6)',
                animation: `float ${Math.random() * 3 + 2}s linear infinite`
              }}
            ></div>
          ))}
        </div>
      )}
      <div className="flex flex-col items-center justify-center gap-4 md:gap-6 relative z-10">
        <div className="text-center mb-0 md:mb-2">
          <h2 className="text-xl md:text-2xl font-bold text-foreground mb-1 md:mb-2 flex items-center justify-center">
            <Zap className="mr-2 text-primary" size={24} />
            Radar de Bots
          </h2>
          <p className="text-sm md:text-base text-muted-foreground max-w-xl mx-auto">Detecte automáticamente el bot con mejor desempeño en el catálogo</p>
        </div>
        <div className="flex flex-col items-center justify-center w-full">
          {showInitial && !isSearching && !foundBot ? (
            <button 
              ref={buttonRef}
              onClick={startDetection}
              className="relative bg-gradient-to-r from-primary/80 to-primary hover:from-primary hover:to-primary/90 text-primary-foreground font-bold py-2 md:py-3 px-6 md:px-8 rounded-full shadow-lg transition-all duration-300 flex items-center overflow-hidden group"
            >
              {/* Shine effect */}
              <div className="absolute inset-0 w-full h-full bg-gradient-to-r from-transparent via-white/20 to-transparent -translate-x-full group-hover:translate-x-full transition-transform duration-1000"></div>
              <Search className="mr-2" size={18} />
              DETECTAR MEJOR BOT
            </button>
          ) : isSearching ? (
            <div className="relative py-6 md:py-8">
              <div ref={radarRef} className="w-24 h-24 md:w-40 md:h-40 rounded-full border-8 md:border-[14px] border-primary/40 relative animate-pulse-ring">
                {/* Inner radar circle */}
                <div className="absolute inset-2 md:inset-4 rounded-full border-4 md:border-8 border-primary/60 animate-pulse"></div>
                <div className="absolute inset-5 md:inset-10 rounded-full border-2 md:border-4 border-primary/20"></div>
                {/* Radar sweep */}
                <div className="absolute w-1 h-10 md:h-20 bg-gradient-to-t from-primary to-primary/70 top-1/2 left-1/2 -ml-0.5 origin-bottom animate-radar-sweep shadow-lg shadow-primary/50"></div>
                {/* Center dot */}
                <div className="absolute w-3 h-3 md:w-4 md:h-4 bg-primary rounded-full top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 shadow-lg shadow-primary/50"></div>
              </div>
              <p className="text-center text-foreground mt-4 md:mt-6 font-medium text-sm md:text-base">
                Escaneando catálogo...
              </p>
            </div>
          ) : foundBot ? (
            <div className="w-full flex justify-center items-center py-4 md:py-6">
              <div className="bg-secondary/80 p-4 md:p-6 rounded-xl backdrop-blur-sm border border-primary/30 flex flex-col md:flex-row items-center relative overflow-hidden w-full max-w-2xl shadow-lg">
                {/* Background gradient effect */}
                <div className="absolute inset-0 bg-gradient-to-br from-primary/5 to-primary/10"></div>
                
                {/* Left side - Bot accuracy circle */}
                <div className="flex flex-col items-center mb-4 md:mb-0 md:mr-6">
                  <div className="relative w-24 h-24 md:w-28 md:h-28 mb-2">
                    {/* Outer ring */}
                    <div className="absolute inset-0 rounded-full bg-gradient-to-r from-primary/70 to-primary/50 animate-pulse-ring"></div>
                    {/* Inner circle with accuracy */}
                    <div className="absolute inset-3 md:inset-4 rounded-full bg-secondary flex items-center justify-center flex-col border-2 border-primary/20">
                      <span className="text-lg md:text-xl font-bold text-foreground">{foundBot.accuracy}%</span>
                      <span className="text-xs text-muted-foreground">Asertividad</span>
                    </div>
                  </div>
                </div>
                
                {/* Center - Bot information */}
                <div className="flex-1 text-center md:text-left">
                  <div className="flex items-center justify-center md:justify-start mb-2">
                    <Award className="text-primary mr-2" size={20} />
                    <span className="text-primary font-semibold text-sm">
                      {currentBotIndex === 0 ? "Bot más Asertivo" : `Bot #${currentBotIndex + 1} en Ranking`}
                    </span>
                  </div>
                  
                  <h3 className="text-xl md:text-2xl font-bold text-foreground mb-2">{foundBot.name}</h3>
                  
                  <p className="text-sm text-muted-foreground mb-3 max-w-md">
                    {foundBot.description.length > 120 
                      ? `${foundBot.description.substring(0, 120)}...` 
                      : foundBot.description
                    }
                  </p>
                  
                  <div className="flex flex-wrap gap-2 justify-center md:justify-start">
                    <span className="px-2 py-1 bg-primary/10 text-primary text-xs rounded-full">
                      {foundBot.strategy}
                    </span>
                    {foundBot.operations > 0 && (
                      <span className="px-2 py-1 bg-muted/50 text-muted-foreground text-xs rounded-full">
                        {foundBot.operations} operações
                      </span>
                    )}
                    <span className="px-2 py-1 bg-green-500/10 text-green-400 text-xs rounded-full">
                      Risk: {foundBot.riskLevel}/10
                    </span>
                  </div>
                </div>
              </div>
            </div>
          ) : null}
        </div>
      </div>
    </div>
  );
};

const Index = () => {
  const [filteredBots, setFilteredBots] = useState(bots);
  const [searchTerm, setSearchTerm] = useState('');
  const [currentStrategy, setCurrentStrategy] = useState('');
  const [currentAsset, setCurrentAsset] = useState('');
  const [sortBy, setSortBy] = useState('performance');
  const [showRanking, setShowRanking] = useState(true);
  const [sortedBots, setSortedBots] = useState<typeof bots>([]);
  const [isLoadingRanking, setIsLoadingRanking] = useState(false);
  const [rankingError, setRankingError] = useState<string | null>(null);



  // Carrega e atualiza o ranking dos bots com dados do Supabase
  useEffect(() => {
    const carregarRankingBots = async () => {
      try {
        setIsLoadingRanking(true);
        setRankingError(null);
        
        // Atualizar bots com dados reais do Supabase
        const botsAtualizados = await atualizarRankingBots();
        
        // Ordenar por precisão (accuracy) para manter o ranking correto
        const sorted = botsAtualizados.sort((a, b) => b.accuracy - a.accuracy);
        setSortedBots(sorted);
        
        // Atualizar filteredBots com os dados atualizados
        setFilteredBots(sorted);
        
      } catch (error) {
        setRankingError('Erro ao carregar dados do ranking');
        
        // Fallback para dados locais
        const sorted = [...bots].sort((a, b) => b.accuracy - a.accuracy);
        setSortedBots(sorted);
        setFilteredBots(sorted);
        
      } finally {
        setIsLoadingRanking(false);
      }
    };

    carregarRankingBots();
  }, []);

  // Atualiza filteredBots quando sortedBots muda
  useEffect(() => {
    filterBots(searchTerm, currentStrategy, currentAsset, sortBy);
  }, [sortedBots, showRanking]);

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
    // Usar sortedBots (com dados do Supabase) em vez de bots estáticos
    const botsToFilter = sortedBots.length > 0 ? sortedBots : bots;
    
    let result = botsToFilter.filter(bot => {
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
            <h1 className="text-2xl font-bold">Panel de Bots de Trading</h1>
            <p className="text-muted-foreground">Gestiona y analiza bots de trading</p>
          </div>
          <SearchInput onChange={handleSearch} />
        </div>
      </section>
      
      {/* Bot Finder Radar Section */}
      <section className="px-6 py-4">
        <BotFinderRadar />
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
            title="Operaciones"
            value={dashboardStats.totalOperations}
            icon={<Clock size={24} />}
            trend={{ value: 12.5, isPositive: true }}
          />
          <StatCard 
            title="Asertividad Media"
            value={`${dashboardStats.averageAccuracy}%`}
            icon={<ChartLine size={24} />}
            trend={{ value: 3.2, isPositive: true }}
          />
          <StatCard 
            title="Usuarios Activos"
            value={dashboardStats.activeUsers}
            icon={<User size={24} />}
            trend={{ value: 5.1, isPositive: true }}
          />
        </div>
      </section>
      
      {/* Investment Risk Warning Banner */}
      <section className="px-6 py-4">
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
      
      {/* Charts Section */}
      <section className="px-6 py-4">
        <h2 className="text-xl font-semibold mb-4">Analítica</h2>
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-6">
          <PerformanceChart 
            data={performanceData.profitLoss} 
            isPositive={true}
            title="Rendimiento (P&L)"
            yAxisLabel="Valor ($)"
          />
          <PerformanceChart 
            data={performanceData.accuracy} 
            isPositive={true}
            title="Asertividad"
            yAxisLabel="%"
          />
          <PerformanceChart 
            data={performanceData.volatility} 
            isPositive={false}
            title="Volatilidad"
            yAxisLabel="Índice"
          />
        </div>
      </section>
      
      {/* Bots Library Section */}
      <section className="px-6 py-4">
        <div className="flex justify-between items-center mb-4">
          <div className="flex items-center gap-3">
            <h2 className="text-xl font-semibold">Ranking de Bots</h2>
            {isLoadingRanking && (
              <div className="flex items-center gap-2 text-sm text-muted-foreground">
                <div className="w-4 h-4 border-2 border-primary border-t-transparent rounded-full animate-spin"></div>
                Actualizando ranking...
              </div>
            )}
            {rankingError && (
              <div className="flex items-center gap-2 text-sm text-orange-600">
                <AlertTriangle size={16} />
                Usando datos locales
              </div>
            )}
            {!isLoadingRanking && !rankingError && sortedBots.length > 0 && (
              <div className="flex items-center gap-2 text-sm text-green-600">
                <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                Datos actualizados
              </div>
            )}
          </div>
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
          {filteredBots.map(bot => (
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
          ))}
          {filteredBots.length === 0 && (
            <div className="col-span-full py-12 text-center text-muted-foreground">
              <p>No se encontraron bots con los filtros actuales.</p>
              <p className="mt-2">Intenta ajustar los filtros o buscar con otros términos.</p>
            </div>
          )}
        </div>
      </section>
    </div>
  );
};

export default Index;
