#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Classe para representar uma execução de estratégia
"""
from datetime import datetime
from typing import Optional, Dict, Any
from dataclasses import dataclass

@dataclass
class StrategyExecution:
    """Representa uma execução de estratégia com validação rigorosa"""
    
    # Campos obrigatórios
    id: Optional[int] = None
    bot_name: str = ""
    strategy_name: str = ""
    confidence_level: float = 0.0
    trigger_type: str = ""
    
    # Timestamps
    pattern_detected_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    # Resultados das operações
    operation_1_result: Optional[str] = None
    operation_1_completed_at: Optional[datetime] = None
    operation_2_result: Optional[str] = None
    operation_2_completed_at: Optional[datetime] = None
    
    # Resultado final
    final_result: Optional[str] = None
    pattern_success: Optional[bool] = None
    
    # Controle de status
    status: str = "WAITING"
    completed_at: Optional[datetime] = None
    
    def __post_init__(self):
        """Validação após inicialização"""
        if not self.pattern_detected_at:
            self.pattern_detected_at = datetime.now()
        if not self.created_at:
            self.created_at = datetime.now()
        if not self.updated_at:
            self.updated_at = datetime.now()
    
    def validate(self) -> tuple[bool, str]:
        """Valida os dados da execução"""
        
        # Validar campos obrigatórios
        if not self.bot_name or not self.bot_name.strip():
            return False, "bot_name é obrigatório"
        
        if not self.strategy_name or not self.strategy_name.strip():
            return False, "strategy_name é obrigatório"
        
        if not isinstance(self.confidence_level, (int, float)):
            return False, "confidence_level deve ser numérico"
        
        if self.confidence_level <= 0 or self.confidence_level > 100:
            return False, "confidence_level deve estar entre 0 e 100"
        
        if not self.trigger_type or not self.trigger_type.strip():
            return False, "trigger_type é obrigatório"
        
        # Validar status
        valid_statuses = ["WAITING", "MONITORING", "COMPLETED", "TIMEOUT", "ERROR"]
        if self.status not in valid_statuses:
            return False, f"status deve ser um de: {valid_statuses}"
        
        # Validar resultados de operação
        if self.operation_1_result and self.operation_1_result not in ["WIN", "LOSS"]:
            return False, "operation_1_result deve ser 'WIN' ou 'LOSS'"
        
        if self.operation_2_result and self.operation_2_result not in ["WIN", "LOSS"]:
            return False, "operation_2_result deve ser 'WIN' ou 'LOSS'"
        
        # Validar resultado final
        if self.final_result and self.final_result not in ["WIN", "EMPATE", "LOSS"]:
            return False, "final_result deve ser 'WIN', 'EMPATE' ou 'LOSS'"
        
        return True, ""
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário para inserção no banco"""
        return {
            'bot_name': self.bot_name.strip(),
            'strategy_name': self.strategy_name.strip(),
            'confidence_level': float(self.confidence_level),
            'trigger_type': self.trigger_type.strip(),
            'pattern_detected_at': self.pattern_detected_at.isoformat() if self.pattern_detected_at else None,
            'operation_1_result': self.operation_1_result,
            'operation_1_completed_at': self.operation_1_completed_at.isoformat() if self.operation_1_completed_at else None,
            'operation_2_result': self.operation_2_result,
            'operation_2_completed_at': self.operation_2_completed_at.isoformat() if self.operation_2_completed_at else None,
            'final_result': self.final_result,
            'pattern_success': self.pattern_success,
            'status': self.status,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def calculate_final_result(self):
        """Calcula o resultado final baseado nas operações"""
        if not self.operation_1_result or not self.operation_2_result:
            return
        
        if self.operation_1_result == "WIN" and self.operation_2_result == "WIN":
            self.final_result = "WIN"
            self.pattern_success = True
        elif self.operation_1_result == "LOSS" and self.operation_2_result == "LOSS":
            self.final_result = "LOSS"
            self.pattern_success = False
        else:
            self.final_result = "EMPATE"
            self.pattern_success = False
        
        self.updated_at = datetime.now()
    
    def mark_completed(self):
        """Marca a execução como completada"""
        self.status = "COMPLETED"
        self.completed_at = datetime.now()
        self.updated_at = datetime.now()
    
    def mark_timeout(self):
        """Marca a execução como timeout"""
        self.status = "TIMEOUT"
        self.completed_at = datetime.now()
        self.updated_at = datetime.now()
    
    def mark_error(self):
        """Marca a execução como erro"""
        self.status = "ERROR"
        self.completed_at = datetime.now()
        self.updated_at = datetime.now()

def test_strategy_execution():
    """Teste da classe StrategyExecution"""
    print("=== TESTE DA STRATEGY EXECUTION ===")
    
    # Teste 1: Criação válida
    execution = StrategyExecution(
        bot_name="radartunder1.5",
        strategy_name="Quantum+",
        confidence_level=71.98,
        trigger_type="LLL"
    )
    
    is_valid, error_msg = execution.validate()
    print(f"Teste 1 - Criação válida: {'PASS' if is_valid else 'FAIL'}")
    if not is_valid:
        print(f"  Erro: {error_msg}")
    
    # Teste 2: Validação de campos obrigatórios
    invalid_execution = StrategyExecution()
    is_valid, error_msg = invalid_execution.validate()
    print(f"Teste 2 - Campos obrigatórios: {'PASS' if not is_valid else 'FAIL'}")
    print(f"  Erro esperado: {error_msg}")
    
    # Teste 3: Confidence level inválido
    invalid_confidence = StrategyExecution(
        bot_name="test",
        strategy_name="test",
        confidence_level=150,  # Inválido
        trigger_type="test"
    )
    is_valid, error_msg = invalid_confidence.validate()
    print(f"Teste 3 - Confidence inválido: {'PASS' if not is_valid else 'FAIL'}")
    print(f"  Erro esperado: {error_msg}")
    
    # Teste 4: Conversão para dicionário
    dict_data = execution.to_dict()
    print(f"Teste 4 - Conversão para dict: {'PASS' if isinstance(dict_data, dict) else 'FAIL'}")
    print(f"  Keys: {list(dict_data.keys())}")
    
    # Teste 5: Cálculo de resultado final
    execution.operation_1_result = "WIN"
    execution.operation_2_result = "WIN"
    execution.calculate_final_result()
    print(f"Teste 5 - Resultado WIN-WIN: {'PASS' if execution.final_result == 'WIN' and execution.pattern_success else 'FAIL'}")
    
    # Teste 6: Resultado EMPATE
    execution.operation_1_result = "WIN"
    execution.operation_2_result = "LOSS"
    execution.calculate_final_result()
    print(f"Teste 6 - Resultado WIN-LOSS (EMPATE): {'PASS' if execution.final_result == 'EMPATE' and not execution.pattern_success else 'FAIL'}")
    
    # Teste 7: Resultado LOSS
    execution.operation_1_result = "LOSS"
    execution.operation_2_result = "LOSS"
    execution.calculate_final_result()
    print(f"Teste 7 - Resultado LOSS-LOSS: {'PASS' if execution.final_result == 'LOSS' and not execution.pattern_success else 'FAIL'}")
    
    # Teste 8: Marcar como completado
    execution.mark_completed()
    print(f"Teste 8 - Marcar completado: {'PASS' if execution.status == 'COMPLETED' and execution.completed_at else 'FAIL'}")
    
    # Teste 9: Marcar timeout
    timeout_execution = StrategyExecution(
        bot_name="test",
        strategy_name="test",
        confidence_level=50,
        trigger_type="test"
    )
    timeout_execution.mark_timeout()
    print(f"Teste 9 - Marcar timeout: {'PASS' if timeout_execution.status == 'TIMEOUT' else 'FAIL'}")
    
    # Teste 10: Marcar erro
    error_execution = StrategyExecution(
        bot_name="test",
        strategy_name="test",
        confidence_level=50,
        trigger_type="test"
    )
    error_execution.mark_error()
    print(f"Teste 10 - Marcar erro: {'PASS' if error_execution.status == 'ERROR' else 'FAIL'}")
    
    print("\n=== RESUMO DOS TESTES ===")
    print("Todos os testes da StrategyExecution foram executados.")
    print("Classe pronta para integração com o sistema de trading.")

if __name__ == "__main__":
    test_strategy_execution()