#!/usr/bin/env python3
"""
Script para corrigir o arquivo radartunder3.5.py
"""

def fix_radartunder_file():
    """Corrige o arquivo radartunder3.5.py removendo código duplicado e mal formatado"""
    
    file_path = "radartunder3.5.py"
    
    try:
        # Lê o arquivo
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # Remove linhas problemáticas e duplicadas
        cleaned_lines = []
        skip_until_class = False
        
        for i, line in enumerate(lines):
            # Se encontrarmos a linha problemática, começamos a pular
            if "}']" in line and "analysis" in lines[i-1] if i > 0 else False:
                skip_until_class = True
                # Adiciona o fechamento correto da função
                cleaned_lines.append("        }\n")
                continue
            
            # Se estivermos pulando e encontrarmos a classe RiskDetector, paramos de pular
            if skip_until_class and line.strip().startswith("class RiskDetector:"):
                skip_until_class = False
                cleaned_lines.append(line)
                continue
            
            # Se não estivermos pulando, adiciona a linha
            if not skip_until_class:
                cleaned_lines.append(line)
        
        # Salva o arquivo corrigido
        with open(file_path, 'w', encoding='utf-8') as f:
            f.writelines(cleaned_lines)
        
        print("✅ Arquivo radartunder3.5.py limpo com sucesso!")
        print(f"📊 Linhas originais: {len(lines)}")
        print(f"📊 Linhas após limpeza: {len(cleaned_lines)}")
        return True
            
    except Exception as e:
        print(f"❌ Erro ao corrigir arquivo: {e}")
        return False

if __name__ == "__main__":
    fix_radartunder_file()