#!/usr/bin/env python3
"""
Script para limpar completamente o arquivo radartunder3.5.py
Remove código duplicado e malformado, mantendo apenas o conteúdo válido
"""

def clean_radartunder_file():
    file_path = 'radartunder3.5.py'
    
    try:
        # Ler o arquivo atual
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        print(f"Arquivo original tem {len(lines)} linhas")
        
        # Encontrar onde termina a função validacao_cruzada_martingale
        clean_lines = []
        inside_function = False
        function_ended = False
        
        for i, line in enumerate(lines):
            # Adicionar linhas até encontrar o final da função validacao_cruzada_martingale
            if 'def validacao_cruzada_martingale' in line:
                inside_function = True
                clean_lines.append(line)
                continue
            
            if inside_function:
                clean_lines.append(line)
                # Verificar se chegamos ao final da função (próxima função ou classe)
                if (line.strip().startswith('def ') and 'validacao_cruzada_martingale' not in line) or \
                   (line.strip().startswith('class ')) or \
                   (line.strip() == '' and i + 1 < len(lines) and 
                    (lines[i + 1].strip().startswith('def ') or lines[i + 1].strip().startswith('class '))):
                    function_ended = True
                    break
            else:
                # Se ainda não encontramos a função, adicionar a linha
                if not function_ended:
                    clean_lines.append(line)
        
        # Se não encontramos o final da função, vamos procurar por padrões problemáticos
        if not function_ended:
            # Remover linhas após problemas conhecidos
            final_lines = []
            for line in clean_lines:
                # Parar se encontrarmos linhas problemáticas
                if ("padrao_atual = ''.join(['" in line or 
                    line.strip().endswith("['") or
                    "W' if op == 'WIN' else 'L'" in line):
                    break
                final_lines.append(line)
            clean_lines = final_lines
        
        # Garantir que o arquivo termine corretamente
        if clean_lines and not clean_lines[-1].strip() == '':
            clean_lines.append('\n')
        
        # Escrever o arquivo limpo
        with open(file_path, 'w', encoding='utf-8') as f:
            f.writelines(clean_lines)
        
        print(f"Arquivo limpo tem {len(clean_lines)} linhas")
        print(f"Redução: {len(lines) - len(clean_lines)} linhas removidas")
        
        return True
        
    except Exception as e:
        print(f"Erro ao limpar arquivo: {e}")
        return False

if __name__ == "__main__":
    success = clean_radartunder_file()
    if success:
        print("✅ Arquivo radartunder3.5.py limpo com sucesso!")
    else:
        print("❌ Erro ao limpar arquivo")