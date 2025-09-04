import pytest
from unittest.mock import AsyncMock, MagicMock

# Constante GROWTH_RATE como float entre 0.01 e 0.05
GROWTH_RATE = 0.02

def build_accu_parameters(symbol, amount, take_profit=None):
    """
    Constrói parâmetros para contratos ACCUMULATOR (ACCU) da Deriv API.
    
    Args:
        symbol (str): Símbolo do ativo (ex: 'R_100')
        amount (float): Valor da aposta
        take_profit (float, optional): Valor de take profit
    
    Returns:
        dict: Parâmetros formatados para a API Deriv
    """
    params = {
        "buy": 1,
        "price": 100000,
        "parameters": {
            "contract_type": "ACCU",
            "symbol": symbol,
            "currency": "USD",
            "amount": amount,
            "basis": "stake",
            "growth_rate": GROWTH_RATE,
        }
    }
    
    if take_profit is not None:
        params["parameters"]["limit_order"] = {"take_profit": take_profit}
    
    return params

def validate_growth_rate(growth_rate):
    """
    Valida se o growth_rate está no intervalo correto.
    
    Args:
        growth_rate (float): Valor do growth_rate
    
    Returns:
        bool: True se válido, False caso contrário
    """
    return isinstance(growth_rate, float) and 0.01 <= growth_rate <= 0.05

# Mock da biblioteca deriv_api para testes
class DerivSocket:
    """Mock da classe DerivSocket para testes."""
    
    def __init__(self):
        self.connected = True
    
    async def send(self, request):
        """Mock do método send."""
        # Simula resposta da API
        if "proposal" in request:
            return {
                "proposal": {
                    "id": "12345",
                    "ask_price": 100000,
                    "display_value": "100.00 USD"
                }
            }
        elif "buy" in request:
            return {
                "buy": {
                    "contract_id": "67890",
                    "longcode": "Accumulator contract",
                    "transaction_id": "98765"
                }
            }
        else:
            return {"error": "Invalid request"}