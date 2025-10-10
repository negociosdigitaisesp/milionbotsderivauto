#!/usr/bin/env python3
"""
Technical Analysis Module for RESET CALL/PUT Strategy
Implementa análise técnica com SMA (5,12,40,50) + RSI (3,7,10) para sinais de entrada
"""

import logging
from typing import List, Optional, Dict, Any

logger = logging.getLogger(__name__)

class TechnicalAnalysis:
    """
    Classe para análise técnica com indicadores SMA e RSI
    Implementa lógica de sinais RESETCALL/RESETPUT conforme especificação
    """
    
    def __init__(self):
        """Inicializa o analisador técnico"""
        logger.info("🔧 TechnicalAnalysis inicializado")
    
    def calculate_sma(self, prices: List[float], period: int) -> Optional[float]:
        """
        Calcula Simple Moving Average (SMA)
        
        Args:
            prices: Lista de preços
            period: Período para cálculo da média
            
        Returns:
            Valor da SMA ou None se dados insuficientes
        """
        if not prices or len(prices) < period:
            return None
        
        # Usar os últimos 'period' valores
        recent_prices = prices[-period:]
        sma = sum(recent_prices) / period
        
        logger.debug(f"📊 SMA({period}): {sma:.5f} (últimos {period} preços)")
        return sma
    
    def calculate_rsi(self, prices: List[float], period: int) -> Optional[float]:
        """
        Calcula Relative Strength Index (RSI)
        
        Args:
            prices: Lista de preços
            period: Período para cálculo do RSI
            
        Returns:
            Valor do RSI (0-100) ou None se dados insuficientes
        """
        if not prices or len(prices) < period + 1:
            return None
        
        # Calcular mudanças de preço
        price_changes = []
        for i in range(1, len(prices)):
            change = prices[i] - prices[i-1]
            price_changes.append(change)
        
        if len(price_changes) < period:
            return None
        
        # Usar os últimos 'period' valores de mudança
        recent_changes = price_changes[-period:]
        
        # Separar ganhos e perdas
        gains = [change if change > 0 else 0 for change in recent_changes]
        losses = [-change if change < 0 else 0 for change in recent_changes]
        
        # Calcular médias
        avg_gain = sum(gains) / period if gains else 0
        avg_loss = sum(losses) / period if losses else 0
        
        # Evitar divisão por zero
        if avg_loss == 0:
            rsi = 100.0
        else:
            rs = avg_gain / avg_loss
            rsi = 100 - (100 / (1 + rs))
        
        logger.debug(f"📊 RSI({period}): {rsi:.2f} (avg_gain: {avg_gain:.5f}, avg_loss: {avg_loss:.5f})")
        return rsi
    
    def analyze_entry_signal(self, tick_history: List[float]) -> Optional[str]:
        """
        Analisa sinais de entrada baseado em SMA + RSI
        
        Args:
            tick_history: Histórico de ticks (preços)
            
        Returns:
            "RESETCALL", "RESETPUT" ou None
        """
        if not tick_history or len(tick_history) < 50:
            logger.debug(f"📊 Histórico insuficiente: {len(tick_history) if tick_history else 0}/50 ticks")
            return None
        
        try:
            # Calcular SMAs
            sma5 = self.calculate_sma(tick_history, 5)
            sma12 = self.calculate_sma(tick_history, 12)
            sma40 = self.calculate_sma(tick_history, 40)
            sma50 = self.calculate_sma(tick_history, 50)
            
            # Calcular RSIs
            rsi3 = self.calculate_rsi(tick_history, 3)
            rsi7 = self.calculate_rsi(tick_history, 7)
            rsi10 = self.calculate_rsi(tick_history, 10)
            
            # Verificar se todos os indicadores foram calculados
            if None in [sma5, sma12, sma40, sma50, rsi3]:
                logger.debug("📊 Alguns indicadores não puderam ser calculados")
                return None
            
            # Preços atuais para análise de tendência
            current_price = tick_history[-1]
            previous_price = tick_history[-2] if len(tick_history) >= 2 else current_price
            
            logger.debug(f"📊 Indicadores calculados:")
            logger.debug(f"   SMA5: {sma5:.5f}, SMA12: {sma12:.5f}")
            logger.debug(f"   SMA40: {sma40:.5f}, SMA50: {sma50:.5f}")
            logger.debug(f"   RSI3: {rsi3:.2f}, RSI7: {rsi7:.2f}, RSI10: {rsi10:.2f}")
            logger.debug(f"   Preço atual: {current_price:.5f}, anterior: {previous_price:.5f}")
            
            # === LÓGICA RESETCALL (Sinal de Alta) ===
            # Condição principal: SMA40 > SMA50 AND SMA5 > SMA12 AND 55 < RSI3 < 75
            resetcall_condition = (
                sma40 > sma50 and 
                sma5 > sma12 and 
                55 < rsi3 < 75
            )
            
            # === LÓGICA RESETPUT (Sinal de Baixa) ===
            # Condição principal: SMA40 < SMA50 AND SMA5 < SMA12 AND 25 < RSI3 < 45
            resetput_condition = (
                sma40 < sma50 and 
                sma5 < sma12 and 
                25 < rsi3 < 45
            )
            
            # === SINAIS ESPECIAIS (Sobrecompra/Sobrevenda) ===
            # RSI3 > 85 e preço caindo = RESETPUT
            special_resetput = (rsi3 > 85 and current_price < previous_price)
            
            # RSI3 < 15 e preço subindo = RESETCALL
            special_resetcall = (rsi3 < 15 and current_price > previous_price)
            
            # Determinar sinal final
            signal = None
            reason = ""
            
            if resetcall_condition:
                signal = "RESETCALL"
                reason = f"SMA40({sma40:.5f}) > SMA50({sma50:.5f}) AND SMA5({sma5:.5f}) > SMA12({sma12:.5f}) AND RSI3({rsi3:.2f}) em zona de alta"
            elif resetput_condition:
                signal = "RESETPUT"
                reason = f"SMA40({sma40:.5f}) < SMA50({sma50:.5f}) AND SMA5({sma5:.5f}) < SMA12({sma12:.5f}) AND RSI3({rsi3:.2f}) em zona de baixa"
            elif special_resetput:
                signal = "RESETPUT"
                reason = f"Sinal especial: RSI3({rsi3:.2f}) > 85 (sobrecompra) e preço caindo"
            elif special_resetcall:
                signal = "RESETCALL"
                reason = f"Sinal especial: RSI3({rsi3:.2f}) < 15 (sobrevenda) e preço subindo"
            
            if signal:
                logger.info(f"🎯 SINAL DETECTADO: {signal}")
                logger.info(f"📋 Razão: {reason}")
            else:
                logger.debug("📊 Nenhum sinal detectado nas condições atuais")
            
            return signal
            
        except Exception as e:
            logger.error(f"❌ Erro na análise técnica: {e}")
            return None
    
    def get_signal_confidence(self, tick_history: List[float]) -> float:
        """
        Calcula nível de confiança do sinal (0.0 a 1.0)
        
        Args:
            tick_history: Histórico de ticks
            
        Returns:
            Nível de confiança (0.0 a 1.0)
        """
        if not tick_history or len(tick_history) < 50:
            return 0.0
        
        try:
            # Calcular indicadores
            sma5 = self.calculate_sma(tick_history, 5)
            sma12 = self.calculate_sma(tick_history, 12)
            sma40 = self.calculate_sma(tick_history, 40)
            sma50 = self.calculate_sma(tick_history, 50)
            rsi3 = self.calculate_rsi(tick_history, 3)
            rsi7 = self.calculate_rsi(tick_history, 7)
            
            if None in [sma5, sma12, sma40, sma50, rsi3, rsi7]:
                return 0.0
            
            confidence = 0.0
            
            # Fator 1: Alinhamento das SMAs (0.0 a 0.4)
            sma_trend_strength = abs(sma5 - sma12) / max(sma5, sma12)
            sma_long_trend_strength = abs(sma40 - sma50) / max(sma40, sma50)
            sma_confidence = min(0.4, (sma_trend_strength + sma_long_trend_strength) * 20)
            confidence += sma_confidence
            
            # Fator 2: RSI em zona definida (0.0 a 0.4)
            if 55 <= rsi3 <= 75 or 25 <= rsi3 <= 45:
                rsi_confidence = 0.4
            elif rsi3 > 85 or rsi3 < 15:
                rsi_confidence = 0.5  # Sinais especiais têm mais confiança
            else:
                rsi_confidence = max(0.0, 0.4 - abs(rsi3 - 50) / 100)
            confidence += rsi_confidence
            
            # Fator 3: Consistência entre RSI3 e RSI7 (0.0 a 0.2)
            rsi_consistency = max(0.0, 0.2 - abs(rsi3 - rsi7) / 100)
            confidence += rsi_consistency
            
            # Normalizar para 0.0-1.0
            confidence = min(1.0, confidence)
            
            logger.debug(f"📊 Confiança calculada: {confidence:.3f}")
            logger.debug(f"   SMA: {sma_confidence:.3f}, RSI: {rsi_confidence:.3f}, Consistência: {rsi_consistency:.3f}")
            
            return confidence
            
        except Exception as e:
            logger.error(f"❌ Erro no cálculo de confiança: {e}")
            return 0.0
    
    def get_market_analysis(self, tick_history: List[float]) -> Dict[str, Any]:
        """
        Retorna análise completa do mercado
        
        Args:
            tick_history: Histórico de ticks
            
        Returns:
            Dicionário com análise completa
        """
        if not tick_history or len(tick_history) < 50:
            return {"error": "Dados insuficientes"}
        
        try:
            analysis = {
                "timestamp": logger.handlers[0].formatter.formatTime(logging.LogRecord("", 0, "", 0, "", (), None)),
                "data_points": len(tick_history),
                "current_price": tick_history[-1],
                "sma": {},
                "rsi": {},
                "signal": None,
                "confidence": 0.0,
                "trend": "NEUTRO"
            }
            
            # Calcular SMAs
            analysis["sma"]["sma5"] = self.calculate_sma(tick_history, 5)
            analysis["sma"]["sma12"] = self.calculate_sma(tick_history, 12)
            analysis["sma"]["sma40"] = self.calculate_sma(tick_history, 40)
            analysis["sma"]["sma50"] = self.calculate_sma(tick_history, 50)
            
            # Calcular RSIs
            analysis["rsi"]["rsi3"] = self.calculate_rsi(tick_history, 3)
            analysis["rsi"]["rsi7"] = self.calculate_rsi(tick_history, 7)
            analysis["rsi"]["rsi10"] = self.calculate_rsi(tick_history, 10)
            
            # Determinar tendência
            sma5 = analysis["sma"]["sma5"]
            sma50 = analysis["sma"]["sma50"]
            if sma5 and sma50:
                if sma5 > sma50 * 1.001:  # 0.1% de margem
                    analysis["trend"] = "ALTA"
                elif sma5 < sma50 * 0.999:
                    analysis["trend"] = "BAIXA"
            
            # Obter sinal e confiança
            analysis["signal"] = self.analyze_entry_signal(tick_history)
            analysis["confidence"] = self.get_signal_confidence(tick_history)
            
            return analysis
            
        except Exception as e:
            logger.error(f"❌ Erro na análise de mercado: {e}")
            return {"error": str(e)}