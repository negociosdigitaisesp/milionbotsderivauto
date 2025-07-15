# API de Verificação de Status do Usuário

Este documento explica como usar a nova chamada de API `verificarStatusDoUsuario` para verificar o status de acesso do usuário.

## Configuração

### Informações do Projeto Supabase
- **Project URL:** `https://xwclmxjeombwabfdvyij.supabase.co`
- **Anon Key:** `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Inh3Y2xteGplb21id2FiZmR2eWlqIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTI1MjY0NTQsImV4cCI6MjA2ODEwMjQ1NH0.lB4EBPozpPUJS0oI5wpatJdo_HCTcuDRFmd42b_7i9U`

## Função: `verificarStatusDoUsuario`

### Parâmetros
- **`userId`** (string): ID do usuário autenticado
- **`authToken`** (string): Token de autenticação (JWT) do usuário

### Retorno
```typescript
{
  success: boolean;
  isActive: boolean;
  data?: any;
  error?: string;
}
```

### Exemplo de Uso

```typescript
import { verificarStatusDoUsuario } from '../services/verificarStatusDoUsuario';
import { supabase } from '../lib/supabaseClient';

async function verificarAcesso() {
  // 1. Obter usuário autenticado
  const { data: { user } } = await supabase.auth.getUser();
  if (!user) return;
  
  // 2. Obter token de acesso
  const { data: { session } } = await supabase.auth.getSession();
  if (!session?.access_token) return;
  
  // 3. Verificar status
  const resultado = await verificarStatusDoUsuario(user.id, session.access_token);
  
  if (resultado.success) {
    console.log('Usuário ativo:', resultado.isActive);
  } else {
    console.error('Erro:', resultado.error);
  }
}
```

## Detalhes da Chamada HTTP

### Método
`GET`

### URL
```
https://xwclmxjeombwabfdvyij.supabase.co/rest/v1/profiles?select=is_active&id=eq.{USER_ID}
```

### Headers
```
apikey: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Inh3Y2xteGplb21id2FiZmR2eWlqIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTI1MjY0NTQsImV4cCI6MjA2ODEwMjQ1NH0.lB4EBPozpPUJS0oI5wpatJdo_HCTcuDRFmd42b_7i9U
Authorization: Bearer {AUTH_TOKEN}
Content-Type: application/json
```

### Variáveis
- **`{USER_ID}`**: ID do usuário autenticado
- **`{AUTH_TOKEN}`**: Token JWT do usuário autenticado

## Alternativa com Cliente Supabase

Para uma implementação mais simples, use a função `verificarStatusDoUsuarioSupabase`:

```typescript
import { verificarStatusDoUsuarioSupabase } from '../services/verificarStatusDoUsuario';

async function verificarAcessoSimples() {
  const { data: { user } } = await supabase.auth.getUser();
  if (!user) return;
  
  const resultado = await verificarStatusDoUsuarioSupabase(user.id);
  
  if (resultado.success) {
    console.log('Usuário ativo:', resultado.isActive);
  }
}
```

## Tratamento de Erros

A função trata os seguintes cenários de erro:
- Usuário não encontrado
- Erro de autenticação
- Erro de rede
- Resposta inválida da API

## Integração com React

Veja o arquivo `exemploVerificacaoStatus.ts` para um exemplo de hook personalizado que pode ser usado em componentes React.

## Segurança

- A chave `anon` é segura para uso no frontend
- O token de autenticação é específico do usuário e tem tempo de expiração
- A API respeita as políticas RLS (Row Level Security) do Supabase

## Teste

Para testar a função no console do navegador:

```javascript
// Abra o console do navegador e execute:
import { exemploVerificacaoStatus } from './src/examples/exemploVerificacaoStatus';
exemploVerificacaoStatus();
```