# Configuração da Integração Deriv

Este documento explica como configurar corretamente a integração com a API da Deriv.

## Variáveis de Ambiente

### Para Desenvolvimento Local

Adicione a seguinte variável ao seu arquivo `.env.local`:

```bash
VITE_DERIV_APP_ID=your_deriv_app_id
```

### Para Produção (Netlify/Vercel)

Configure a variável de ambiente no painel de controle da sua plataforma de deploy:

- **Nome**: `VITE_DERIV_APP_ID`
- **Valor**: Seu App ID da Deriv (ex: `qfbVc5YUYapY6S8`)

## Como Obter o App ID da Deriv

1. Acesse [Deriv API Dashboard](https://app.deriv.com/account/api-token)
2. Faça login na sua conta Deriv
3. Vá para "API Token" ou "Aplicações"
4. Crie uma nova aplicação ou use uma existente
5. Copie o App ID fornecido

## Verificação da Configuração

Para verificar se a variável está sendo lida corretamente:

1. Abra o console do navegador (F12)
2. Digite: `console.log(import.meta.env.VITE_DERIV_APP_ID)`
3. Deve retornar o seu App ID

## Problemas Comuns

### "A solicitação está faltando um app_id válido"

**Causa**: A variável de ambiente não está sendo lida corretamente.

**Soluções**:
1. Verifique se o nome da variável está correto: `VITE_DERIV_APP_ID`
2. Reinicie o servidor de desenvolvimento após adicionar a variável
3. Em produção, verifique se a variável foi configurada no painel de deploy
4. Certifique-se de que não há espaços extras no valor da variável

### Variável undefined em produção

**Causa**: Plataformas de deploy precisam que as variáveis sejam configuradas explicitamente.

**Soluções**:
1. Configure `VITE_DERIV_APP_ID` no painel da Netlify/Vercel
2. Faça um novo deploy após configurar a variável
3. Verifique se o prefixo `VITE_` está presente (obrigatório para Vite)

## Segurança

- O App ID da Deriv é público e pode ser exposto no frontend
- Nunca exponha tokens de acesso ou chaves privadas no frontend
- Use sempre HTTPS em produção para proteger as comunicações

## Framework Específico

Este projeto usa **Vite**, por isso:
- Prefixo obrigatório: `VITE_`
- Acesso no código: `import.meta.env.VITE_DERIV_APP_ID`
- Fallback implementado: Se a variável não existir, usa valor padrão