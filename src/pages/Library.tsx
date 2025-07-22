import React, { useState, useEffect, useMemo } from 'react';
import { supabase } from '../lib/supabaseClient';
import BotPerformanceCard from '../components/BotPerformanceCard';
import SkeletonCard from '../components/SkeletonCard';
import TimeFilterControls from '../components/TimeFilterControls';
import LoadingState from '../components/LoadingState';
import { 
  Search, 
  Filter, 
  SortDesc, 
  ChevronDown, 
  Shield, 
  BarChart3, 
  Target, 
  Users, 
  Star,
  TrendingUp,
  Activity,
  Zap,
  Award,
  Bot,
  DollarSign,
  Trophy,
  Sparkles,
  ArrowUpDown,
  X
} from 'lucide-react';
import { useNavigate } from 'react-router-dom';

interface BotStats {
  nome_bot: string;
  total_operacoes: number;
  vitorias: number;
  derrotas: number;
  assertividade_percentual: number;
  lucro_total?: number;
}

const Library = () => {
  const navigate = useNavigate();
  
  // Estados principais - ÚNICA FONTE DE DADOS
  const [periodoSelecionado, setPeriodoSelecionado] = useState('24 hours');
  const [stats, setStats] = useState<BotStats[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  // Estados para filtros profissionais
  const [searchTerm, setSearchTerm] = useState('');
  const [performanceFilter, setPerformanceFilter] = useState<'all' | 'excellent' | 'good' | 'average'>('all');
  const [sortBy, setSortBy] = useState<'accuracy' | 'operations' | 'wins' | 'name'>('accuracy');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc');
  const [showFilters, setShowFilters] = useState(false);
  
  // Estados para filtros avançados
  const [advancedFilters, setAdvancedFilters] = useState({
    showMostAssertive: false,    // Más Asertivos (>80%)
    showMostProfitable: false    // Más Lucrativos (mayor lucro y positivos)
  });
  
  // Novos estados para controle de exibição
  const [showResults, setShowResults] = useState(false);
  const [isFirstLoad, setIsFirstLoad] = useState(true);
  const [isLoadingTransition, setIsLoadingTransition] = useState(false);
  
  // Função para lidar com a mudança de período
  const handlePeriodChange = (periodo: string) => {
    // Se for a primeira seleção ou uma mudança de período
    if (isFirstLoad || periodoSelecionado !== periodo) {
      setPeriodoSelecionado(periodo);
      setIsLoadingTransition(true);
      
      // Se for a primeira carga, atualizar o estado
      if (isFirstLoad) {
        setIsFirstLoad(false);
      }
      
      // Simular um tempo de carregamento para melhor UX
      setTimeout(() => {
        setShowResults(true);
        setIsLoadingTransition(false);
      }, 1500); // Tempo suficiente para mostrar a animação de loading
    }
  };
  
  // useEffect principal - ÚNICA FONTE DE DADOS
  useEffect(() => {
    // Só buscar dados se não for a primeira carga (após seleção do usuário)
    if (!isFirstLoad) {
      const fetchFilteredStats = async () => {
        setLoading(true);
        setError(null);
  
        console.log(`[DIAGNÓSTICO] Chamando RPC com período: '${periodoSelecionado}'`);
  
        const { data, error: rpcError } = await supabase.rpc(
          'calcular_estatisticas_por_periodo',
          { periodo: periodoSelecionado }
        );
  
        if (rpcError) {
          console.error("[DIAGNÓSTICO] Erro na chamada RPC:", rpcError);
          setError("Não foi possível carregar os dados. Verifique o console para detalhes técnicos.");
        } else {
          console.log(`[DIAGNÓSTICO] Dados recebidos da RPC:`, data);
          setStats(data || []);
        }
        
        setLoading(false);
      };
    
      fetchFilteredStats();
    }
  }, [periodoSelecionado, isFirstLoad]);
  
  // Função para mapear nomes de bots para suas rotas específicas
  const getBotRoute = (botName: string): string => {
    const normalizedName = botName.toLowerCase().replace(/[_\s]/g, '');
    
    const botRoutes: { [key: string]: string } = {
      'quantumbotfixedstake': '/bot/11',
      'quantumbot': '/bot/11',
      'botapalancamiento': '/apalancamiento-100x',
      'apalancamiento': '/apalancamiento-100x',
      'botai2.0': '/bot/16',
      'botai': '/bot/16',
      'factor50xconservador': '/factor50x',
      'factor50x': '/factor50x',
      'wolfbot2.0': '/bot/wolf-bot',
      'wolfbot': '/bot/wolf-bot',
      'sniperbotmartingale': '/bot/15',
      'sniperbot': '/bot/15',
      'nexusbot': '/bot/14',
      'bkbot1.0': '/bk-bot',
      'bkbot': '/bk-bot'
    };
  
    return botRoutes[normalizedName] || '/';
  };
  
  // Função para navegar para a página do bot
  const handleBotClick = (botName: string) => {
    const route = getBotRoute(botName);
    navigate(route);
  };
  
  // Función para obtener el color de la asertividad
  const getAccuracyColor = (accuracy: number) => {
    if (accuracy >= 80) return 'text-emerald-500';
    if (accuracy >= 70) return 'text-primary';
    if (accuracy >= 60) return 'text-blue-500';
    return 'text-orange-500';
  };
  
  // Función para obtener el color del progreso
  const getProgressColor = (accuracy: number) => {
    if (accuracy >= 80) return 'from-emerald-500 to-emerald-400';
    if (accuracy >= 70) return 'from-primary to-primary/80';
    if (accuracy >= 60) return 'from-blue-500 to-blue-400';
    return 'from-orange-500 to-orange-400';
  };
  
  // Lógica de filtros e ordenação com useMemo para performance
  const filteredAndSortedStats = useMemo(() => {
    let filtered = stats.filter(bot => {
      // Filtro de busca
      const matchesSearch = bot.nome_bot.toLowerCase().includes(searchTerm.toLowerCase());
      
      // Filtro de performance
      const accuracy = parseFloat(bot.assertividade_percentual?.toString() || '0');
      let matchesPerformance = true;
      
      switch (performanceFilter) {
        case 'excellent':
          matchesPerformance = accuracy >= 80;
          break;
        case 'good':
          matchesPerformance = accuracy >= 70 && accuracy < 80;
          break;
        case 'average':
          matchesPerformance = accuracy < 70;
          break;
        default:
          matchesPerformance = true;
      }
      
      // Filtros avançados simplificados
      let matchesMostAssertive = true;
      if (advancedFilters.showMostAssertive) {
        matchesMostAssertive = bot.assertividade_percentual >= 80;
      }
      
      let matchesMostProfitable = true;
      if (advancedFilters.showMostProfitable && bot.lucro_total !== undefined) {
        matchesMostProfitable = bot.lucro_total > 0;
      }

      return matchesSearch && matchesPerformance && matchesMostAssertive && matchesMostProfitable;
    });

    // Ordenação
    filtered.sort((a, b) => {
      let aValue: number | string;
      let bValue: number | string;
      
      // Se o filtro "Más Lucrativos" estiver ativo, priorizar ordenação por lucro
      if (advancedFilters.showMostProfitable && sortBy === 'accuracy') {
        aValue = a.lucro_total || 0;
        bValue = b.lucro_total || 0;
      } else {
        switch (sortBy) {
          case 'accuracy':
            aValue = parseFloat(a.assertividade_percentual?.toString() || '0');
            bValue = parseFloat(b.assertividade_percentual?.toString() || '0');
            break;
          case 'operations':
            aValue = parseInt(a.total_operacoes?.toString() || '0');
            bValue = parseInt(b.total_operacoes?.toString() || '0');
            break;
          case 'wins':
            aValue = parseInt(a.vitorias?.toString() || '0');
            bValue = parseInt(b.vitorias?.toString() || '0');
            break;
          case 'name':
            aValue = a.nome_bot.toLowerCase();
            bValue = b.nome_bot.toLowerCase();
            break;
          default:
            aValue = parseFloat(a.assertividade_percentual?.toString() || '0');
            bValue = parseFloat(b.assertividade_percentual?.toString() || '0');
        }
      }
      
      if (sortOrder === 'asc') {
        return aValue > bValue ? 1 : -1;
      } else {
        return aValue < bValue ? 1 : -1;
      }
    });

    return filtered;
  }, [stats, searchTerm, performanceFilter, sortBy, sortOrder, advancedFilters]);

  // Estatísticas calculadas
  const localStats = useMemo(() => {
    const totalBots = filteredAndSortedStats.length;
    const avgAccuracy = totalBots > 0 ? filteredAndSortedStats.reduce((sum, bot) => sum + parseFloat(bot.assertividade_percentual?.toString() || '0'), 0) / totalBots : 0;
    const totalOperations = filteredAndSortedStats.reduce((sum, bot) => sum + parseInt(bot.total_operacoes?.toString() || '0'), 0);
    const excellentBots = filteredAndSortedStats.filter(bot => parseFloat(bot.assertividade_percentual?.toString() || '0') >= 80).length;
    
    return {
      totalBots,
      avgAccuracy: Math.round(avgAccuracy * 10) / 10,
      totalOperations,
      excellentBots
    };
  }, [filteredAndSortedStats]);

  // Renderização condicional para loading inicial
  if (loading && isLoadingTransition === false) {
    return (
      <div className="container max-w-7xl mx-auto py-8 px-4 animate-in fade-in duration-500">
        <section className="mb-12">
          <div className="relative overflow-hidden rounded-2xl shadow-xl">
            <div className="absolute inset-0 bg-gradient-to-br from-primary/25 via-primary/15 to-background"></div>
            
            <div className="relative z-10 py-12 px-8 text-center">
              <div className="inline-block mb-3 bg-primary/10 backdrop-blur-sm rounded-full px-4 py-1.5 border border-primary/20">
                <span className="text-primary font-medium text-sm flex items-center gap-2">
                  <Award size={14} className="text-primary" />
                  Ranking de Asertividad
                </span>
              </div>
              <h1 className="text-4xl md:text-5xl font-bold mb-8 text-foreground leading-tight">
                🏆 <span className="text-primary">Ranking de Asertividad</span>
              </h1>
              
              <div className="bg-primary/10 border border-primary/30 rounded-xl p-6 max-w-md mx-auto">
                <div className="flex items-center gap-3 mb-4">
                  <div className="w-10 h-10 rounded-full bg-primary/20 flex items-center justify-center">
                    <Bot className="text-primary animate-spin" size={20} />
                  </div>
                  <div className="text-left">
                    <h3 className="font-semibold text-primary">Cargando datos</h3>
                    <p className="text-sm text-muted-foreground">Analizando rendimiento de bots</p>
                  </div>
                </div>
                <div className="flex items-center gap-2 text-sm text-muted-foreground">
                  <div className="w-2 h-2 bg-primary rounded-full animate-pulse"></div>
                  <span>Procesando estadísticas...</span>
                </div>
              </div>
            </div>
          </div>
        </section>
      </div>
    );
  }

  if (error && stats.length === 0 && !isFirstLoad) {
    return (
      <div className="container max-w-7xl mx-auto py-8 px-4 animate-in fade-in duration-500">
        <section className="mb-12">
          <div className="relative overflow-hidden rounded-2xl shadow-xl">
            <div className="absolute inset-0 bg-gradient-to-br from-primary/25 via-primary/15 to-background"></div>
            
            <div className="relative z-10 py-12 px-8 text-center">
              <div className="inline-block mb-3 bg-primary/10 backdrop-blur-sm rounded-full px-4 py-1.5 border border-primary/20">
                <span className="text-primary font-medium text-sm flex items-center gap-2">
                  <Award size={14} className="text-primary" />
                  Ranking de Asertividad
                </span>
              </div>
              <h1 className="text-4xl md:text-5xl font-bold mb-8 text-foreground leading-tight">
                🏆 <span className="text-primary">Ranking de Asertividad</span>
              </h1>
              
              <div className="bg-destructive/10 border border-destructive/30 rounded-xl p-6 max-w-md mx-auto">
                <div className="flex items-center gap-3 mb-4">
                  <div className="w-10 h-10 rounded-full bg-destructive/20 flex items-center justify-center">
                    <Bot className="text-destructive" size={20} />
                  </div>
                  <div className="text-left">
                    <h3 className="font-semibold text-destructive">Error al cargar datos</h3>
                    <p className="text-sm text-muted-foreground">Problema de conexión detectado</p>
                  </div>
                </div>
                <p className="text-sm text-destructive/80 mb-4">{error}</p>
                <div className="flex items-center gap-2 text-sm text-muted-foreground">
                  <div className="w-2 h-2 bg-primary rounded-full animate-pulse"></div>
                  <span>Cargando datos simulados...</span>
                </div>
              </div>
            </div>
          </div>
        </section>
      </div>
    );
  }

  return (
    <div className="container max-w-7xl mx-auto py-8 px-4 animate-in fade-in duration-500">
      {/* Hero Section */}
      <section className="mb-12">
        <div className="relative overflow-hidden rounded-2xl shadow-xl">
          <div className="absolute inset-0 bg-gradient-to-br from-primary/25 via-primary/15 to-background"></div>
          
          {/* Elementos decorativos */}
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
                  <Award size={14} className="text-primary" />
                  Ranking de Asertividad
                </span>
              </div>
              <h1 className="text-4xl md:text-5xl font-bold mb-4 text-foreground leading-tight">
                🏆 <span className="text-primary">Ranking de Asertividad</span>
              </h1>
              <p className="text-lg text-muted-foreground mb-6">
                Descubre los bots de trading con mejor desempeño en nuestra plataforma. 
                Analiza su asertividad, operaciones y resultados en diferentes períodos de tiempo.
              </p>
              
              {showResults && (
                <div className="flex flex-wrap gap-4 mt-6">
                  <div className="flex items-center gap-2 bg-primary/10 backdrop-blur-sm rounded-full px-4 py-2 border border-primary/20">
                    <Zap size={16} className="text-primary" />
                    <span className="text-sm font-medium">
                      <span className="text-primary">{localStats.totalBots}</span> Bots Analizados
                    </span>
                  </div>
                  <div className="flex items-center gap-2 bg-emerald-500/10 backdrop-blur-sm rounded-full px-4 py-2 border border-emerald-500/20">
                    <TrendingUp size={16} className="text-emerald-500" />
                    <span className="text-sm font-medium">
                      <span className="text-emerald-500">{localStats.excellentBots}</span> Bots Excelentes
                    </span>
                  </div>
                  <div className="flex items-center gap-2 bg-blue-500/10 backdrop-blur-sm rounded-full px-4 py-2 border border-blue-500/20">
                    <Activity size={16} className="text-blue-500" />
                    <span className="text-sm font-medium">
                      <span className="text-blue-500">{localStats.avgAccuracy}%</span> Precisión Media
                    </span>
                  </div>
                </div>
              )}
            </div>
            
            {showResults && (
              <div className="w-full md:w-auto mt-8 md:mt-0">
                <div className="bg-card/50 backdrop-blur-sm rounded-xl border border-border/50 p-6 shadow-lg">
                  <div className="flex items-center gap-3 mb-4">
                    <div className="w-12 h-12 rounded-full bg-primary/10 flex items-center justify-center">
                      <BarChart3 className="text-primary" size={24} />
                    </div>
                    <div>
                      <h3 className="font-semibold text-foreground">Estadísticas Globales</h3>
                      <p className="text-sm text-muted-foreground">Período: {periodoSelecionado}</p>
                    </div>
                  </div>
                  
                  <div className="space-y-4">
                    <div>
                      <div className="flex justify-between mb-1">
                        <span className="text-sm text-muted-foreground">Operaciones Totales</span>
                        <span className="text-sm font-medium">{localStats.totalOperations.toLocaleString()}</span>
                      </div>
                      <div className="h-2 bg-background rounded-full overflow-hidden">
                        <div className="h-full bg-gradient-to-r from-primary/50 to-primary rounded-full" style={{ width: '100%' }}></div>
                      </div>
                    </div>
                    
                    <div>
                      <div className="flex justify-between mb-1">
                        <span className="text-sm text-muted-foreground">Precisión Media</span>
                        <span className="text-sm font-medium">{localStats.avgAccuracy}%</span>
                      </div>
                      <div className="h-2 bg-background rounded-full overflow-hidden">
                        <div className="h-full bg-gradient-to-r from-emerald-500/50 to-emerald-500 rounded-full" style={{ width: `${localStats.avgAccuracy}%` }}></div>
                      </div>
                    </div>
                    
                    <div>
                      <div className="flex justify-between mb-1">
                        <span className="text-sm text-muted-foreground">Bots Excelentes</span>
                        <span className="text-sm font-medium">{localStats.excellentBots} de {localStats.totalBots}</span>
                      </div>
                      <div className="h-2 bg-background rounded-full overflow-hidden">
                        <div className="h-full bg-gradient-to-r from-blue-500/50 to-blue-500 rounded-full" style={{ width: `${(localStats.excellentBots / Math.max(localStats.totalBots, 1)) * 100}%` }}></div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </section>
      
      {/* Controles de filtro por período */}
      <section className="mb-8">
        <div className="flex justify-center">
          <TimeFilterControls 
            periodoAtual={periodoSelecionado} 
            onPeriodoChange={handlePeriodChange}
            showResults={showResults}
          />
        </div>
      </section>

      {/* Filtros Avanzados */}
      {showResults && !isLoadingTransition && (
        <section className="mb-8 animate-in fade-in slide-in-from-bottom-4 duration-300">
          <div className="max-w-6xl mx-auto">
            {/* Header de los Filtros */}
            <div className="flex items-center gap-3 mb-6">
              <div className="w-10 h-10 rounded-full bg-primary/10 flex items-center justify-center">
                <Filter className="text-primary" size={20} />
              </div>
              <div>
                <h2 className="text-xl font-semibold text-foreground">Filtros Avanzados</h2>
                <p className="text-sm text-muted-foreground">Encuentra los robots más exitosos</p>
              </div>
            </div>

            {/* Filtros Básicos - Siempre Visibles */}
            <div className="bg-card/50 backdrop-blur-sm rounded-xl border border-border/50 p-6 mb-4">
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                {/* Buscar por Nombre */}
                <div className="space-y-2">
                  <label className="text-sm font-medium text-foreground flex items-center gap-2">
                    <Search size={14} className="text-primary" />
                    Buscar por Nombre
                  </label>
                  <div className="relative">
                    <input
                      type="text"
                      placeholder="Escribe el nombre del robot..."
                      value={searchTerm}
                      onChange={(e) => setSearchTerm(e.target.value)}
                      className="w-full px-4 py-2 bg-background border border-border rounded-lg focus:ring-2 focus:ring-primary/20 focus:border-primary transition-all duration-200"
                    />
                    {searchTerm && (
                      <button
                        onClick={() => setSearchTerm('')}
                        className="absolute right-2 top-1/2 -translate-y-1/2 p-1 hover:bg-muted rounded"
                      >
                        <X size={14} className="text-muted-foreground" />
                      </button>
                    )}
                  </div>
                </div>

                {/* Filtro de Rendimiento */}
                <div className="space-y-2">
                  <label className="text-sm font-medium text-foreground flex items-center gap-2">
                    <Target size={14} className="text-primary" />
                    Nivel de Rendimiento
                  </label>
                  <select
                    value={performanceFilter}
                    onChange={(e) => setPerformanceFilter(e.target.value)}
                    className="w-full px-4 py-2 bg-background border border-border rounded-lg focus:ring-2 focus:ring-primary/20 focus:border-primary transition-all duration-200"
                  >
                    <option value="all">Todos los Niveles</option>
                    <option value="excellent">Excelente (≥80%)</option>
                    <option value="good">Bueno (60-79%)</option>
                    <option value="average">Promedio (40-59%)</option>
                  </select>
                </div>

                {/* Filtro Elite: Más Asertivos */}
                <div className="space-y-2">
                  <label className="text-sm font-medium text-foreground flex items-center gap-2">
                    <BarChart3 size={14} className="text-emerald-500" />
                    Más Asertivos
                  </label>
                  <button
                    onClick={() => setAdvancedFilters(prev => ({
                      ...prev,
                      showMostAssertive: !prev.showMostAssertive
                    }))}
                    className={`w-full px-4 py-2 rounded-lg border-2 transition-all duration-300 flex items-center justify-center gap-2 ${
                      advancedFilters.showMostAssertive 
                        ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-600 shadow-lg shadow-emerald-500/10' 
                        : 'bg-background border-border hover:border-emerald-500/20 hover:bg-emerald-500/5 text-muted-foreground hover:text-emerald-600'
                    }`}
                  >
                    <div className={`w-3 h-3 rounded-full transition-all duration-300 ${
                      advancedFilters.showMostAssertive ? 'bg-emerald-500' : 'bg-muted-foreground/30'
                    }`}></div>
                    <span className="text-sm font-medium">≥80%</span>
                  </button>
                </div>

                {/* Filtro Elite: Más Lucrativos */}
                <div className="space-y-2">
                  <label className="text-sm font-medium text-foreground flex items-center gap-2">
                    <DollarSign size={14} className="text-green-500" />
                    Más Lucrativos
                  </label>
                  <button
                    onClick={() => setAdvancedFilters(prev => ({
                      ...prev,
                      showMostProfitable: !prev.showMostProfitable
                    }))}
                    className={`w-full px-4 py-2 rounded-lg border-2 transition-all duration-300 flex items-center justify-center gap-2 ${
                      advancedFilters.showMostProfitable 
                        ? 'bg-green-500/10 border-green-500/30 text-green-600 shadow-lg shadow-green-500/10' 
                        : 'bg-background border-border hover:border-green-500/20 hover:bg-green-500/5 text-muted-foreground hover:text-green-600'
                    }`}
                  >
                    <div className={`w-3 h-3 rounded-full transition-all duration-300 ${
                      advancedFilters.showMostProfitable ? 'bg-green-500' : 'bg-muted-foreground/30'
                    }`}></div>
                    <span className="text-sm font-medium">Positivos</span>
                  </button>
                </div>
              </div>
            </div>

            {/* Botón de Reset - Minimalista */}
            <div className="flex justify-center mb-4">
              <button
                onClick={() => {
                  setAdvancedFilters({
                    showMostAssertive: false,
                    showMostProfitable: false
                  });
                  setSearchTerm('');
                  setPerformanceFilter('all');
                  setSortBy('accuracy');
                  setSortOrder('desc');
                }}
                className="flex items-center gap-2 px-4 py-2 bg-muted/50 hover:bg-muted/80 rounded-lg border border-border transition-all duration-200 group"
              >
                <X size={16} className="text-muted-foreground group-hover:text-foreground transition-colors" />
                <span className="text-sm font-medium text-muted-foreground group-hover:text-foreground transition-colors">
                  Limpiar Filtros
                </span>
              </button>
            </div>

            {/* Resultados de los Filtros */}
            <div className="mt-4 flex items-center justify-between text-sm text-muted-foreground">
              <div className="flex items-center gap-2">
                <Users size={14} />
                <span>
                  Mostrando <span className="font-medium text-primary">{filteredAndSortedStats.length}</span> de{' '}
                  <span className="font-medium">{stats?.length || 0}</span> robots
                </span>
              </div>
              {(searchTerm || performanceFilter !== 'all' || advancedFilters.showMostAssertive || 
                advancedFilters.showMostProfitable) && (
                <div className="flex items-center gap-2 text-primary">
                  <Filter size={14} />
                  <span>Filtros activos</span>
                </div>
              )}
            </div>
          </div>
        </section>
      )}

      {/* Estado de carregamento personalizado */}
      {isLoadingTransition && (
        <section className="mb-8 animate-in fade-in slide-in-from-bottom-4 duration-300">
          <LoadingState message={`Analisando dados dos últimos ${periodoSelecionado}`} />
        </section>
      )}

      {/* Container dos cards - Design profissional com cores nativas */}
      {showResults && !isLoadingTransition && (
        <section className="animate-in fade-in slide-in-from-bottom-4 duration-300">
          {loading && (
            <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
              {[...Array(6)].map((_, i) => <SkeletonCard key={i} />)}
            </div>
          )}

          {!loading && error && (
            <div className="text-center py-10 text-red-500">{error}</div>
          )}

          {!loading && !error && filteredAndSortedStats.length === 0 && (
            <div className="text-center py-10 text-gray-500">
              Nenhuma operação encontrada para este período.
            </div>
          )}

          {!loading && !error && filteredAndSortedStats.length > 0 && (
            <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
              {filteredAndSortedStats.map((bot, index) => (
                <BotPerformanceCard 
                  key={bot.nome_bot} 
                  bot={bot} 
                  index={index} 
                  periodoSelecionado={periodoSelecionado}
                />
              ))}
            </div>
          )}
        </section>
      )}
    </div>
  );
};

export default Library;