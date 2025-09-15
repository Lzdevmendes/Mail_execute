#!/usr/bin/env python3
"""
Script para limpar cache e arquivos temporários do projeto
Execute: python clean_cache.py
"""

import os
import shutil
from pathlib import Path

def clean_python_cache():
    """Remove __pycache__ e arquivos .pyc/.pyo"""
    removed_count = 0

    for root, dirs, files in os.walk('.'):
        # Remove __pycache__ directories
        if '__pycache__' in dirs:
            cache_dir = os.path.join(root, '__pycache__')
            print(f"Removendo: {cache_dir}")
            shutil.rmtree(cache_dir)
            dirs.remove('__pycache__')
            removed_count += 1

        # Remove .pyc and .pyo files
        for file in files:
            if file.endswith(('.pyc', '.pyo')):
                file_path = os.path.join(root, file)
                print(f"Removendo: {file_path}")
                os.remove(file_path)
                removed_count += 1

    return removed_count

def clean_test_cache():
    """Remove .pytest_cache"""
    pytest_cache = Path('.pytest_cache')
    if pytest_cache.exists():
        print(f"Removendo: {pytest_cache}")
        shutil.rmtree(pytest_cache)
        return 1
    return 0

def clean_logs():
    """Remove logs antigos mas mantém sys.stdout atual"""
    removed_count = 0

    # Remove logs antigos
    for log_file in Path('.').glob('*.log'):
        print(f"Removendo log: {log_file}")
        log_file.unlink()
        removed_count += 1

    return removed_count

def main():
    print("🧹 Limpando cache e arquivos temporários...")

    total_removed = 0

    # Limpar cache Python
    print("\n📁 Limpando cache Python...")
    total_removed += clean_python_cache()

    # Limpar cache de testes
    print("\n🧪 Limpando cache de testes...")
    total_removed += clean_test_cache()

    # Limpar logs antigos
    print("\n📋 Limpando logs antigos...")
    total_removed += clean_logs()

    print(f"\n✅ Limpeza concluída! {total_removed} itens removidos.")
    print("\n💡 Dica: Execute 'python clean_cache.py' sempre antes de commits!")

if __name__ == "__main__":
    main()