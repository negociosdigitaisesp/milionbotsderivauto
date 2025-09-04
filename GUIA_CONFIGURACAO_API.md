# 🔧 Guia de Configuração da API da Deriv

## 📋 Status Atual

✅ **Sistema configurado**: O bot está pronto para funcionar  
❌ **Token inválido**: O token no arquivo `.env` precisa ser atualizado  
⚠️ **Supabase opcional**: Não é necessário para o funcionamento básico  

## 🚀 Como Obter um Token Válido da Deriv

### Passo 1: Acessar o Portal da Deriv
1. Abra seu navegador e vá para: **https://app.deriv.com/account/api-token**
2. Faça login na sua conta Deriv
3. Se não tiver conta, crie uma em: **https://deriv.com/**

### Passo 2: Criar um Token de API
1. Na página de tokens, clique em **"Create new token"**
2. Dê um nome para o token (ex: "Accumulator Bot")
3. Selecione as permissões necessárias:
   - ✅ **Read**: Para ler dados da conta
   - ✅ **Trade**: Para executar operações
   - ✅ **Trading information**: Para obter informações de trading
   - ✅ **Payments**: Para informações de pagamento
4. Clique em **"Create"**

### Passo 3: Copiar o Token
1. **IMPORTANTE**: Copie o token imediatamente após a criação
2. O token será exibido apenas uma vez
3. Se perder o token, você precisará criar um novo

### Passo 4: Configurar o Arquivo .env
1. Abra o arquivo `.env` no diretório do projeto
2. Substitua o valor do `DERIV_TOKEN` pelo seu token real:
   ```
   DERIV_TOKEN=seu_token_aqui_sem_espacos
   ```
3. Mantenha o `DERIV_APP_ID=1089` (padrão)
4. Salve o arquivo

## 🧪 Testar a Conexão

Após configurar o token, execute o teste:
```bash
python test_connection.py
```

Você deve ver:
```
✅ Conexão bem-sucedida!
👤 Usuário: CR1234567
💰 Moeda: USD
🏦 Saldo: 10000.00
```

## 🤖 Executar o Bot

Com o token configurado, execute o bot:
```bash
python accumulator_standalone.py
```

## 🔒 Segurança do Token

⚠️ **IMPORTANTE**: 
- Nunca compartilhe seu token de API
- Não commite o arquivo `.env` no Git
- Mantenha o token seguro
- Se suspeitar que foi comprometido, revogue e crie um novo

## 🆘 Solução de Problemas

### Token Inválido
- Verifique se copiou o token completo
- Certifique-se de que não há espaços extras
- Verifique se o token não expirou
- Tente criar um novo token

### Erro de Conexão
- Verifique sua conexão com a internet
- Tente usar uma VPN se estiver em região restrita
- Verifique se a conta Deriv está ativa

### Erro de Permissões
- Certifique-se de que o token tem permissões de Trade
- Verifique se a conta tem saldo suficiente
- Confirme que a conta permite trading de Accumulator

## 📞 Suporte

Se continuar com problemas:
1. Execute `python test_connection.py` e anote o erro
2. Verifique se sua conta Deriv está funcionando no site
3. Tente criar um novo token de API
4. Verifique se sua região permite trading automatizado

---

**✅ Após seguir este guia, seu bot estará pronto para operar!**