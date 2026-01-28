# -*- coding: utf-8 -*-
"""
Script para investigar a estrutura dos contratos no Sienge e Supabase
Para identificar o campo correto de Situação (Emitido/Cancelado)
"""

import os
import json
from supabase import create_client
from dotenv import load_dotenv
from sienge_client import sienge_client

load_dotenv()


def conectar_supabase():
    """Conecta ao Supabase"""
    return create_client(
        os.getenv('SUPABASE_URL'),
        os.getenv('SUPABASE_KEY')
    )


def investigar_contratos_supabase():
    """Mostra a estrutura dos contratos no Supabase"""
    print("\n" + "="*70)
    print("INVESTIGANDO CONTRATOS NO SUPABASE")
    print("="*70)
    
    supabase = conectar_supabase()
    
    # Buscar alguns contratos
    result = supabase.table('sienge_contratos').select('*').limit(5).execute()
    
    if result.data:
        print(f"\nTotal de contratos encontrados (amostra): {len(result.data)}")
        print("\nCampos disponíveis:")
        print("-" * 50)
        
        # Mostrar todos os campos do primeiro contrato
        primeiro = result.data[0]
        for campo, valor in primeiro.items():
            print(f"  {campo}: {valor}")
        
        print("\n" + "-"*50)
        print("VALORES ÚNICOS DO CAMPO 'status':")
        
        # Buscar todos para ver valores únicos de status
        result_all = supabase.table('sienge_contratos').select('status, numero_contrato, nome_cliente').execute()
        
        status_unicos = {}
        for c in (result_all.data or []):
            st = c.get('status') or 'NULL'
            if st not in status_unicos:
                status_unicos[st] = []
            if len(status_unicos[st]) < 3:  # Guardar até 3 exemplos
                status_unicos[st].append(f"{c.get('numero_contrato')} - {c.get('nome_cliente')}")
        
        for status, exemplos in sorted(status_unicos.items()):
            print(f"\n  Status: '{status}'")
            for ex in exemplos:
                print(f"    - {ex}")
    else:
        print("Nenhum contrato encontrado no Supabase")


def investigar_contratos_sienge():
    """Mostra a estrutura dos contratos diretamente da API do Sienge"""
    print("\n" + "="*70)
    print("INVESTIGANDO CONTRATOS NA API DO SIENGE")
    print("="*70)
    
    # Buscar alguns contratos
    contratos = sienge_client.get_contracts(limit=5)
    
    if contratos:
        print(f"\nTotal de contratos encontrados (amostra): {len(contratos)}")
        print("\nEstrutura completa do primeiro contrato:")
        print("-" * 50)
        
        # Mostrar JSON formatado do primeiro contrato
        print(json.dumps(contratos[0], indent=2, ensure_ascii=False, default=str))
        
        print("\n" + "-"*50)
        print("CAMPOS ENCONTRADOS:")
        for campo in sorted(contratos[0].keys()):
            print(f"  - {campo}")
    else:
        print("Nenhum contrato encontrado na API do Sienge")


def investigar_comissoes_supabase():
    """Mostra a estrutura das comissões no Supabase"""
    print("\n" + "="*70)
    print("INVESTIGANDO COMISSÕES NO SUPABASE")
    print("="*70)
    
    supabase = conectar_supabase()
    
    # Buscar algumas comissões
    result = supabase.table('sienge_comissoes').select('*').limit(5).execute()
    
    if result.data:
        print(f"\nTotal de comissões encontradas (amostra): {len(result.data)}")
        print("\nCampos disponíveis:")
        print("-" * 50)
        
        # Mostrar todos os campos da primeira comissão
        primeira = result.data[0]
        for campo, valor in primeira.items():
            print(f"  {campo}: {valor}")
    else:
        print("Nenhuma comissão encontrada no Supabase")


def buscar_contrato_especifico(numero_contrato):
    """Busca um contrato específico para análise"""
    print(f"\n" + "="*70)
    print(f"BUSCANDO CONTRATO {numero_contrato}")
    print("="*70)
    
    supabase = conectar_supabase()
    
    # Buscar no Supabase
    result = supabase.table('sienge_contratos')\
        .select('*')\
        .eq('numero_contrato', numero_contrato)\
        .execute()
    
    if result.data:
        print(f"\nEncontrado no Supabase:")
        for c in result.data:
            print(json.dumps(c, indent=2, ensure_ascii=False, default=str))
    else:
        print(f"Contrato {numero_contrato} não encontrado no Supabase")
    
    # Buscar comissões relacionadas
    result_comissoes = supabase.table('sienge_comissoes')\
        .select('*')\
        .eq('numero_contrato', numero_contrato)\
        .execute()
    
    if result_comissoes.data:
        print(f"\nComissões relacionadas ({len(result_comissoes.data)}):")
        for c in result_comissoes.data:
            print(f"  - ID {c.get('id')} | Corretor: {c.get('broker_nome')} | Status: {c.get('installment_status')} | Valor: R$ {c.get('commission_value', 0)}")


def main():
    print("\n" + "="*70)
    print("  INVESTIGAÇÃO DE ESTRUTURA DE DADOS")
    print("  Sistema de Comissões Young Empreendimentos")
    print("="*70)
    
    # Investigar Supabase
    investigar_contratos_supabase()
    
    # Investigar comissões
    investigar_comissoes_supabase()
    
    # Investigar API Sienge (se disponível)
    try:
        investigar_contratos_sienge()
    except Exception as e:
        print(f"\nErro ao acessar API Sienge: {str(e)}")
    
    # Buscar contrato específico (248 que aparece duplicado)
    buscar_contrato_especifico('248')
    buscar_contrato_especifico('248A')


if __name__ == '__main__':
    # Redirecionar saída para arquivo
    import sys
    with open('resultado_investigacao.txt', 'w', encoding='utf-8') as f:
        sys.stdout = f
        main()
        sys.stdout = sys.__stdout__
    print("Resultado salvo em resultado_investigacao.txt")

