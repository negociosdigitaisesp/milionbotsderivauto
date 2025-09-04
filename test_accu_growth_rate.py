import pytest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock
from accu_parameters import build_accu_parameters, GROWTH_RATE, DerivSocket, validate_growth_rate

class TestAccuGrowthRate:
    """Testes unitários para validação do growth_rate em contratos ACCU."""
    
    def test_growth_rate_is_float(self):
        """Testa se GROWTH_RATE é do tipo float."""
        assert isinstance(GROWTH_RATE, float), f"GROWTH_RATE deve ser float, mas é {type(GROWTH_RATE)}"
    
    def test_growth_rate_within_range(self):
        """Testa se GROWTH_RATE está no intervalo aceitável (0.01 a 0.05)."""
        assert 0.01 <= GROWTH_RATE <= 0.05, f"GROWTH_RATE {GROWTH_RATE} deve estar entre 0.01 e 0.05"
    
    def test_build_accu_parameters_with_take_profit(self):
        """Testa build_accu_parameters com take_profit definido."""
        symbol = "R_100"
        amount = 10.0
        take_profit = 50.0
        
        params = build_accu_parameters(symbol, amount, take_profit)
        
        # Verificações estruturais
        assert "buy" in params
        assert "price" in params
        assert "parameters" in params
        
        # Verificações dos parâmetros ACCU
        accu_params = params["parameters"]
        assert accu_params["contract_type"] == "ACCU"
        assert accu_params["symbol"] == symbol
        assert accu_params["currency"] == "USD"
        assert accu_params["amount"] == amount
        assert accu_params["basis"] == "stake"
        
        # Verificação específica do growth_rate
        assert "growth_rate" in accu_params
        assert isinstance(accu_params["growth_rate"], float)
        assert 0.01 <= accu_params["growth_rate"] <= 0.05
        assert accu_params["growth_rate"] == GROWTH_RATE
        
        # Verificação do take_profit
        assert "limit_order" in accu_params
        assert accu_params["limit_order"]["take_profit"] == take_profit
    
    def test_build_accu_parameters_without_take_profit(self):
        """Testa build_accu_parameters sem take_profit (fallback)."""
        symbol = "R_50"
        amount = 25.0
        
        params = build_accu_parameters(symbol, amount)
        
        # Verificações estruturais
        assert "buy" in params
        assert "price" in params
        assert "parameters" in params
        
        # Verificações dos parâmetros ACCU
        accu_params = params["parameters"]
        assert accu_params["contract_type"] == "ACCU"
        assert accu_params["symbol"] == symbol
        assert accu_params["currency"] == "USD"
        assert accu_params["amount"] == amount
        assert accu_params["basis"] == "stake"
        
        # Verificação específica do growth_rate
        assert "growth_rate" in accu_params
        assert isinstance(accu_params["growth_rate"], float)
        assert 0.01 <= accu_params["growth_rate"] <= 0.05
        assert accu_params["growth_rate"] == GROWTH_RATE
        
        # Verificação da ausência de take_profit
        assert "limit_order" not in accu_params
    
    def test_validate_growth_rate_function(self):
        """Testa a função validate_growth_rate com diferentes valores."""
        # Valores válidos
        assert validate_growth_rate(0.01) == True
        assert validate_growth_rate(0.02) == True
        assert validate_growth_rate(0.03) == True
        assert validate_growth_rate(0.05) == True
        
        # Valores inválidos - fora do intervalo
        assert validate_growth_rate(0.009) == False
        assert validate_growth_rate(0.051) == False
        assert validate_growth_rate(0.1) == False
        
        # Valores inválidos - tipo incorreto
        assert validate_growth_rate(2) == False  # int
        assert validate_growth_rate("0.02") == False  # string
        assert validate_growth_rate(None) == False  # None
    
    @pytest.mark.asyncio
    async def test_proposal_call_with_take_profit(self):
        """Testa chamada de proposal com take_profit usando mock."""
        socket = DerivSocket()
        
        # Preparar parâmetros
        params = build_accu_parameters("R_100", 10, take_profit=50)
        
        # Simular chamada proposal
        proposal_request = {"proposal": 1, **params}
        response = await socket.send(proposal_request)
        
        # Verificações da resposta
        assert "proposal" in response
        assert "id" in response["proposal"]
        assert "ask_price" in response["proposal"]
        assert response["proposal"]["ask_price"] == 100000
    
    @pytest.mark.asyncio
    async def test_proposal_call_without_take_profit(self):
        """Testa chamada de proposal sem take_profit (fallback) usando mock."""
        socket = DerivSocket()
        
        # Preparar parâmetros
        params = build_accu_parameters("R_100", 10)
        
        # Simular chamada proposal
        proposal_request = {"proposal": 1, **params}
        response = await socket.send(proposal_request)
        
        # Verificações da resposta
        assert "proposal" in response
        assert "id" in response["proposal"]
        assert "ask_price" in response["proposal"]
        assert response["proposal"]["ask_price"] == 100000
    
    @pytest.mark.asyncio
    async def test_buy_call_with_take_profit(self):
        """Testa chamada de buy com take_profit usando mock."""
        socket = DerivSocket()
        
        # Preparar parâmetros
        params = build_accu_parameters("R_100", 10, take_profit=50)
        
        # Simular chamada buy
        buy_request = {"buy": "12345", "price": 100000}
        response = await socket.send(buy_request)
        
        # Verificações da resposta
        assert "buy" in response
        assert "contract_id" in response["buy"]
        assert "transaction_id" in response["buy"]
        assert response["buy"]["contract_id"] == "67890"
    
    @pytest.mark.asyncio
    async def test_buy_call_without_take_profit(self):
        """Testa chamada de buy sem take_profit (fallback) usando mock."""
        socket = DerivSocket()
        
        # Preparar parâmetros
        params = build_accu_parameters("R_100", 10)
        
        # Simular chamada buy
        buy_request = {"buy": "12345", "price": 100000}
        response = await socket.send(buy_request)
        
        # Verificações da resposta
        assert "buy" in response
        assert "contract_id" in response["buy"]
        assert "transaction_id" in response["buy"]
        assert response["buy"]["contract_id"] == "67890"
    
    @pytest.mark.asyncio
    async def test_complete_workflow_with_take_profit(self):
        """Testa workflow completo: proposal -> buy com take_profit."""
        socket = DerivSocket()
        
        # 1. Preparar parâmetros
        params = build_accu_parameters("R_100", 15, take_profit=75)
        
        # Verificar que growth_rate está correto nos parâmetros
        assert params["parameters"]["growth_rate"] == GROWTH_RATE
        assert isinstance(params["parameters"]["growth_rate"], float)
        
        # 2. Chamada proposal
        proposal_request = {"proposal": 1, **params}
        proposal_response = await socket.send(proposal_request)
        
        assert "proposal" in proposal_response
        proposal_id = proposal_response["proposal"]["id"]
        ask_price = proposal_response["proposal"]["ask_price"]
        
        # 3. Chamada buy
        buy_request = {"buy": proposal_id, "price": ask_price}
        buy_response = await socket.send(buy_request)
        
        assert "buy" in buy_response
        assert "contract_id" in buy_response["buy"]
        assert "transaction_id" in buy_response["buy"]
    
    @pytest.mark.asyncio
    async def test_complete_workflow_without_take_profit(self):
        """Testa workflow completo: proposal -> buy sem take_profit (fallback)."""
        socket = DerivSocket()
        
        # 1. Preparar parâmetros
        params = build_accu_parameters("R_50", 20)
        
        # Verificar que growth_rate está correto nos parâmetros
        assert params["parameters"]["growth_rate"] == GROWTH_RATE
        assert isinstance(params["parameters"]["growth_rate"], float)
        
        # 2. Chamada proposal
        proposal_request = {"proposal": 1, **params}
        proposal_response = await socket.send(proposal_request)
        
        assert "proposal" in proposal_response
        proposal_id = proposal_response["proposal"]["id"]
        ask_price = proposal_response["proposal"]["ask_price"]
        
        # 3. Chamada buy
        buy_request = {"buy": proposal_id, "price": ask_price}
        buy_response = await socket.send(buy_request)
        
        assert "buy" in buy_response
        assert "contract_id" in buy_response["buy"]
        assert "transaction_id" in buy_response["buy"]

if __name__ == "__main__":
    # Executar testes diretamente
    pytest.main(["-v", __file__])