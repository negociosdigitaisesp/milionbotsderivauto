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

async function testarConexao() {
    try {
        console.log('🔍 Testando conexão com Supabase...');
        
        // Teste 1: Verificar se a tabela operacoes existe
        console.log('📋 Verificando tabela operacoes...');
        const { data: tableTest, error: tableError } = await supabase
            .from('operacoes')
            .select('count')
            .limit(1);
            
        if (tableError) {
            console.error('❌ Erro ao acessar tabela operacoes:', tableError.message);
            return;
        }
        
        console.log('✅ Tabela operacoes acessível');
        
        // Teste 2: Verificar registros DoubleCuentas
        console.log('🔍 Verificando registros DoubleCuentas...');
        const { data: countData, error: countError } = await supabase
            .from('operacoes')
            .select('id', { count: 'exact', head: true })
            .eq('nome_bot', 'DoubleCuentas');
            
        if (countError) {
            console.error('❌ Erro ao contar registros DoubleCuentas:', countError.message);
            return;
        }
        
        console.log('✅ Consulta DoubleCuentas executada com sucesso');
        
        // Teste 3: Buscar alguns registros de exemplo
        console.log('📥 Buscando 5 registros de exemplo...');
        const { data: sampleData, error: sampleError } = await supabase
            .from('operacoes')
            .select('id, nome_bot, created_at')
            .eq('nome_bot', 'DoubleCuentas')
            .limit(5);
            
        if (sampleError) {
            console.error('❌ Erro ao buscar registros de exemplo:', sampleError.message);
            return;
        }
        
        if (sampleData && sampleData.length > 0) {
            console.log(`✅ Encontrados ${sampleData.length} registros de exemplo:`);
            sampleData.forEach((record, index) => {
                console.log(`   ${index + 1}. ID: ${record.id}, Bot: ${record.nome_bot}, Data: ${record.created_at}`);
            });
        } else {
            console.log('⚠️  Nenhum registro DoubleCuentas encontrado');
        }
        
        console.log('🎉 Teste de conexão concluído com sucesso!');
        
    } catch (error) {
        console.error('💥 Erro durante o teste:', error.message);
        console.error('🔍 Detalhes:', error);
    }
}

// Executar teste
console.log('🎯 Iniciando teste de conexão Supabase...');
testarConexao()
    .then(() => {
        console.log('✨ Teste finalizado!');
        process.exit(0);
    })
    .catch((error) => {
        console.error('💥 Erro fatal no teste:', error);
        process.exit(1);
    });