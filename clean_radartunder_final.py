#!/usr/bin/env python3
"""
Script final para limpar completamente o arquivo radartunder3.5.py
"""

def clean_radartunder_final():
    """Limpa completamente o arquivo radartunder3.5.py removendo duplicações"""
    
    file_path = "radartunder3.5.py"
    
    try:
        # Lê o arquivo
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # Encontra onde termina a primeira classe RiskDetector completa
        cleaned_lines = []
        inside_risk_detector = False
        risk_detector_complete = False
        
        for i, line in enumerate(lines):
            # Se encontrarmos a primeira classe RiskDetector
            if line.strip().startswith("class RiskDetector:") and not risk_detector_complete:
                inside_risk_detector = True
                cleaned_lines.append(line)
                continue
            
            # Se estivermos dentro da classe RiskDetector
            if inside_risk_detector:
                cleaned_lines.append(line)
                
                # Se encontrarmos o final da função analyze_last_20_operations
                if line.strip() == "}" and i > 0 and "analysis" in lines[i-1]:
                    risk_detector_complete = True
                    inside_risk_detector = False
                continue
            
            # Se a classe RiskDetector já foi completada, ignoramos tudo depois
            if risk_detector_complete:
                break
            
            # Se não estivermos dentro da classe RiskDetector e ela não foi completada ainda
            if not inside_risk_detector and not risk_detector_complete:
                cleaned_lines.append(line)
        
        # Salva o arquivo corrigido
        with open(file_path, 'w', encoding='utf-8') as f:
            f.writelines(cleaned_lines)
        
        print("✅ Arquivo radartunder3.5.py limpo completamente!")
        print(f"📊 Linhas originais: {len(lines)}")
        print(f"📊 Linhas após limpeza final: {len(cleaned_lines)}")
        return True
            
    except Exception as e:
        print(f"❌ Erro ao limpar arquivo: {e}")
        return False

if __name__ == "__main__":
    clean_radartunder_final()