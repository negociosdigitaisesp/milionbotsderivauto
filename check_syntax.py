#!/usr/bin/env python3
import ast
import sys

def analyze_try_blocks(filename):
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        try_stack = []
        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            indent = len(line) - len(line.lstrip())
            
            if stripped.startswith('try:'):
                try_stack.append((i, indent))
                print(f"Linha {i}: TRY encontrado (indentação: {indent})")
            elif stripped.startswith('except ') or stripped == 'except:':
                if try_stack:
                    try_line, try_indent = try_stack[-1]
                    if indent == try_indent:
                        print(f"Linha {i}: EXCEPT correspondente ao TRY da linha {try_line}")
                        try_stack.pop()
                    else:
                        print(f"Linha {i}: EXCEPT com indentação incorreta (esperado: {try_indent}, atual: {indent})")
                else:
                    print(f"Linha {i}: EXCEPT órfão (sem TRY correspondente)")
            elif stripped.startswith('finally:'):
                if try_stack:
                    try_line, try_indent = try_stack[-1]
                    if indent == try_indent:
                        print(f"Linha {i}: FINALLY correspondente ao TRY da linha {try_line}")
                        try_stack.pop()
                    else:
                        print(f"Linha {i}: FINALLY com indentação incorreta (esperado: {try_indent}, atual: {indent})")
                else:
                    print(f"Linha {i}: FINALLY órfão (sem TRY correspondente)")
        
        if try_stack:
            print("\n❌ TRY blocks órfãos encontrados:")
            for try_line, try_indent in try_stack:
                print(f"   Linha {try_line}: TRY sem EXCEPT/FINALLY correspondente")
        else:
            print("\n✅ Todos os TRY blocks têm EXCEPT/FINALLY correspondentes")
            
        return len(try_stack) == 0
        
    except Exception as e:
        print(f"❌ Erro ao analisar {filename}: {e}")
        return False

def check_syntax(filename):
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            source = f.read()
        
        # Tentar compilar o código
        ast.parse(source, filename=filename)
        print(f"✅ Sintaxe do arquivo {filename} está correta!")
        return True
        
    except SyntaxError as e:
        print(f"❌ Erro de sintaxe em {filename}:")
        print(f"   Linha {e.lineno}: {e.text.strip() if e.text else 'N/A'}")
        print(f"   Erro: {e.msg}")
        print(f"   Posição: {' ' * (e.offset - 1) if e.offset else ''}^")
        return False
    except Exception as e:
        print(f"❌ Erro ao verificar {filename}: {e}")
        return False

if __name__ == "__main__":
    filename = "tunderbot.py"
    print("=== Análise de blocos TRY-EXCEPT ===")
    analyze_try_blocks(filename)
    print("\n=== Verificação de sintaxe ===")
    if not check_syntax(filename):
        sys.exit(1)