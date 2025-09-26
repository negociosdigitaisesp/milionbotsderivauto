import dotenv from 'dotenv';
import { createClient } from '@supabase/supabase-js';
import fs from 'fs';

dotenv.config();

// Configurar cliente Supabase
const supabaseUrl = process.env.SUPABASE_URL || process.env.NEXT_PUBLIC_SUPABASE_URL;
const supabaseKey = process.env.SUPABASE_ANON_KEY || process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY;

if (!supabaseUrl || !supabaseKey) {
    console.error('❌ Erro: Variáveis SUPABASE_URL e SUPABASE_ANON_KEY não encontradas no .env');
    process.exit(1);
}

const supabase = createClient(supabaseUrl, supabaseKey);

/**
 * Converte array de objetos para formato CSV
 * @param {Array} data - Array de objetos para converter
 * @returns {string} - String CSV formatada
 */
function converterParaCSV(data) {
    if (!data || data.length === 0) {
        return '';
    }

    // Obter headers das chaves do primeiro objeto
    const headers = Object.keys(data[0]);
    
    // Função para escapar valores CSV
    const escaparValor = (valor) => {
        if (valor === null || valor === undefined) {
            return '';
        }
        
        const valorStr = String(valor);
        
        // Se contém vírgula, quebra de linha ou aspas, precisa ser escapado
        if (valorStr.includes(',') || valorStr.includes('\n') || valorStr.includes('"')) {
            return `"${valorStr.replace(/"/g, '""')}"`;
        }
        
        return valorStr;
    };

    // Criar linha de headers
    const linhaHeaders = headers.map(header => escaparValor(header)).join(',');
    
    // Criar linhas de dados
    const linhasDados = data.map(row => {
        return headers.map(header => escaparValor(row[header])).join(',');
    });

    return [linhaHeaders, ...linhasDados].join('\n');
}

/**
 * Busca todos os registros da tabela operacoes onde nome_bot = 'DoubleCuentas'
 */
async function baixarDoubleCuentas() {
    try {
        console.log('🚀 Iniciando download dos dados DoubleCuentas...');
        
        console.log('✅ Registros DoubleCuentas confirmados! Iniciando download...');
        
        let todosOsDados = [];
        let ultimoId = 0;
        const tamanhoPagina = 10; // Começar muito pequeno
        let temMaisDados = true;
        let tentativa = 0;
        const maxTentativas = 3;
        
        while (temMaisDados) {
            console.log(`📥 Buscando registros a partir do ID ${ultimoId}...`);
            
            try {
                const { data, error } = await supabase
                    .from('operacoes')
                    .select('id, nome_bot, lucro, timestamp, created_at')
                    .eq('nome_bot', 'DoubleCuentas')
                    .gt('id', ultimoId)
                    .order('id', { ascending: true })
                    .limit(10); // Muito pequeno para teste
                    
                if (error) {
                    throw new Error(`Erro ao buscar dados: ${error.message}`);
                }
                
                if (data && data.length > 0) {
                    todosOsDados = todosOsDados.concat(data);
                    ultimoId = data[data.length - 1].id; // Pegar o último ID para próxima consulta
                    console.log(`✅ ${data.length} registros obtidos. Total acumulado: ${todosOsDados.length}`);
                    
                    // Se obtivemos menos registros que o tamanho da página, chegamos ao fim
                    if (data.length < tamanhoPagina) {
                        temMaisDados = false;
                    }
                    
                    tentativa = 0; // Reset tentativas em caso de sucesso
                } else {
                    temMaisDados = false;
                }
                
            } catch (err) {
                tentativa++;
                console.log(`⚠️  Tentativa ${tentativa}/${maxTentativas} falhou: ${err.message}`);
                
                if (tentativa >= maxTentativas) {
                    throw err;
                }
                
                // Aguardar antes de tentar novamente
                console.log('⏳ Aguardando 2 segundos antes de tentar novamente...');
                await new Promise(resolve => setTimeout(resolve, 2000));
                continue;
            }
            
            // Pausa maior para não sobrecarregar a API
            await new Promise(resolve => setTimeout(resolve, 500));
        }
        
        console.log(`📊 Total de registros encontrados: ${todosOsDados.length}`);
        
        if (todosOsDados.length === 0) {
            console.log('⚠️  Nenhum registro encontrado para DoubleCuentas');
            return;
        }
        
        // Converter para CSV
        console.log('🔄 Convertendo dados para CSV...');
        const csvContent = converterParaCSV(todosOsDados);
        
        // Salvar arquivo
        const nomeArquivo = 'doublecuentas.csv';
        console.log(`💾 Salvando arquivo ${nomeArquivo}...`);
        
        fs.writeFileSync(nomeArquivo, csvContent, 'utf8');
        
        console.log(`🎉 Sucesso! Arquivo ${nomeArquivo} criado com ${todosOsDados.length} registros`);
        console.log(`📁 Localização: ${process.cwd()}\\${nomeArquivo}`);
        
    } catch (error) {
        console.error('❌ Erro durante o processo:', error.message);
        console.error('🔍 Detalhes do erro:', error);
        process.exit(1);
    }
}

// Executar a função
console.log('🎯 Iniciando script de download DoubleCuentas...');
baixarDoubleCuentas()
    .then(() => {
        console.log('✨ Script finalizado com sucesso!');
        process.exit(0);
    })
    .catch((error) => {
        console.error('💥 Erro fatal:', error);
        process.exit(1);
    });

export { baixarDoubleCuentas, converterParaCSV };