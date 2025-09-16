"""
Validador de Bot Name - Componente crítico para garantir consistência
"""
import re
import logging
from typing import Tuple

logger = logging.getLogger(__name__)

class BotNameValidator:
    """Validador rigoroso para nomes de bot"""
    
    # Configurações de validação
    MAX_LENGTH = 50
    MIN_LENGTH = 3
    ALLOWED_PATTERN = r'^[a-zA-Z0-9._-]+$'
    
    @classmethod
    def validate(cls, bot_name: str) -> Tuple[bool, str]:
        """
        Valida o nome do bot
        
        Args:
            bot_name: Nome do bot a ser validado
            
        Returns:
            Tuple[bool, str]: (is_valid, error_message)
        """
        # Verificação básica de tipo e existência
        if bot_name is None:
            return False, "Bot name não pode ser None"
        
        if not isinstance(bot_name, str):
            return False, f"Bot name deve ser string, recebido: {type(bot_name).__name__}"
        
        # Limpar espaços e verificar se fica vazio
        bot_name_clean = bot_name.strip()
        
        if len(bot_name_clean) == 0:
            return False, "Bot name não pode ser vazio após limpeza"
        
        # Verificar comprimento
        if len(bot_name_clean) < cls.MIN_LENGTH:
            return False, f"Bot name muito curto: {len(bot_name_clean)} < {cls.MIN_LENGTH}"
        
        if len(bot_name_clean) > cls.MAX_LENGTH:
            return False, f"Bot name muito longo: {len(bot_name_clean)} > {cls.MAX_LENGTH}"
        
        # Verificar caracteres permitidos
        if not re.match(cls.ALLOWED_PATTERN, bot_name_clean):
            invalid_chars = set(bot_name_clean) - set('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789._-')
            return False, f"Bot name contém caracteres inválidos: {invalid_chars}"
        
        # Verificações adicionais de segurança
        if bot_name_clean.startswith('.') or bot_name_clean.endswith('.'):
            return False, "Bot name não pode começar ou terminar com ponto"
        
        if '--' in bot_name_clean or '__' in bot_name_clean:
            return False, "Bot name não pode conter caracteres consecutivos (-- ou __)"
        
        return True, ""
    
    @classmethod
    def clean_and_validate(cls, bot_name: str) -> Tuple[bool, str, str]:
        """
        Limpa e valida o nome do bot
        
        Returns:
            Tuple[bool, str, str]: (is_valid, cleaned_name, error_message)
        """
        if bot_name is None:
            return False, "", "Bot name é None"
        
        if not isinstance(bot_name, str):
            return False, "", f"Bot name deve ser string"
        
        cleaned = bot_name.strip()
        is_valid, error = cls.validate(cleaned)
        
        return is_valid, cleaned, error

def test_validator():
    """Função de teste para validar o comportamento"""
    test_cases = [
        ("radartunder1.5", True),
        ("bot_name_123", True),
        ("test-bot.v2", True),
        ("", False),
        ("a", False),  # Muito curto
        ("a" * 60, False),  # Muito longo
        ("bot name", False),  # Espaço
        ("bot@name", False),  # Caractere inválido
        (".botname", False),  # Começa com ponto
        ("bot--name", False),  # Caracteres consecutivos
        (None, False),
        (123, False),
    ]
    
    print("=== TESTE DO VALIDADOR ===")
    for test_input, expected in test_cases:
        is_valid, error = BotNameValidator.validate(test_input)
        status = "✅" if is_valid == expected else "❌"
        print(f"{status} Input: {test_input} | Expected: {expected} | Got: {is_valid}")
        if not is_valid:
            print(f"    Error: {error}")
    print("=== FIM DOS TESTES ===")

if __name__ == "__main__":
    test_validator()