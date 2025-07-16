# 🚀 Guia de Deploy na Vercel - Bot Strategy Hub

## 📋 Variáveis de Ambiente Necessárias

Configure as seguintes variáveis de ambiente no painel da Vercel:

### 🔐 Supabase Configuration
```
VITE_SUPABASE_URL=https://xwclmxjeombwabfdvyij.supabase.co
VITE_SUPABASE_ANON_KEY=sb_publishable_3M1Xw1IMCQ6iWMvgKdXPTA_ad4tGlth
VITE_SUPABASE_DEBUG=false
```

### 🎯 Deriv API Configuration
```
VITE_DERIV_APP_ID=85515
VITE_DERIV_API_TOKEN=R9mD6PO5A1x7rz5
```

## 🛠️ Como Configurar na Vercel

### Método 1: Interface Web
1. Acesse o painel da Vercel: https://vercel.com/dashboard
2. Selecione seu projeto `bot-strategy-hub`
3. Vá para **Settings** → **Environment Variables**
4. Adicione cada variável uma por vez:
   - **Name**: `VITE_SUPABASE_URL`
   - **Value**: `https://xwclmxjeombwabfdvyij.supabase.co`
   - **Environment**: Selecione `Production`, `Preview`, e `Development`
   - Clique em **Save**
5. Repita para todas as variáveis listadas acima

### Método 2: Vercel CLI
```bash
# Instalar Vercel CLI (se não tiver)
npm i -g vercel

# Fazer login
vercel login

# Configurar variáveis
vercel env add VITE_SUPABASE_URL production
# Cole: https://xwclmxjeombwabfdvyij.supabase.co

vercel env add VITE_SUPABASE_ANON_KEY production
# Cole: sb_publishable_3M1Xw1IMCQ6iWMvgKdXPTA_ad4tGlth

vercel env add VITE_SUPABASE_DEBUG production
# Cole: false

vercel env add VITE_DERIV_APP_ID production
# Cole: 85515

vercel env add VITE_DERIV_API_TOKEN production
# Cole: R9mD6PO5A1x7rz5
```

## 🔄 Após Configurar as Variáveis

1. **Redeploy**: Faça um novo deploy para aplicar as variáveis
   ```bash
   vercel --prod
   ```

2. **Verificar**: Acesse sua aplicação e teste o botão "🔍 Teste de Depuração"

## ✅ Resultado Esperado no Teste

Após o deploy, o teste deve mostrar:
```
🔍 TESTE DE VARIÁVEL DE AMBIENTE:

VITE_DERIV_APP_ID: 85515
VITE_DERIV_API_TOKEN: R9mD6...
App ID Tipo: string
Token Tipo: string
App ID está vazio?: NÃO
Token está vazio?: NÃO
Todas as variáveis VITE encontradas: VITE_SUPABASE_URL, VITE_SUPABASE_ANON_KEY, VITE_SUPABASE_DEBUG, VITE_DERIV_APP_ID, VITE_DERIV_API_TOKEN
```

## 🔧 Configuração da Deriv

### URLs de Callback Autorizadas
No painel da Deriv (https://app.deriv.com/account/api-token), configure:

**Para Produção:**
- `https://seu-dominio.vercel.app/deriv/callback`

**Para Desenvolvimento:**
- `http://localhost:8081/deriv/callback`

### App ID: 85515
- ✅ Ativo
- ✅ URLs de callback configuradas
- ✅ Permissões: read, trade

## 🚨 Problemas Comuns

### 1. "app_id inválido"
- ✅ Verificar se `VITE_DERIV_APP_ID=85515` está configurado
- ✅ Fazer redeploy após adicionar variáveis

### 2. "Token não encontrado"
- ✅ Verificar se `VITE_DERIV_API_TOKEN=R9mD6PO5A1x7rz5` está configurado
- ✅ Verificar se o token está ativo no painel da Deriv

### 3. "Callback URL não autorizada"
- ✅ Adicionar URL de produção no painel da Deriv
- ✅ Verificar se a URL está exatamente igual

## 📞 Suporte

Se o problema persistir:
1. Verificar logs da Vercel
2. Testar localmente primeiro
3. Verificar configurações no painel da Deriv