# 🔍 Teste de Depuração Visual - Deriv App ID

## Objetivo
Verificar se a variável de ambiente `VITE_DERIV_APP_ID` está sendo lida corretamente no frontend.

## Como Executar o Teste

### Passo 1: Acesse a Aplicação
1. Abra a aplicação em: http://localhost:8081/
2. Faça login na aplicação
3. Navegue para: **Integração Deriv** (no menu lateral)

### Passo 2: Execute o Teste

#### **MÉTODO 1: Botão de Teste Seguro (RECOMENDADO)**
1. Na página "Integração Deriv", procure pela seção **"🔍 Teste de Depuração"** (caixa amarela)
2. Clique no botão **"Testar Variável"**
3. Um alert aparecerá com todas as informações da variável

#### **MÉTODO 2: Botão de Conexão (Teste Original)**
1. Clique no botão **"Conectar com Deriv"**
2. **IMPORTANTE**: NÃO feche os alerts que aparecerão!

### Passo 3: Analise os Resultados

#### ✅ **RESULTADO ESPERADO (Sucesso)**

**Método 1 - Botão de Teste Seguro:**
```
🔍 TESTE DE VARIÁVEL DE AMBIENTE:

VITE_DERIV_APP_ID: qfbVc5YUYapY6S8
Tipo: string
Está vazio?: NÃO
Todas as variáveis VITE encontradas: VITE_SUPABASE_URL, VITE_SUPABASE_ANON_KEY, VITE_DERIV_APP_ID
```

**Método 2 - Botão de Conexão:**
```
Alert 1: "O App ID que será usado é: qfbVc5YUYapY6S8"
Alert 2: "URL que será usada: https://oauth.deriv.com/oauth2/authorize?app_id=qfbVc5YUYapY6S8&..."
```

**Diagnóstico**: ✅ A variável está sendo lida corretamente em desenvolvimento.
**Próximo passo**: Verificar configuração de produção.

#### ❌ **RESULTADO DE ERRO (Falha)**

**Método 1 - Botão de Teste Seguro:**
```
🔍 TESTE DE VARIÁVEL DE AMBIENTE:

VITE_DERIV_APP_ID: UNDEFINED
Tipo: undefined
Está vazio?: SIM
Todas as variáveis VITE encontradas: VITE_SUPABASE_URL, VITE_SUPABASE_ANON_KEY
```

**Método 2 - Botão de Conexão:**
```
Alert 1: "O App ID que será usado é: undefined"
OU
Alert 1: "O App ID que será usado é: "
OU
Alert 1: "ERRO: O app_id é nulo ou indefinido! Verifique o arquivo .env e o prefixo VITE_"
```

**Diagnóstico**: ❌ A variável NÃO está sendo lida em desenvolvimento.

### Passo 4: Verificações Adicionais

#### Console do Navegador
1. Abra o console (F12)
2. Procure por mensagens que começam com "🔍 DEPURAÇÃO"
3. Verifique os valores mostrados

#### Verificação Manual da Variável
No console do navegador, digite **UMA LINHA POR VEZ**:

**Linha 1:**
```javascript
console.log('Variável direta:', import.meta.env.VITE_DERIV_APP_ID)
```

**Linha 2:**
```javascript
console.log('Todas as variáveis VITE:', import.meta.env)
```

**⚠️ IMPORTANTE**: 
- Digite uma linha por vez e pressione Enter
- NÃO copie e cole múltiplas linhas de uma vez
- Remova as aspas se aparecerem automaticamente

## Soluções para Problemas Comuns

### Se o App ID aparecer como "undefined"

1. **Verificar arquivo .env.local**:
   ```bash
   # Deve estar na raiz do projeto: D:/milions1407/bot-strategy-hub/.env.local
   VITE_DERIV_APP_ID=qfbVc5YUYapY6S8
   ```

2. **Verificar nome da variável**:
   - ✅ Correto: `VITE_DERIV_APP_ID`
   - ❌ Errado: `DERIV_APP_ID`, `REACT_APP_DERIV_APP_ID`

3. **Reiniciar servidor**:
   ```bash
   # Parar o servidor (Ctrl+C) e reiniciar
   npm run dev
   ```

4. **Verificar localização do arquivo**:
   - ✅ Correto: `/bot-strategy-hub/.env.local`
   - ❌ Errado: `/bot-strategy-hub/src/.env.local`

### Se o App ID aparecer correto mas ainda der erro na Deriv

1. **Verificar URL de callback**:
   - Desenvolvimento: `http://localhost:8081/deriv/callback`
   - Produção: `https://millionbots.site/deriv/callback`

2. **Verificar configuração no painel da Deriv**:
   - App ID deve estar ativo
   - URLs de callback devem estar autorizadas

## Próximos Passos

### Se o teste PASSOU em desenvolvimento:
- Configurar a mesma variável no ambiente de produção (Netlify/Vercel)
- Fazer deploy e testar em produção

### Se o teste FALHOU em desenvolvimento:
- Corrigir a configuração local primeiro
- Repetir o teste até funcionar
- Só então configurar produção

## Remover Depuração

Após identificar e corrigir o problema, remover as linhas de alert do código:
- `src/pages/DerivIntegration.tsx` (função handleConnect)
- `src/services/derivApiService.ts` (função generateAuthUrl)