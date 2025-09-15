#!/usr/bin/env python3
"""
Teste da integração OpenAI para verificar se está funcionando.
"""

import os
import asyncio
import sys
from pathlib import Path

# Adicionar o diretório raiz ao path
sys.path.append(str(Path(__file__).parent))

from backend.app.services.openai_service import openai_service

async def test_openai_integration():
    """Teste completo da integração OpenAI."""

    print("🧪 Testando integração OpenAI...")
    print("=" * 50)

    # Verificar se está disponível
    print(f"✅ OpenAI disponível: {openai_service.is_available()}")

    if not openai_service.is_available():
        print("❌ OpenAI não está configurado ou USE_OPENAI=False")
        print("\n📋 Para ativar OpenAI:")
        print("1. Verifique se OPENAI_API_KEY está configurada no .env")
        print("2. Configure USE_OPENAI=true no .env")
        return

    # Teste 1: Email produtivo
    print("\n🔍 Teste 1: Email Produtivo")
    email_produtivo = """
    Prezados,

    Estou enfrentando problemas críticos no sistema de vendas.
    O servidor está retornando erro 500 e precisamos resolver urgentemente
    pois isso está impactando as vendas de hoje.

    Podem me ajudar a resolver este problema?

    Obrigado,
    João Silva
    """

    try:
        resultado = await openai_service.classify_email(email_produtivo)
        if resultado:
            print(f"   📊 Categoria: {resultado.get('categoria')}")
            print(f"   🎯 Confiança: {resultado.get('confianca'):.2f}")
            print(f"   💭 Motivo: {resultado.get('motivo')}")

            # Gerar resposta
            resposta = await openai_service.generate_response(email_produtivo, resultado.get('categoria'))
            if resposta:
                print(f"   💬 Resposta gerada: {resposta}")
        else:
            print("   ❌ Falha na classificação")
    except Exception as e:
        print(f"   ❌ Erro: {e}")

    # Teste 2: Email improdutivo
    print("\n🔍 Teste 2: Email Improdutivo")
    email_improdutivo = """
    Oi pessoal!

    Espero que todos estejam bem! 🌟

    Queria agradecer pela festa de aniversário de ontem,
    foi incrível! Muito obrigado por tudo.

    Abraços carinhosos para todos! ❤️

    Maria
    """

    try:
        resultado = await openai_service.classify_email(email_improdutivo)
        if resultado:
            print(f"   📊 Categoria: {resultado.get('categoria')}")
            print(f"   🎯 Confiança: {resultado.get('confianca'):.2f}")
            print(f"   💭 Motivo: {resultado.get('motivo')}")

            # Gerar resposta
            resposta = await openai_service.generate_response(email_improdutivo, resultado.get('categoria'))
            if resposta:
                print(f"   💬 Resposta gerada: {resposta}")
        else:
            print("   ❌ Falha na classificação")
    except Exception as e:
        print(f"   ❌ Erro: {e}")

    print("\n" + "=" * 50)
    print("✅ Teste da integração OpenAI concluído!")

if __name__ == "__main__":
    # Definir variáveis de ambiente para teste
    os.environ['USE_OPENAI'] = 'true'

    # Executar teste
    asyncio.run(test_openai_integration())