from radar_analyzer import analisar_estrategias_portfolio

# Teste isolado da CYCLE_TRANSITION
historico = ['D'] + ['V'] * 20

print(f"Histórico: {' '.join(historico[:10])}... (total: {len(historico)})")
print(f"Posição no ciclo: {((len(historico)-1) % 20) + 1}/20")
print(f"Últimas 6: {' '.join(historico[1:7])} - WINs: {historico[1:7].count('V')}/6")
print(f"Últimas 12: LOSSes: {historico[1:13].count('D')}/12")
print(f"Ciclo anterior: WINs: {historico[1:21].count('V')}/20 = {(historico[1:21].count('V')/20)*100:.1f}%")

print("\nTestando CYCLE_TRANSITION...")
resultado = analisar_estrategias_portfolio(historico)

print(f"\nResultado: {resultado}")

cycle_found = any(
    estrategia.get('strategy') == 'CYCLE_TRANSITION' 
    for estrategia in resultado.get('estrategias_disponiveis', [])
)

print(f"\nCYCLE_TRANSITION detectada: {cycle_found}")
print(f"Should operate: {resultado.get('should_operate', False)}")