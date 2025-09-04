/**
 * Componente de Cards de Status dos Bots com Realtime Updates
 * 
 * Este componente demonstra como integrar o hook useRealtimeRadarStatus
 * para exibir status dos bots em tempo real sem refresh manual.
 */

import React from 'react';
import useRealtimeRadarStatus from './useRealtimeRadarStatus';

// Estilos CSS inline para demonstração
const styles = {
    dashboard: {
        padding: '20px',
        fontFamily: 'Arial, sans-serif'
    },
    connectionStatus: {
        padding: '10px',
        marginBottom: '20px',
        borderRadius: '5px',
        backgroundColor: '#f0f0f0',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center'
    },
    connected: {
        color: '#28a745',
        fontWeight: 'bold'
    },
    disconnected: {
        color: '#dc3545',
        fontWeight: 'bold'
    },
    stats: {
        display: 'flex',
        gap: '20px',
        marginBottom: '20px',
        padding: '15px',
        backgroundColor: '#e9ecef',
        borderRadius: '5px'
    },
    statItem: {
        textAlign: 'center'
    },
    statNumber: {
        fontSize: '24px',
        fontWeight: 'bold',
        display: 'block'
    },
    statLabel: {
        fontSize: '12px',
        color: '#6c757d'
    },
    botsGrid: {
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))',
        gap: '20px'
    },
    botCard: {
        border: '1px solid #dee2e6',
        borderRadius: '8px',
        padding: '20px',
        backgroundColor: '#fff',
        boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
        transition: 'transform 0.2s, box-shadow 0.2s'
    },
    botCardHover: {
        transform: 'translateY(-2px)',
        boxShadow: '0 4px 8px rgba(0,0,0,0.15)'
    },
    botHeader: {
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        marginBottom: '15px'
    },
    botName: {
        margin: 0,
        fontSize: '18px',
        fontWeight: 'bold'
    },
    badge: {
        padding: '4px 12px',
        borderRadius: '20px',
        fontSize: '12px',
        fontWeight: 'bold',
        textTransform: 'uppercase'
    },
    badgeActive: {
        backgroundColor: '#28a745',
        color: 'white'
    },
    badgeRisk: {
        backgroundColor: '#dc3545',
        color: 'white'
    },
    badgeUnknown: {
        backgroundColor: '#6c757d',
        color: 'white'
    },
    statusMessage: {
        margin: '10px 0',
        padding: '10px',
        backgroundColor: '#f8f9fa',
        borderRadius: '4px',
        fontSize: '14px',
        lineHeight: '1.4'
    },
    botDetails: {
        display: 'grid',
        gridTemplateColumns: '1fr 1fr',
        gap: '10px',
        fontSize: '12px',
        color: '#6c757d'
    },
    detailItem: {
        display: 'flex',
        justifyContent: 'space-between'
    },
    lastUpdate: {
        fontSize: '11px',
        color: '#adb5bd',
        textAlign: 'center',
        marginTop: '10px',
        fontStyle: 'italic'
    },
    error: {
        padding: '15px',
        backgroundColor: '#f8d7da',
        color: '#721c24',
        border: '1px solid #f5c6cb',
        borderRadius: '5px',
        marginBottom: '20px'
    },
    loading: {
        textAlign: 'center',
        padding: '40px',
        fontSize: '16px',
        color: '#6c757d'
    },
    refreshButton: {
        padding: '8px 16px',
        backgroundColor: '#007bff',
        color: 'white',
        border: 'none',
        borderRadius: '4px',
        cursor: 'pointer',
        fontSize: '12px'
    }
};

function BotStatusCards() {
    const {
        botsStatus,
        isConnected,
        lastUpdate,
        error,
        getBotStatusBadge,
        refreshData,
        totalBots,
        activeBots,
        riskBots
    } = useRealtimeRadarStatus();

    // Função para formatar timestamp
    const formatTimestamp = (timestamp) => {
        if (!timestamp) return 'N/A';
        return new Date(timestamp).toLocaleString('pt-BR');
    };

    // Função para obter estilo do badge
    const getBadgeStyle = (badgeClass) => {
        const baseStyle = { ...styles.badge };
        switch (badgeClass) {
            case 'badge-active':
                return { ...baseStyle, ...styles.badgeActive };
            case 'badge-risk':
                return { ...baseStyle, ...styles.badgeRisk };
            default:
                return { ...baseStyle, ...styles.badgeUnknown };
        }
    };

    // Renderizar erro se houver
    if (error) {
        return (
            <div style={styles.dashboard}>
                <div style={styles.error}>
                    <strong>Erro na conexão realtime:</strong> {error}
                    <br />
                    <button 
                        style={styles.refreshButton} 
                        onClick={refreshData}
                    >
                        Tentar Novamente
                    </button>
                </div>
            </div>
        );
    }

    // Renderizar loading se não há dados
    if (botsStatus.length === 0) {
        return (
            <div style={styles.dashboard}>
                <div style={styles.loading}>
                    🔄 Carregando status dos bots...
                </div>
            </div>
        );
    }

    return (
        <div style={styles.dashboard}>
            {/* Status da Conexão */}
            <div style={styles.connectionStatus}>
                <span style={isConnected ? styles.connected : styles.disconnected}>
                    {isConnected ? '🟢 Realtime Conectado' : '🔴 Realtime Desconectado'}
                </span>
                <div>
                    {lastUpdate && (
                        <span>Última atualização: {formatTimestamp(lastUpdate)}</span>
                    )}
                    <button 
                        style={{ ...styles.refreshButton, marginLeft: '10px' }}
                        onClick={refreshData}
                    >
                        🔄 Atualizar
                    </button>
                </div>
            </div>

            {/* Estatísticas Gerais */}
            <div style={styles.stats}>
                <div style={styles.statItem}>
                    <span style={styles.statNumber}>{totalBots}</span>
                    <span style={styles.statLabel}>Total de Bots</span>
                </div>
                <div style={styles.statItem}>
                    <span style={{ ...styles.statNumber, color: '#28a745' }}>{activeBots}</span>
                    <span style={styles.statLabel}>Bots Ativos</span>
                </div>
                <div style={styles.statItem}>
                    <span style={{ ...styles.statNumber, color: '#dc3545' }}>{riskBots}</span>
                    <span style={styles.statLabel}>Bots em Risco</span>
                </div>
            </div>

            {/* Grid de Cards dos Bots */}
            <div style={styles.botsGrid}>
                {botsStatus.map(bot => {
                    const badge = getBotStatusBadge(bot.botName);
                    
                    return (
                        <div 
                            key={bot.botName} 
                            style={styles.botCard}
                            onMouseEnter={(e) => {
                                Object.assign(e.target.style, styles.botCardHover);
                            }}
                            onMouseLeave={(e) => {
                                e.target.style.transform = 'none';
                                e.target.style.boxShadow = '0 2px 4px rgba(0,0,0,0.1)';
                            }}
                        >
                            {/* Header do Card */}
                            <div style={styles.botHeader}>
                                <h3 style={styles.botName}>{bot.botName}</h3>
                                <span style={getBadgeStyle(badge.class)}>
                                    {badge.text}
                                </span>
                            </div>

                            {/* Mensagem de Status */}
                            <div style={styles.statusMessage}>
                                {bot.reason}
                            </div>

                            {/* Detalhes do Bot */}
                            <div style={styles.botDetails}>
                                <div style={styles.detailItem}>
                                    <span>Operações após padrão:</span>
                                    <strong>{bot.operationsAfterPattern}</strong>
                                </div>
                                
                                {bot.lastPatternFound && (
                                    <div style={styles.detailItem}>
                                        <span>Último padrão:</span>
                                        <strong>{bot.lastPatternFound}</strong>
                                    </div>
                                )}
                                
                                {bot.historicalAccuracy !== undefined && (
                                    <div style={styles.detailItem}>
                                        <span>Precisão histórica:</span>
                                        <strong>{(bot.historicalAccuracy * 100).toFixed(1)}%</strong>
                                    </div>
                                )}
                                
                                {bot.winsInLast5Ops !== undefined && (
                                    <div style={styles.detailItem}>
                                        <span>Vitórias (últimas 5):</span>
                                        <strong>{bot.winsInLast5Ops}</strong>
                                    </div>
                                )}
                            </div>

                            {/* Timestamp da Última Atualização */}
                            <div style={styles.lastUpdate}>
                                Atualizado em: {formatTimestamp(bot.lastUpdate)}
                            </div>
                        </div>
                    );
                })}
            </div>
        </div>
    );
}

export default BotStatusCards;

/**
 * Exemplo de uso em uma aplicação:
 * 
 * import React from 'react';
 * import BotStatusCards from './BotStatusCards';
 * 
 * function App() {
 *     return (
 *         <div className="App">
 *             <header>
 *                 <h1>Dashboard de Trading Bots</h1>
 *             </header>
 *             <main>
 *                 <BotStatusCards />
 *             </main>
 *         </div>
 *     );
 * }
 * 
 * export default App;
 */