#!/usr/bin/env python3
"""
Indicadores Técnicos para Estratégia RESET CALL/PUT
===================================================

Este módulo implementa os indicadores técnicos necessários para a estratégia:
- SMA (Simple Moving Average): 5, 12, 40, 50 períodos
- RSI (Relative Strength Index): 3, 7, 10 períodos

Baseado na análise técnica do bot XML alvo.
"""

import logging
from typing import List, Dict, Optional
from collections import deque
import numpy as np

logger = logging.getLogger(__name__)

class TechnicalIndicators:
    """Classe para cálculo de indicadores técnicos em tempo real"""
    
    def __init__(self):
        """Inicializa os buffers para os indicadores"""
        # Buffer principal de preços (mantém até 100 valores para cálculos)
        self.price_buffer = deque(maxlen=100)
        
        # Configurações dos indicadores
        self.sma_periods = [5, 12, 40, 50]
        self.rsi_periods = [3, 7, 10]
        
        # Buffers para RSI (armazenar ganhos e perdas)
        self.rsi_buffers = {}
        for period in self.rsi_periods:
            self.rsi_buffers[period] = {
                'gains': deque(maxlen=period),
                'losses': deque(maxlen=period),
                'last_price': None
            }
    
    def add_price(self, price: float) -> None:
        """Adiciona novo preço ao buffer"""
        if price <= 0:
            logger.warning(f"⚠️ Preço inválido ignorado: {price}")
            return
            
        self.price_buffer.append(price)
        self._update_rsi_buffers(price)
        
        logger.debug(f"📊 Preço adicionado: {price:.5f} (Buffer: {len(self.price_buffer)} valores)")
    
    def _update_rsi_buffers(self, current_price: float) -> None:
        """Atualiza buffers específicos do RSI"""
        for period in self.rsi_periods:
            buffer = self.rsi_buffers[period]
            
            if buffer['last_price'] is not None:
                change = current_price - buffer['last_price']
                
                if change > 0:
                    buffer['gains'].append(change)
                    buffer['losses'].append(0)
                elif change < 0:
                    buffer['gains'].append(0)
                    buffer['losses'].append(abs(change))
                else:
                    buffer['gains'].append(0)
                    buffer['losses'].append(0)
            
            buffer['last_price'] = current_price
    
    def calculate_sma(self, period: int) -> Optional[float]:
        """Calcula Simple Moving Average para o período especificado"""
        if len(self.price_buffer) < period:
            return None
        
        # Pegar os últimos 'period' valores
        recent_prices = list(self.price_buffer)[-period:]
        sma = sum(recent_prices) / len(recent_prices)
        
        logger.debug(f"📈 SMA({period}): {sma:.5f}")
        return sma
    
    def calculate_rsi(self, period: int) -> Optional[float]:
        """Calcula Relative Strength Index para o período especificado"""
        if period not in self.rsi_buffers:
            logger.error(f"❌ Período RSI não configurado: {period}")
            return None
        
        buffer = self.rsi_buffers[period]
        
        if len(buffer['gains']) < period:
            return None
        
        # Calcular médias de ganhos e perdas
        avg_gain = sum(buffer['gains']) / len(buffer['gains'])
        avg_loss = sum(buffer['losses']) / len(buffer['losses'])
        
        # Evitar divisão por zero
        if avg_loss == 0:
            rsi = 100.0
        else:
            rs = avg_gain / avg_loss
            rsi = 100 - (100 / (1 + rs))
        
        logger.debug(f"📊 RSI({period}): {rsi:.2f}")
        return rsi
    
    def get_all_indicators(self) -> Dict[str, Optional[float]]:
        """Retorna todos os indicadores calculados"""
        indicators = {}
        
        # Calcular todas as SMAs
        for period in self.sma_periods:
            indicators[f'sma_{period}'] = self.calculate_sma(period)
        
        # Calcular todos os RSIs
        for period in self.rsi_periods:
            indicators[f'rsi_{period}'] = self.calculate_rsi(period)
        
        return indicators
    
    def get_signal_analysis(self) -> Dict[str, any]:
        """
        Análise completa dos sinais baseada nos indicadores
        Retorna recomendação de CALL/PUT baseada na estratégia XML
        """
        indicators = self.get_all_indicators()
        
        # Verificar se temos indicadores suficientes
        valid_indicators = {k: v for k, v in indicators.items() if v is not None}
        
        if len(valid_indicators) < 4:  # Precisamos de pelo menos alguns indicadores
            return {
                'signal': 'WAIT',
                'confidence': 0.0,
                'reason': 'Indicadores insuficientes',
                'indicators': indicators
            }
        
        # Análise de tendência baseada nas SMAs
        sma_signals = self._analyze_sma_trend(indicators)
        
        # Análise de momentum baseada nos RSIs
        rsi_signals = self._analyze_rsi_momentum(indicators)
        
        # Combinar sinais para decisão final
        final_signal = self._combine_signals(sma_signals, rsi_signals)
        
        return {
            'signal': final_signal['signal'],
            'confidence': final_signal['confidence'],
            'reason': final_signal['reason'],
            'sma_analysis': sma_signals,
            'rsi_analysis': rsi_signals,
            'indicators': indicators
        }
    
    def _analyze_sma_trend(self, indicators: Dict[str, Optional[float]]) -> Dict[str, any]:
        """Analisa tendência baseada nas SMAs"""
        smas = {k: v for k, v in indicators.items() if k.startswith('sma_') and v is not None}
        
        if len(smas) < 2:
            return {'trend': 'NEUTRAL', 'strength': 0.0}
        
        # Ordenar SMAs por período
        sorted_smas = sorted(smas.items(), key=lambda x: int(x[0].split('_')[1]))
        
        # Verificar alinhamento das médias
        bullish_alignment = 0
        bearish_alignment = 0
        
        for i in range(len(sorted_smas) - 1):
            current_sma = sorted_smas[i][1]
            next_sma = sorted_smas[i + 1][1]
            
            if current_sma > next_sma:  # SMA menor > SMA maior = bullish
                bullish_alignment += 1
            elif current_sma < next_sma:  # SMA menor < SMA maior = bearish
                bearish_alignment += 1
        
        # Determinar tendência
        total_comparisons = len(sorted_smas) - 1
        if bullish_alignment > bearish_alignment:
            trend = 'BULLISH'
            strength = bullish_alignment / total_comparisons
        elif bearish_alignment > bullish_alignment:
            trend = 'BEARISH'
            strength = bearish_alignment / total_comparisons
        else:
            trend = 'NEUTRAL'
            strength = 0.5
        
        return {
            'trend': trend,
            'strength': strength,
            'bullish_signals': bullish_alignment,
            'bearish_signals': bearish_alignment
        }
    
    def _analyze_rsi_momentum(self, indicators: Dict[str, Optional[float]]) -> Dict[str, any]:
        """Analisa momentum baseado nos RSIs"""
        rsis = {k: v for k, v in indicators.items() if k.startswith('rsi_') and v is not None}
        
        if len(rsis) == 0:
            return {'momentum': 'NEUTRAL', 'strength': 0.0}
        
        # Analisar níveis de RSI
        oversold_signals = 0  # RSI < 30
        overbought_signals = 0  # RSI > 70
        neutral_signals = 0
        
        for rsi_name, rsi_value in rsis.items():
            if rsi_value < 30:
                oversold_signals += 1
            elif rsi_value > 70:
                overbought_signals += 1
            else:
                neutral_signals += 1
        
        total_rsis = len(rsis)
        
        # Determinar momentum
        if oversold_signals > overbought_signals:
            momentum = 'OVERSOLD'  # Sinal de compra (CALL)
            strength = oversold_signals / total_rsis
        elif overbought_signals > oversold_signals:
            momentum = 'OVERBOUGHT'  # Sinal de venda (PUT)
            strength = overbought_signals / total_rsis
        else:
            momentum = 'NEUTRAL'
            strength = neutral_signals / total_rsis
        
        return {
            'momentum': momentum,
            'strength': strength,
            'oversold_count': oversold_signals,
            'overbought_count': overbought_signals,
            'neutral_count': neutral_signals
        }
    
    def _combine_signals(self, sma_signals: Dict, rsi_signals: Dict) -> Dict[str, any]:
        """Combina sinais de SMA e RSI para decisão final"""
        
        # Lógica de combinação baseada na estratégia XML
        signal = 'WAIT'
        confidence = 0.0
        reason = 'Análise em andamento'
        
        sma_trend = sma_signals.get('trend', 'NEUTRAL')
        rsi_momentum = rsi_signals.get('momentum', 'NEUTRAL')
        
        # Sinais de CALL (compra)
        if sma_trend == 'BULLISH' and rsi_momentum == 'OVERSOLD':
            signal = 'CALL'
            confidence = (sma_signals.get('strength', 0) + rsi_signals.get('strength', 0)) / 2
            reason = 'Tendência bullish + RSI oversold'
        
        # Sinais de PUT (venda)
        elif sma_trend == 'BEARISH' and rsi_momentum == 'OVERBOUGHT':
            signal = 'PUT'
            confidence = (sma_signals.get('strength', 0) + rsi_signals.get('strength', 0)) / 2
            reason = 'Tendência bearish + RSI overbought'
        
        # Sinais moderados
        elif sma_trend == 'BULLISH' and rsi_momentum != 'OVERBOUGHT':
            signal = 'CALL'
            confidence = sma_signals.get('strength', 0) * 0.7
            reason = 'Tendência bullish dominante'
        
        elif sma_trend == 'BEARISH' and rsi_momentum != 'OVERSOLD':
            signal = 'PUT'
            confidence = sma_signals.get('strength', 0) * 0.7
            reason = 'Tendência bearish dominante'
        
        elif rsi_momentum == 'OVERSOLD' and sma_trend != 'BEARISH':
            signal = 'CALL'
            confidence = rsi_signals.get('strength', 0) * 0.6
            reason = 'RSI oversold dominante'
        
        elif rsi_momentum == 'OVERBOUGHT' and sma_trend != 'BULLISH':
            signal = 'PUT'
            confidence = rsi_signals.get('strength', 0) * 0.6
            reason = 'RSI overbought dominante'
        
        # Ajustar confiança (mínimo 0.3 para executar operação)
        confidence = max(0.0, min(1.0, confidence))
        
        return {
            'signal': signal,
            'confidence': confidence,
            'reason': reason
        }
    
    def is_ready_for_analysis(self) -> bool:
        """Verifica se temos dados suficientes para análise"""
        return len(self.price_buffer) >= max(self.sma_periods)
    
    def get_buffer_status(self) -> Dict[str, int]:
        """Retorna status dos buffers"""
        return {
            'price_buffer_size': len(self.price_buffer),
            'max_sma_period': max(self.sma_periods),
            'ready_for_analysis': self.is_ready_for_analysis()
        }