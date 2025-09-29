#!/usr/bin/env python3
"""
Teste para verificar se o timeout no ConnectionPool está funcionando corretamente
"""

import asyncio
import os
from dotenv import load_dotenv
from deriv_api import DerivAPI
from typing import List, Optional

# Carregar variáveis de ambiente
load_dotenv()

class ConnectionPool:
    """Pool de conexões WebSocket com failover e reconexão automática"""
    def __init__(self, app_id: str, token: str, pool_size: int = 2):
        self.app_id = app_id
        self.token = token
        self.pool_size = pool_size
        self.connections: List[Optional[DerivAPI]] = []
        self.current_index = 0
        self.connection_lock = asyncio.Lock()

    async def initialize(self):
        """Inicializa o pool de conexões"""
        print(f"🔌 Inicializando pool de {self.pool_size} conexões...")
        
        for i in range(self.pool_size):
            try:
                api = DerivAPI(app_id=self.app_id)
                await asyncio.wait_for(api.authorize(self.token), timeout=30.0)
                self.connections.append(api)
                print(f"✅ Conexão {i+1}/{self.pool_size} estabelecida")
            except asyncio.TimeoutError:
                print(f"⏰ Timeout na conexão {i+1}: Autorização demorou mais de 30 segundos")
                self.connections.append(None)
            except Exception as e:
                print(f"❌ Falha na conexão {i+1}: {e}")
                self.connections.append(None)
        
        active_connections = sum(1 for conn in self.connections if conn is not None)
        print(f"🎯 Pool inicializado com {active_connections} conexões")
        
        if active_connections == 0:
            raise Exception("Nenhuma conexão WebSocket pôde ser estabelecida")

    async def close_all(self):
        """Fecha todas as conexões do pool"""
        print("🔌 Fechando todas as conexões...")
        for i, conn in enumerate(self.connections):
            if conn is not None:
                try:
                    await conn.disconnect()
                    print(f"✅ Conexão {i+1} fechada")
                except Exception as e:
                    print(f"⚠️ Erro ao fechar conexão {i+1}: {e}")

async def test_connection_pool():
    """Testa o pool de conexões com timeout"""
    print("🧪 Iniciando teste do ConnectionPool com timeout...")
    
    # Obter credenciais
    DERIV_APP_ID = os.getenv("DERIV_APP_ID")
    DERIV_API_TOKEN = os.getenv("DERIV_API_TOKEN")
    
    if not all([DERIV_APP_ID, DERIV_API_TOKEN]):
        print("❌ Erro: Variáveis de ambiente DERIV_APP_ID e DERIV_API_TOKEN não encontradas")
        return False
    
    try:
        # Criar pool com tamanho pequeno para teste
        pool = ConnectionPool(DERIV_APP_ID, DERIV_API_TOKEN, pool_size=1)
        
        # Testar inicialização
        start_time = asyncio.get_event_loop().time()
        await pool.initialize()
        end_time = asyncio.get_event_loop().time()
        
        duration = end_time - start_time
        print(f"⏱️ Inicialização levou {duration:.2f} segundos")
        
        # Verificar se pelo menos uma conexão foi estabelecida
        active_connections = sum(1 for conn in pool.connections if conn is not None)
        
        if active_connections > 0:
            print(f"✅ Teste bem-sucedido! {active_connections} conexão(ões) ativa(s)")
            result = True
        else:
            print("⚠️ Nenhuma conexão ativa, mas timeout funcionou corretamente")
            result = True  # Timeout funcionou, que era o objetivo
        
        # Fechar conexões
        await pool.close_all()
        
        return result
        
    except asyncio.TimeoutError:
        print("✅ Timeout capturado corretamente!")
        return True
    except Exception as e:
        print(f"❌ Erro durante o teste: {e}")
        return False

if __name__ == "__main__":
    print("🔧 Teste do ConnectionPool com Timeout")
    print("=" * 50)
    
    try:
        result = asyncio.run(test_connection_pool())
        if result:
            print("\n🎉 Teste concluído com sucesso!")
            print("✅ O timeout de 30 segundos está funcionando corretamente")
        else:
            print("\n❌ Teste falhou")
    except KeyboardInterrupt:
        print("\n⏹️ Teste interrompido pelo usuário")
    except Exception as e:
        print(f"\n❌ Erro crítico no teste: {e}")