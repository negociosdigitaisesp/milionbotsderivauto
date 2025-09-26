import dotenv from 'dotenv';
import { createClient } from '@supabase/supabase-js';

dotenv.config();

// Configurar cliente Supabase
const supabaseUrl = process.env.SUPABASE_URL || process.env.NEXT_PUBLIC_SUPABASE_URL;
const supabaseKey = process.env.SUPABASE_ANON_KEY || process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY;

if (!supabaseUrl || !supabaseKey) {
    console.error('❌ Erro: Variáveis SUPABASE_URL e SUPABASE_ANON_KEY não encontradas no .env');
    process.exit(1);
}

const supabase = createClient(supabaseUrl, supabaseKey);

async function verificarTabelas() {
    try {
        console.log('🔍 Verificando tabelas disponíveis...');
        
        // Lista de possíveis nomes de tabelas
        const tabelasPossiveis = [
            'operacoes',
            'operations', 
            'trades',
            'bot_operations',
            'trading_operations',
            'logs',
            'bot_logs'
        ];
        
        for (const tabela of tabelasPossiveis) {
            try {
                console.log(`📋 Testando tabela: ${tabela}`);
                
                const { data, error } = await supabase
                    .from(tabela)
                    .select('*')
                    .limit(1);
                    
                if (!error && data !== null) {
                    console.log(`✅ Tabela '${tabela}' encontrada e acessível`);
                    
                    // Se encontrou dados, mostrar as colunas
                    if (data.length > 0) {
                        const colunas = Object.keys(data[0]);
                        console.log(`   📊 Colunas: ${colunas.join(', ')}`);
                        
                        // Verificar se tem coluna nome_bot
                        if (colunas.includes('nome_bot')) {
                            console.log('   🎯 Coluna nome_bot encontrada!');
                            
                            // Tentar buscar DoubleCuentas especificamente
                            const { data: botData, error: botError } = await supabase
                                .from(tabela)
                                .select('nome_bot')
                                .eq('nome_bot', 'DoubleCuentas')
                                .limit(1);
                                
                            if (!botError && botData && botData.length > 0) {
                                console.log('   🎉 Registros DoubleCuentas encontrados nesta tabela!');
                            } else {
                                console.log('   ⚠️  Nenhum registro DoubleCuentas nesta tabela');
                            }
                        }
                    } else {
                        console.log(`   📭 Tabela '${tabela}' está vazia`);
                    }
                } else {
                    console.log(`   ❌ Tabela '${tabela}' não acessível: ${error?.message || 'não encontrada'}`);
                }
                
            } catch (err) {
                console.log(`   💥 Erro ao testar tabela '${tabela}': ${err.message}`);
            }
            
            // Pequena pausa entre testes
            await new Promise(resolve => setTimeout(resolve, 200));
        }
        
        console.log('🏁 Verificação de tabelas concluída!');
        
    } catch (error) {
        console.error('💥 Erro durante verificação:', error.message);
        console.error('🔍 Detalhes:', error);
    }
}

// Executar verificação
console.log('🎯 Iniciando verificação de tabelas...');
verificarTabelas()
    .then(() => {
        console.log('✨ Verificação finalizada!');
        process.exit(0);
    })
    .catch((error) => {
        console.error('💥 Erro fatal:', error);
        process.exit(1);
    });