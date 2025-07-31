#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🧪 SCRIPT DE TESTE PARA VALIDAÇÃO DAS OTIMIZAÇÕES

Este script testa as melhorias de performance antes da migração completa:
- Rate limiting distribuído
- Pool de conexões
- Execução paralela real
- Monitoramento em tempo real
"""

import asyncio
import time
from datetime import datetime
import json
from migrate_to_optimized import OptimizedBotManager, bot_gold_optimized_compatible

class PerformanceTest:
    """Classe para testes de performance"""
    
    def __init__(self):
        self.results = {
            'sequential_time': 0,
            'parallel_time': 0,
            'api_calls_sequential': 0,
            'api_calls_parallel': 0,
            'errors_sequential': 0,
            'errors_parallel': 0
        }
    
    async def simulate_bot_operation(self, manager: OptimizedBotManager, bot_name: str, duration: int = 30):
        """Simular operação de bot por tempo limitado"""
        start_time = time.time()
        operations = 0
        
        while time.time() - start_time < duration:
            try:
                # Simular chamadas API típicas de um bot
                await manager.safe_api_call(
                    bot_name, 'ticks_history', {
                        "ticks_history": "R_100",
                        "count": 1,
                        "end": "latest"
                    }
                )
                
                operations += 1
                await asyncio.sleep(0.5)  # Simular processamento
                
            except Exception as e:
                print(f"❌ {bot_name}: Erro na simulação - {e}")
                break
        
        return operations
    
    async def test_sequential_execution(self, duration: int = 60):
        """Testar execução sequencial (modo atual)"""
        print("🔄 Testando execução SEQUENCIAL...")
        
        manager = OptimizedBotManager()
        await manager.initialize()
        
        start_time = time.time()
        total_operations = 0
        
        # Executar bots sequencialmente
        for i in range(3):
            bot_name = f"TestBot_Sequential_{i+1}"
            operations = await self.simulate_bot_operation(manager, bot_name, duration // 3)
            total_operations += operations
            print(f"✅ {bot_name}: {operations} operações")
        
        execution_time = time.time() - start_time
        
        self.results['sequential_time'] = execution_time
        self.results['api_calls_sequential'] = manager.total_api_calls
        self.results['errors_sequential'] = manager.total_errors
        
        print(f"📊 Sequencial: {execution_time:.1f}s, {total_operations} ops, {manager.total_api_calls} API calls")
        return total_operations
    
    async def test_parallel_execution(self, duration: int = 60):
        """Testar execução paralela (modo otimizado)"""
        print("🚀 Testando execução PARALELA...")
        
        manager = OptimizedBotManager()
        await manager.initialize()
        
        start_time = time.time()
        
        # Executar bots em paralelo
        tasks = []
        for i in range(3):
            bot_name = f"TestBot_Parallel_{i+1}"
            task = asyncio.create_task(
                self.simulate_bot_operation(manager, bot_name, duration)
            )
            tasks.append((bot_name, task))
        
        # Aguardar conclusão
        results = await asyncio.gather(*[task for _, task in tasks], return_exceptions=True)
        
        execution_time = time.time() - start_time
        total_operations = sum(r for r in results if isinstance(r, int))
        
        self.results['parallel_time'] = execution_time
        self.results['api_calls_parallel'] = manager.total_api_calls
        self.results['errors_parallel'] = manager.total_errors
        
        for (bot_name, _), operations in zip(tasks, results):
            if isinstance(operations, int):
                print(f"✅ {bot_name}: {operations} operações")
            else:
                print(f"❌ {bot_name}: Erro - {operations}")
        
        print(f"📊 Paralelo: {execution_time:.1f}s, {total_operations} ops, {manager.total_api_calls} API calls")
        return total_operations
    
    async def test_rate_limiting_efficiency(self):
        """Testar eficiência do rate limiting"""
        print("⏱️ Testando eficiência do rate limiting...")
        
        manager = OptimizedBotManager()
        await manager.initialize()
        
        # Teste de rajada de chamadas
        start_time = time.time()
        tasks = []
        
        for i in range(10):
            task = asyncio.create_task(
                manager.safe_api_call(
                    f"RateLimitTest_{i}", 'ticks_history', {
                        "ticks_history": "R_100",
                        "count": 1,
                        "end": "latest"
                    }
                )
            )
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        execution_time = time.time() - start_time
        
        successful_calls = sum(1 for r in results if not isinstance(r, Exception))
        
        print(f"📊 Rate Limiting: {successful_calls}/10 sucessos em {execution_time:.1f}s")
        return successful_calls, execution_time
    
    def generate_report(self):
        """Gerar relatório de performance"""
        if self.results['sequential_time'] > 0 and self.results['parallel_time'] > 0:
            speedup = self.results['sequential_time'] / self.results['parallel_time']
            efficiency = (speedup / 3) * 100  # 3 bots
        else:
            speedup = 0
            efficiency = 0
        
        report = {
            'timestamp': datetime.now().isoformat(),
            'performance_comparison': {
                'sequential_time': round(self.results['sequential_time'], 2),
                'parallel_time': round(self.results['parallel_time'], 2),
                'speedup': round(speedup, 2),
                'efficiency_percent': round(efficiency, 2)
            },
            'api_efficiency': {
                'sequential_calls': self.results['api_calls_sequential'],
                'parallel_calls': self.results['api_calls_parallel'],
                'sequential_errors': self.results['errors_sequential'],
                'parallel_errors': self.results['errors_parallel']
            },
            'recommendations': []
        }
        
        # Gerar recomendações
        if speedup > 2.0:
            report['recommendations'].append("✅ Excelente paralelização - migração recomendada")
        elif speedup > 1.5:
            report['recommendations'].append("✅ Boa paralelização - migração benéfica")
        else:
            report['recommendations'].append("⚠️ Paralelização limitada - revisar configurações")
        
        if self.results['errors_parallel'] <= self.results['errors_sequential']:
            report['recommendations'].append("✅ Rate limiting eficiente")
        else:
            report['recommendations'].append("⚠️ Rate limiting precisa ajustes")
        
        return report

async def run_comprehensive_test():
    """Executar teste completo de performance"""
    print("🧪 INICIANDO TESTES DE PERFORMANCE")
    print("=" * 50)
    
    test = PerformanceTest()
    
    try:
        # Teste 1: Execução sequencial
        print("\n1️⃣ TESTE SEQUENCIAL")
        await test.test_sequential_execution(30)
        
        # Pausa entre testes
        print("\n⏸️ Pausa entre testes...")
        await asyncio.sleep(5)
        
        # Teste 2: Execução paralela
        print("\n2️⃣ TESTE PARALELO")
        await test.test_parallel_execution(30)
        
        # Teste 3: Rate limiting
        print("\n3️⃣ TESTE RATE LIMITING")
        await test.test_rate_limiting_efficiency()
        
        # Gerar relatório
        print("\n📊 GERANDO RELATÓRIO...")
        report = test.generate_report()
        
        print("\n" + "=" * 50)
        print("📈 RELATÓRIO DE PERFORMANCE")
        print("=" * 50)
        
        print(f"⏱️ Tempo Sequencial: {report['performance_comparison']['sequential_time']}s")
        print(f"⏱️ Tempo Paralelo: {report['performance_comparison']['parallel_time']}s")
        print(f"🚀 Speedup: {report['performance_comparison']['speedup']}x")
        print(f"📊 Eficiência: {report['performance_comparison']['efficiency_percent']}%")
        
        print(f"\n📡 API Calls Sequencial: {report['api_efficiency']['sequential_calls']}")
        print(f"📡 API Calls Paralelo: {report['api_efficiency']['parallel_calls']}")
        print(f"❌ Erros Sequencial: {report['api_efficiency']['sequential_errors']}")
        print(f"❌ Erros Paralelo: {report['api_efficiency']['parallel_errors']}")
        
        print("\n💡 RECOMENDAÇÕES:")
        for rec in report['recommendations']:
            print(f"  {rec}")
        
        # Salvar relatório
        with open('performance_test_report.json', 'w') as f:
            json.dump(report, f, indent=2)
        
        print("\n💾 Relatório salvo em 'performance_test_report.json'")
        
        return report
        
    except Exception as e:
        print(f"❌ Erro durante os testes: {e}")
        return None

async def test_bot_gold_optimized():
    """Testar especificamente o bot_gold otimizado"""
    print("\n🥇 TESTANDO BOT GOLD OTIMIZADO")
    print("=" * 40)
    
    manager = OptimizedBotManager()
    await manager.initialize()
    
    # Executar por tempo limitado
    test_duration = 60  # 1 minuto
    
    task = asyncio.create_task(
        manager.execute_bot_with_monitoring(
            bot_gold_optimized_compatible, 
            "GoldBot_Test", 
            0
        )
    )
    
    # Aguardar por tempo limitado
    try:
        await asyncio.wait_for(task, timeout=test_duration)
    except asyncio.TimeoutError:
        print(f"⏰ Teste finalizado após {test_duration}s")
        task.cancel()
    
    # Relatório do teste
    report = manager.get_comprehensive_report()
    
    print("\n📊 RESULTADO DO TESTE GOLD BOT:")
    if 'GoldBot_Test' in report['bots']:
        bot_stats = report['bots']['GoldBot_Test']
        print(f"💰 Profit: ${bot_stats['profit']}")
        print(f"📈 Operações: {bot_stats['operations']}")
        print(f"🎯 Taxa de Sucesso: {bot_stats['success_rate']}%")
        print(f"⚡ Tempo Médio de Resposta: {bot_stats['avg_response_time']}s")
    
    return report

if __name__ == "__main__":
    print("🧪 SISTEMA DE TESTES DE OTIMIZAÇÃO")
    print("Escolha o teste a executar:")
    print("1. Teste completo de performance")
    print("2. Teste específico do GoldBot")
    print("3. Ambos")
    
    choice = input("\nEscolha (1-3): ").strip()
    
    async def run_tests():
        if choice in ['1', '3']:
            await run_comprehensive_test()
        
        if choice in ['2', '3']:
            await test_bot_gold_optimized()
    
    try:
        asyncio.run(run_tests())
    except KeyboardInterrupt:
        print("\n⏹️ Testes interrompidos pelo usuário")
    except Exception as e:
        print(f"❌ Erro nos testes: {e}")