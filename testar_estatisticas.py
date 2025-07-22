#!/usr/bin/env python3
"""
Script para testar e exibir estatísticas dos bots de trading.
Conecta ao Supabase e busca dados da view estatisticas_bots.

Autor: Bot Trading System
Data: 2024
"""

import asyncio
import os
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv
from supabase import create_client, Client


class EstatisticasBotTester:
    """Classe para testar e exibir estatísticas dos bots de trading."""
    
    def __init__(self):
        """Inicializa o testador de estatísticas."""
        self.supabase: Optional[Client] = None
        self._carregar_credenciais()
        self._conectar_supabase()
    
    def _carregar_credenciais(self) -> None:
        """Carrega as credenciais do arquivo .env."""
        try:
            # Carrega variáveis de ambiente do arquivo .env
            load_dotenv()
            
            # Obtém as credenciais necessárias
            self.supabase_url = os.getenv('SUPABASE_URL')
            self.supabase_key = os.getenv('SUPABASE_KEY')
            
            # Valida se as credenciais foram carregadas
            if not self.supabase_url or not self.supabase_key:
                raise ValueError(
                    "❌ Credenciais do Supabase não encontradas!\n"
                    "Verifique se o arquivo .env contém SUPABASE_URL e SUPABASE_KEY"
                )
            
            print("✅ Credenciais carregadas com sucesso!")
            
        except Exception as e:
            print(f"❌ Erro ao carregar credenciais: {e}")
            raise
    
    def _conectar_supabase(self) -> None:
        """Conecta ao cliente Supabase."""
        try:
            # Inicializa o cliente Supabase
            self.supabase = create_client(self.supabase_url, self.supabase_key)
            print("✅ Conexão com Supabase estabelecida!")
            
        except Exception as e:
            print(f"❌ Erro ao conectar com Supabase: {e}")
            raise
    
    async def obter_estatisticas_completas(self) -> List[Dict[str, Any]]:
        """
        Função assíncrona para obter estatísticas completas dos bots.
        
        Returns:
            List[Dict[str, Any]]: Lista com dados dos bots ordenados por lucro total
        """
        try:
            print("🔍 Buscando estatísticas dos bots...")
            
            # Conecta à view estatisticas_bots e busca todos os dados
            response = self.supabase.table('estatisticas_bots')\
                .select('*')\
                .order('lucro_total', desc=True)\
                .execute()
            
            # Verifica se houve erro na consulta
            if hasattr(response, 'error') and response.error:
                raise Exception(f"Erro na consulta: {response.error}")
            
            # Obtém os dados da resposta
            dados = response.data if hasattr(response, 'data') else []
            
            print(f"✅ {len(dados)} registros encontrados!")
            return dados
            
        except Exception as e:
            print(f"❌ Erro ao obter estatísticas: {e}")
            return []
    
    def _formatar_moeda(self, valor: float) -> str:
        """Formata valor monetário com símbolo de dólar."""
        return f"${valor:.2f}"
    
    def _formatar_percentual(self, valor: float) -> str:
        """Formata valor percentual."""
        return f"{valor:.2f}%"
    
    def _imprimir_cabecalho(self) -> None:
        """Imprime cabeçalho do relatório."""
        print("\n" + "="*80)
        print("📊 RELATÓRIO DE ESTATÍSTICAS DOS BOTS DE TRADING")
        print("="*80)
        print(f"🕒 Gerado em: {asyncio.get_event_loop().time()}")
        print("="*80)
    
    def _imprimir_card_bot(self, bot: Dict[str, Any], posicao: int) -> None:
        """
        Imprime as estatísticas de um bot em formato de card.
        
        Args:
            bot (Dict[str, Any]): Dados do bot
            posicao (int): Posição no ranking
        """
        # Emojis para ranking
        emojis_ranking = {1: "🥇", 2: "🥈", 3: "🥉"}
        emoji = emojis_ranking.get(posicao, "🤖")
        
        # Determina cor do lucro
        lucro = float(bot.get('lucro_total', 0))
        status_lucro = "✅" if lucro >= 0 else "❌"
        
        print(f"\n{emoji} {posicao}. {bot.get('nome_bot', 'Bot Desconhecido')}")
        print("-" * 50)
        print(f"   💰 Lucro Total: {self._formatar_moeda(lucro)} {status_lucro}")
        print(f"   📊 Total de Operações: {bot.get('total_operacoes', 0)}")
        print(f"   ✅ Vitórias: {bot.get('vitorias', 0)}")
        print(f"   ❌ Derrotas: {bot.get('derrotas', 0)}")
        
        # Calcula e exibe taxa de assertividade
        taxa_assertividade = bot.get('taxa_vitoria', 0)
        if taxa_assertividade is None:
            # Calcula manualmente se não estiver na view
            total_ops = bot.get('total_operacoes', 0)
            vitorias = bot.get('vitorias', 0)
            taxa_assertividade = (vitorias / total_ops * 100) if total_ops > 0 else 0
        
        print(f"   📈 Taxa de Assertividade: {self._formatar_percentual(taxa_assertividade)}")
        
        # Informações adicionais se disponíveis
        if 'maior_lucro' in bot:
            print(f"   🏆 Maior Lucro: {self._formatar_moeda(bot['maior_lucro'])}")
        if 'maior_perda' in bot:
            print(f"   📉 Maior Perda: {self._formatar_moeda(bot['maior_perda'])}")
    
    def _imprimir_resumo(self, dados: List[Dict[str, Any]]) -> None:
        """Imprime resumo geral das estatísticas."""
        if not dados:
            return
        
        total_bots = len(dados)
        lucro_total_geral = sum(float(bot.get('lucro_total', 0)) for bot in dados)
        total_operacoes_geral = sum(int(bot.get('total_operacoes', 0)) for bot in dados)
        
        bots_lucrativos = sum(1 for bot in dados if float(bot.get('lucro_total', 0)) > 0)
        
        print("\n" + "="*80)
        print("📈 RESUMO GERAL")
        print("="*80)
        print(f"🤖 Total de Bots: {total_bots}")
        print(f"💰 Lucro Total Geral: {self._formatar_moeda(lucro_total_geral)}")
        print(f"📊 Total de Operações: {total_operacoes_geral}")
        print(f"✅ Bots Lucrativos: {bots_lucrativos}/{total_bots}")
        print(f"📈 Taxa de Bots Lucrativos: {self._formatar_percentual((bots_lucrativos/total_bots)*100 if total_bots > 0 else 0)}")
    
    async def main(self) -> None:
        """Função principal para executar o teste de estatísticas."""
        try:
            print("🚀 Iniciando teste de estatísticas dos bots...")
            
            # Obtém as estatísticas dos bots
            dados = await self.obter_estatisticas_completas()
            
            # Verifica se dados foram retornados
            if not dados:
                print("⚠️ Nenhuma estatística encontrada!")
                return
            
            # Imprime cabeçalho do relatório
            self._imprimir_cabecalho()
            
            # Faz loop através de cada bot e imprime suas estatísticas
            for posicao, bot in enumerate(dados, 1):
                self._imprimir_card_bot(bot, posicao)
            
            # Imprime resumo geral
            self._imprimir_resumo(dados)
            
            print("\n" + "="*80)
            print("✅ Teste de estatísticas concluído com sucesso!")
            print("="*80)
            
        except Exception as e:
            print(f"❌ Erro durante execução do teste: {e}")
            raise


# Função assíncrona standalone para compatibilidade
async def obter_estatisticas_completas() -> List[Dict[str, Any]]:
    """
    Função assíncrona standalone para obter estatísticas completas dos bots.
    
    Returns:
        List[Dict[str, Any]]: Lista com dados dos bots ordenados por lucro total
    """
    tester = EstatisticasBotTester()
    return await tester.obter_estatisticas_completas()


async def main() -> None:
    """Função principal assíncrona."""
    tester = EstatisticasBotTester()
    await tester.main()


# Ponto de entrada do script
if __name__ == "__main__":
    try:
        # Executa a função main com asyncio
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⚠️ Execução interrompida pelo usuário.")
    except Exception as e:
        print(f"\n❌ Erro fatal: {e}")
        exit(1)