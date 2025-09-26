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

async function verificarNomesBots() {
    try {
        console.log('🔍 Verificando nomes de bots disponíveis...');
        
        // Tentar buscar alguns registros sem filtro primeiro
        console.log('📋 Buscando primeiros 10 registros da tabela...');
        const { data: sampleData, error: sampleError } = await supabase
            .from('operacoes')
            .select('id, nome_bot')
            .limit(10);
            
        if (sampleError) {
            console.error('❌ Erro ao buscar registros de exemplo:', sampleError.message);
            return;
        }
        
        if (sampleData && sampleData.length > 0) {
            console.log('✅ Registros encontrados:');
            sampleData.forEach((record, index) => {
                console.log(`   ${index + 1}. ID: ${record.id}, Bot: '${record.nome_bot}'`);
            });
            
            // Verificar se algum contém 'Double'
            const doubleRecords = sampleData.filter(r => 
                r.nome_bot && r.nome_bot.toLowerCase().includes('double')
            );
            
            if (doubleRecords.length > 0) {
                console.log('🎯 Registros com "Double" encontrados:');
                doubleRecords.forEach(record => {
                    console.log(`   - ID: ${record.id}, Bot: '${record.nome_bot}'`);
                });
            } else {
                console.log('⚠️  Nenhum registro com "Double" nos primeiros 10');
            }
            
        } else {
            console.log('📭 Nenhum registro encontrado na tabela');
            return;
        }
        
        // Tentar buscar nomes únicos (com limite)
        console.log('\n🔍 Tentando buscar nomes de bots únicos...');
        try {
            const { data: uniqueData, error: uniqueError } = await supabase
                .from('operacoes')
                .select('nome_bot')
                .not('nome_bot', 'is', null)
                .limit(100);
                
            if (!uniqueError && uniqueData) {
                const uniqueNames = [...new Set(uniqueData.map(r => r.nome_bot))];
                console.log(`✅ Encontrados ${uniqueNames.length} nomes únicos de bots:`);
                uniqueNames.forEach((name, index) => {
                    console.log(`   ${index + 1}. '${name}'`);
                });
                
                // Verificar se DoubleCuentas está na lista
                const doubleCuentasExists = uniqueNames.includes('DoubleCuentas');
                console.log(`\n🎯 'DoubleCuentas' existe? ${doubleCuentasExists ? '✅ SIM' : '❌ NÃO'}`);
                
                // Buscar variações
                const variations = uniqueNames.filter(name => 
                    name.toLowerCase().includes('double') || 
                    name.toLowerCase().includes('cuenta')
                );
                
                if (variations.length > 0) {
                    console.log('🔍 Variações encontradas:');
                    variations.forEach(name => {
                        console.log(`   - '${name}'`);
                    });
                }
                
            } else {
                console.log('⚠️  Não foi possível buscar nomes únicos:', uniqueError?.message);
            }
        } catch (err) {
            console.log('⚠️  Erro ao buscar nomes únicos:', err.message);
        }
        
        console.log('\n🏁 Verificação concluída!');
        
    } catch (error) {
        console.error('💥 Erro durante verificação:', error.message);
        console.error('🔍 Detalhes:', error);
    }
}

// Executar verificação
console.log('🎯 Iniciando verificação de nomes de bots...');
verificarNomesBots()
    .then(() => {
        console.log('✨ Verificação finalizada!');
        process.exit(0);
    })
    .catch((error) => {
        console.error('💥 Erro fatal:', error);
        process.exit(1);
    });