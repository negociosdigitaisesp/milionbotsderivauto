# Deploy no Vercel - Configuração Python 3.12

## Configuração Implementada

### 1. Arquivos Criados/Atualizados

- **`vercel.json`**: Configuração principal do Vercel
- **`runtime.txt`**: Especifica Python 3.12
- **`index.py`**: Ponto de entrada da API
- **`requirements.txt`**: Atualizado com `setuptools>=65.0.0`
- **`.env.example`**: Atualizado com variáveis do backend

### 2. Configuração do vercel.json

```json
{
  "build": {
    "installCommand": "pip install --upgrade pip setuptools && pip install -r requirements.txt",
    "env": {
      "PIP_NO_BUILD_ISOLATION": "false"
    }
  },
  "builds": [
    {
      "src": "*.py",
      "use": "@vercel/python"
    }
  ],
  "routes": [
    {
      "src": "/(.*)",
      "dest": "/index.py"
    }
  ]
}
```

### 3. Variáveis de Ambiente Necessárias

Configure no painel do Vercel:

```bash
# Supabase (Backend)
SUPABASE_URL=https://xwclmxjeombwabfdvyij.supabase.co
SUPABASE_KEY=SUPABASE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Inh3Y2xteGplb21id2FiZmR2eWlqIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTI1MjY0NTQsImV4cCI6MjA2ODEwMjQ1NH0.lB4EBPozpPUJS0oI5wpatJdo_HCTcuDRFmd42b_7i9U


# Deriv API (Backend)
DERIV_APP_ID=85515
DERIV_API_TOKEN=R9mD6PO5A1x7rz5

# Frontend (se necessário)
VITE_SUPABASE_URL=https://xwclmxjeombwabfdvyij.supabase.co
VITE_SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Inh3Y2xteGplb21id2FiZmR2eWlqIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTI1MjY0NTQsImV4cCI6MjA2ODEwMjQ1NH0.lB4EBPozpPUJS0oI5wpatJdo_HCTcuDRFmd42b_7i9U
VITE_DERIV_APP_ID=85515
VITE_DERIV_API_TOKEN=R9mD6PO5A1x7rz5
```

### 4. Comandos para Deploy

1. **Conectar ao Vercel:**
   ```bash
   npm i -g vercel
   vercel login
   ```

2. **Deploy:**
   ```bash
   vercel --prod
   ```

### 5. Verificação do Deploy

Após o deploy, verifique:

1. **API Endpoint**: `https://your-project.vercel.app/`
2. **Logs**: Painel do Vercel > Functions > Logs
3. **Teste**: Faça uma requisição GET para verificar se retorna:
   ```json
   {
     "status": "success",
     "message": "Bot Strategy Hub API is running",
     "python_version": "3.12",
     "environment": "Vercel"
   }
   ```

### 6. Troubleshooting

Se houver problemas com `distutils`:

1. Verifique se `setuptools>=65.0.0` está no `requirements.txt`
2. Confirme que o comando de instalação está correto no `vercel.json`
3. Verifique os logs de build no painel do Vercel

### 7. Estrutura de Arquivos

```
bot-strategy-hub/
├── vercel.json          # Configuração do Vercel
├── runtime.txt          # Versão do Python
├── index.py             # Ponto de entrada da API
├── requirements.txt     # Dependências Python
├── bot_trading_system.py # Sistema principal de trading
├── .env.example         # Exemplo de variáveis de ambiente
└── src/                 # Frontend React
```

## Próximos Passos

1. Configure as variáveis de ambiente no painel do Vercel
2. Execute o deploy com `vercel --prod`
3. Teste a API para verificar se está funcionando
4. Monitore os logs para identificar possíveis problemas