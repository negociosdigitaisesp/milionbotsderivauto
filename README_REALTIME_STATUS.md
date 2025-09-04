# Sistema de Status em Tempo Real - Radar de Bots

## 📋 Visão Geral

Este sistema implementa atualizações de status em tempo real para os bots de trading, permitindo que o frontend receba atualizações instantâneas sem necessidade de refresh manual ou polling.

## 🎯 Objetivos Alcançados

✅ **Backend modificado** para usar UPSERT na tabela `radar_de_apalancamiento_signals`  
✅ **Campos obrigatórios** sempre preenchidos com timestamp atualizado  
✅ **Hook personalizado** para subscription do Supabase criado  
✅ **Componente de exemplo** para exibir cards dos bots  
✅ **Sistema testado** e funcionando corretamente  

## 🔧 Arquivos Modificados/Criados

### Backend Python
- `radar_analyzer.py` - ✅ Já usando UPSERT com `on_conflict='bot_name'`
- `radar_analyzer_tunder.py` - ✅ Já usando UPSERT com `on_conflict='bot_name'`
- `test_realtime_status.py` - 🆕 Script de teste do sistema

### Frontend JavaScript/React
- `useRealtimeRadarStatus.js` - 🆕 Hook personalizado para realtime
- `BotStatusCards.jsx` - 🆕 Componente de exemplo dos cards
- `supabaseClient.js` - 🆕 Configuração do cliente Supabase

## 📊 Estrutura da Tabela

A tabela `radar_de_apalancamiento_signals` contém os seguintes campos obrigatórios:

```sql
- id (PRIMARY KEY)
- bot_name (UNIQUE) - Chave para UPSERT
- is_safe_to_operate (BOOLEAN) - Status do bot
- reason (TEXT) - Mensagem de status
- operations_after_pattern (INTEGER) - Contador de operações
- created_at (TIMESTAMP) - Timestamp da última atualização
- pattern_found_at (TIMESTAMP) - Quando o padrão foi encontrado

-- Campos específicos do Tunder Bot:
- last_pattern_found (TEXT)
- losses_in_last_10_ops (INTEGER)
- wins_in_last_5_ops (INTEGER)
- historical_accuracy (FLOAT)
- auto_disable_after_ops (INTEGER)
```

## 🚀 Como Implementar no Frontend

### 1. Instalar Dependências

```bash
npm install @supabase/supabase-js
# ou
yarn add @supabase/supabase-js
```

### 2. Configurar Variáveis de Ambiente

Crie um arquivo `.env` no seu projeto React:

```env
REACT_APP_SUPABASE_URL=https://your-project.supabase.co
REACT_APP_SUPABASE_ANON_KEY=your-anon-key-here
```

### 3. Configurar Cliente Supabase

Use o arquivo `supabaseClient.js` fornecido ou configure manualmente:

```javascript
import { createClient } from '@supabase/supabase-js';

const supabaseUrl = process.env.REACT_APP_SUPABASE_URL;
const supabaseAnonKey = process.env.REACT_APP_SUPABASE_ANON_KEY;

export const supabase = createClient(supabaseUrl, supabaseAnonKey, {
  realtime: {
    params: {
      eventsPerSecond: 10,
    },
  },
});
```

### 4. Usar o Hook de Realtime

```javascript
import useRealtimeRadarStatus from './useRealtimeRadarStatus';

function MyComponent() {
  const {
    botsStatus,
    isConnected,
    lastUpdate,
    error,
    getBotStatus,
    getBotStatusBadge,
    totalBots,
    activeBots,
    riskBots
  } = useRealtimeRadarStatus();

  if (error) {
    return <div>Erro: {error}</div>;
  }

  return (
    <div>
      <div>Status: {isConnected ? '🟢 Conectado' : '🔴 Desconectado'}</div>
      <div>Total: {totalBots} | Ativos: {activeBots} | Em Risco: {riskBots}</div>
      
      {botsStatus.map(bot => {
        const badge = getBotStatusBadge(bot.botName);
        return (
          <div key={bot.botName}>
            <h3>{bot.botName}</h3>
            <span className={badge.class}>{badge.text}</span>
            <p>{bot.reason}</p>
          </div>
        );
      })}
    </div>
  );
}
```

### 5. Implementar Componente Completo

Use o arquivo `BotStatusCards.jsx` como exemplo completo de implementação.

## 🧪 Testes Realizados

O script `test_realtime_status.py` foi executado com sucesso, confirmando:

✅ **Conexão com Supabase**: OK  
✅ **Estrutura da tabela**: OK  
✅ **UPSERT Scalping Bot**: OK  
✅ **UPSERT Tunder Bot**: OK  
✅ **Atualizações sequenciais**: OK  

## 📈 Fluxo de Funcionamento

1. **Backend Python** executa análises dos bots
2. **UPSERT** atualiza/insere dados na tabela usando `bot_name` como chave única
3. **Supabase Realtime** detecta mudanças na tabela
4. **Frontend Hook** recebe eventos via subscription
5. **Estado local** é atualizado automaticamente
6. **Interface** reflete mudanças instantaneamente

## 🔄 Eventos Suportados

O sistema escuta os seguintes eventos do Supabase:

- **INSERT**: Novo bot adicionado
- **UPDATE**: Status de bot existente atualizado
- **DELETE**: Bot removido (opcional)

## 🎨 Customização dos Cards

### Badges de Status
- **ATIVO** (Verde): `is_safe_to_operate = true`
- **RIESGO** (Vermelho): `is_safe_to_operate = false`
- **DESCONHECIDO** (Cinza): Bot não encontrado

### Informações Exibidas
- Nome do bot
- Status de segurança (badge)
- Mensagem de status (`reason`)
- Operações após padrão
- Timestamp da última atualização
- Campos específicos do Tunder Bot (quando aplicável)

## 🔧 Configurações Avançadas

### Limitar Eventos por Segundo
```javascript
realtime: {
  params: {
    eventsPerSecond: 10, // Máximo 10 eventos por segundo
  },
}
```

### Filtrar por Bot Específico
```javascript
supabase
  .channel('bot-specific')
  .on(
    'postgres_changes',
    {
      event: '*',
      schema: 'public',
      table: 'radar_de_apalancamiento_signals',
      filter: 'bot_name=eq.Tunder Bot' // Apenas Tunder Bot
    },
    handleChange
  )
  .subscribe();
```

## 🚨 Troubleshooting

### Problema: Subscription não conecta
**Solução**: Verificar se o Realtime está habilitado no Supabase Dashboard

### Problema: Eventos não chegam
**Solução**: Verificar se a tabela tem Row Level Security (RLS) configurada corretamente

### Problema: Muitos eventos
**Solução**: Implementar debounce ou limitar `eventsPerSecond`

### Problema: Dados não atualizando
**Solução**: Verificar se o backend está usando UPSERT corretamente

## 📝 Logs de Debug

O sistema inclui logs detalhados:

```javascript
console.log('[Realtime] Evento recebido:', eventType, newRecord);
console.log('[Realtime] Status da subscription:', status);
console.log('[Realtime] Buscando dados iniciais...');
```

## 🔐 Segurança

- Use variáveis de ambiente para credenciais
- Configure RLS no Supabase se necessário
- Limite rate de eventos para evitar spam
- Valide dados recebidos antes de processar

## 📚 Recursos Adicionais

- [Documentação Supabase Realtime](https://supabase.com/docs/guides/realtime)
- [React Hooks Best Practices](https://reactjs.org/docs/hooks-rules.html)
- [PostgreSQL UPSERT](https://www.postgresql.org/docs/current/sql-insert.html)

## 🎉 Resultado Final

Com este sistema implementado, você terá:

- ✅ Status dos bots atualizando **instantaneamente**
- ✅ **Sem necessidade** de refresh manual
- ✅ **Sem polling** desnecessário
- ✅ Interface **responsiva** e moderna
- ✅ Sistema **escalável** e **confiável**

---

**Desenvolvido para Million Bots - Sistema de Trading Automatizado**