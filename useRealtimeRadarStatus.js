/**
 * Hook personalizado para escutar mudanças em tempo real na tabela radar_de_apalancamiento_signals
 * 
 * Este hook implementa subscription do Supabase para receber atualizações instantâneas
 * dos status dos bots sem necessidade de polling manual ou refresh da página.
 * 
 * @returns {Object} Estado com dados dos bots e funções de controle
 */

// Importar Supabase client (assumindo que já está configurado)
// import { supabase } from './supabaseClient';

function useRealtimeRadarStatus() {
    // Estado local para armazenar dados dos bots
    const [botsStatus, setBotsStatus] = useState(new Map());
    const [isConnected, setIsConnected] = useState(false);
    const [lastUpdate, setLastUpdate] = useState(null);
    const [error, setError] = useState(null);

    // Função para processar dados recebidos do subscription
    const processRadarData = (payload) => {
        try {
            const { eventType, new: newRecord, old: oldRecord } = payload;
            
            console.log(`[Realtime] Evento recebido: ${eventType}`, newRecord);
            
            setBotsStatus(prevStatus => {
                const newStatus = new Map(prevStatus);
                
                switch (eventType) {
                    case 'INSERT':
                    case 'UPDATE':
                        if (newRecord && newRecord.bot_name) {
                            newStatus.set(newRecord.bot_name, {
                                id: newRecord.id,
                                botName: newRecord.bot_name,
                                isSafeToOperate: newRecord.is_safe_to_operate,
                                reason: newRecord.reason || 'Status não disponível',
                                operationsAfterPattern: newRecord.operations_after_pattern || 0,
                                lastUpdate: newRecord.created_at,
                                patternFoundAt: newRecord.pattern_found_at,
                                // Campos específicos do Tunder Bot
                                lastPatternFound: newRecord.last_pattern_found,
                                lossesInLast10Ops: newRecord.losses_in_last_10_ops,
                                winsInLast5Ops: newRecord.wins_in_last_5_ops,
                                historicalAccuracy: newRecord.historical_accuracy,
                                autoDisableAfterOps: newRecord.auto_disable_after_ops
                            });
                        }
                        break;
                        
                    case 'DELETE':
                        if (oldRecord && oldRecord.bot_name) {
                            newStatus.delete(oldRecord.bot_name);
                        }
                        break;
                }
                
                return newStatus;
            });
            
            setLastUpdate(new Date().toISOString());
            setError(null);
            
        } catch (err) {
            console.error('[Realtime] Erro ao processar dados:', err);
            setError(err.message);
        }
    };

    // Função para buscar dados iniciais
    const fetchInitialData = async () => {
        try {
            console.log('[Realtime] Buscando dados iniciais...');
            
            const { data, error } = await supabase
                .from('radar_de_apalancamiento_signals')
                .select('*')
                .order('created_at', { ascending: false });
            
            if (error) throw error;
            
            const initialStatus = new Map();
            data.forEach(record => {
                if (record.bot_name) {
                    initialStatus.set(record.bot_name, {
                        id: record.id,
                        botName: record.bot_name,
                        isSafeToOperate: record.is_safe_to_operate,
                        reason: record.reason || 'Status não disponível',
                        operationsAfterPattern: record.operations_after_pattern || 0,
                        lastUpdate: record.created_at,
                        patternFoundAt: record.pattern_found_at,
                        // Campos específicos do Tunder Bot
                        lastPatternFound: record.last_pattern_found,
                        lossesInLast10Ops: record.losses_in_last_10_ops,
                        winsInLast5Ops: record.wins_in_last_5_ops,
                        historicalAccuracy: record.historical_accuracy,
                        autoDisableAfterOps: record.auto_disable_after_ops
                    });
                }
            });
            
            setBotsStatus(initialStatus);
            console.log(`[Realtime] ${initialStatus.size} bots carregados inicialmente`);
            
        } catch (err) {
            console.error('[Realtime] Erro ao buscar dados iniciais:', err);
            setError(err.message);
        }
    };

    // Configurar subscription do Supabase
    useEffect(() => {
        let subscription = null;
        
        const setupRealtimeSubscription = async () => {
            try {
                console.log('[Realtime] Configurando subscription...');
                
                // Buscar dados iniciais
                await fetchInitialData();
                
                // Configurar subscription para eventos em tempo real
                subscription = supabase
                    .channel('radar-status-updates')
                    .on(
                        'postgres_changes',
                        {
                            event: '*', // Escutar INSERT, UPDATE e DELETE
                            schema: 'public',
                            table: 'radar_de_apalancamiento_signals'
                        },
                        processRadarData
                    )
                    .subscribe((status) => {
                        console.log('[Realtime] Status da subscription:', status);
                        setIsConnected(status === 'SUBSCRIBED');
                        
                        if (status === 'SUBSCRIPTION_ERROR') {
                            setError('Erro na subscription do Supabase');
                        }
                    });
                
            } catch (err) {
                console.error('[Realtime] Erro ao configurar subscription:', err);
                setError(err.message);
                setIsConnected(false);
            }
        };
        
        setupRealtimeSubscription();
        
        // Cleanup na desmontagem do componente
        return () => {
            if (subscription) {
                console.log('[Realtime] Removendo subscription...');
                supabase.removeChannel(subscription);
            }
        };
    }, []);

    // Função para obter status de um bot específico
    const getBotStatus = (botName) => {
        return botsStatus.get(botName) || null;
    };

    // Função para obter todos os bots como array
    const getAllBots = () => {
        return Array.from(botsStatus.values());
    };

    // Função para verificar se um bot está seguro para operar
    const isBotSafe = (botName) => {
        const bot = botsStatus.get(botName);
        return bot ? bot.isSafeToOperate : false;
    };

    // Função para obter badge de status
    const getBotStatusBadge = (botName) => {
        const bot = botsStatus.get(botName);
        if (!bot) return { text: 'DESCONHECIDO', class: 'badge-unknown' };
        
        return bot.isSafeToOperate 
            ? { text: 'ATIVO', class: 'badge-active' }
            : { text: 'RIESGO', class: 'badge-risk' };
    };

    // Função para forçar atualização manual (fallback)
    const refreshData = async () => {
        await fetchInitialData();
    };

    return {
        // Estados
        botsStatus: getAllBots(),
        isConnected,
        lastUpdate,
        error,
        
        // Funções utilitárias
        getBotStatus,
        getAllBots,
        isBotSafe,
        getBotStatusBadge,
        refreshData,
        
        // Estatísticas
        totalBots: botsStatus.size,
        activeBots: Array.from(botsStatus.values()).filter(bot => bot.isSafeToOperate).length,
        riskBots: Array.from(botsStatus.values()).filter(bot => !bot.isSafeToOperate).length
    };
}

// Exportar o hook
// export default useRealtimeRadarStatus;

/**
 * Exemplo de uso em um componente:
 * 
 * function BotDashboard() {
 *     const {
 *         botsStatus,
 *         isConnected,
 *         lastUpdate,
 *         error,
 *         getBotStatus,
 *         getBotStatusBadge,
 *         totalBots,
 *         activeBots,
 *         riskBots
 *     } = useRealtimeRadarStatus();
 * 
 *     if (error) {
 *         return <div className="error">Erro: {error}</div>;
 *     }
 * 
 *     return (
 *         <div className="dashboard">
 *             <div className="connection-status">
 *                 Status: {isConnected ? '🟢 Conectado' : '🔴 Desconectado'}
 *                 {lastUpdate && <span> | Última atualização: {new Date(lastUpdate).toLocaleTimeString()}</span>}
 *             </div>
 *             
 *             <div className="stats">
 *                 <span>Total: {totalBots}</span>
 *                 <span>Ativos: {activeBots}</span>
 *                 <span>Em Risco: {riskBots}</span>
 *             </div>
 *             
 *             <div className="bots-grid">
 *                 {botsStatus.map(bot => {
 *                     const badge = getBotStatusBadge(bot.botName);
 *                     return (
 *                         <div key={bot.botName} className="bot-card">
 *                             <h3>{bot.botName}</h3>
 *                             <span className={`badge ${badge.class}`}>{badge.text}</span>
 *                             <p className="status-message">{bot.reason}</p>
 *                             <small>Operações após padrão: {bot.operationsAfterPattern}</small>
 *                         </div>
 *                     );
 *                 })}
 *             </div>
 *         </div>
 *     );
 * }
 */