# -*- coding: utf-8 -*-
"""
Script para executar a limpeza de comissões canceladas e duplicadas automaticamente
Sistema de Comissões Young Empreendimentos
"""

import os
from datetime import datetime
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()


def conectar_supabase():
    """Conecta ao Supabase"""
    return create_client(
        os.getenv('SUPABASE_URL'),
        os.getenv('SUPABASE_KEY')
    )


def executar_limpeza():
    """Executa a limpeza completa de comissões canceladas e duplicadas"""
    print("\n" + "="*60)
    print("  LIMPEZA AUTOMÁTICA DE COMISSÕES")
    print("  Sistema de Comissões Young Empreendimentos")
    print("="*60)
    
    supabase = conectar_supabase()
    
    # 1. DELETAR COMISSÕES CANCELADAS
    print("\n[1/3] Buscando comissões canceladas...")
    result = supabase.table('sienge_comissoes').select('*').execute()
    
    comissoes_canceladas = []
    for c in (result.data or []):
        status = (c.get('installment_status') or '').upper()
        if 'CANCEL' in status:
            comissoes_canceladas.append(c)
    
    print(f"    Encontradas {len(comissoes_canceladas)} comissões canceladas")
    
    count_canceladas = 0
    for c in comissoes_canceladas:
        try:
            supabase.table('sienge_comissoes').delete().eq('id', c['id']).execute()
            count_canceladas += 1
        except Exception as e:
            print(f"    Erro ao deletar comissão {c['id']}: {str(e)}")
    
    print(f"    ✓ Deletadas {count_canceladas} comissões canceladas")
    
    # 2. BUSCAR E LIMPAR DUPLICATAS
    print("\n[2/3] Buscando comissões duplicadas...")
    result = supabase.table('sienge_comissoes').select('*').execute()
    
    # Agrupar por numero_contrato + unit_name + building_id
    grupos = {}
    for c in (result.data or []):
        chave = f"{c.get('numero_contrato')}_{c.get('unit_name')}_{c.get('building_id')}"
        if chave not in grupos:
            grupos[chave] = []
        grupos[chave].append(c)
    
    # Encontrar duplicatas
    duplicatas = {k: v for k, v in grupos.items() if len(v) > 1}
    print(f"    Encontrados {len(duplicatas)} grupos de duplicatas")
    
    count_duplicatas = 0
    for chave, comissoes in duplicatas.items():
        # Ordenar: não-canceladas primeiro, depois por ID
        def prioridade(c):
            status = (c.get('installment_status') or '').upper()
            is_cancelada = 'CANCEL' in status
            return (is_cancelada, c.get('id', 0))
        
        comissoes_ordenadas = sorted(comissoes, key=prioridade)
        
        # Manter a primeira, deletar as outras
        deletar = comissoes_ordenadas[1:]
        
        for c in deletar:
            try:
                supabase.table('sienge_comissoes').delete().eq('id', c['id']).execute()
                count_duplicatas += 1
            except Exception as e:
                print(f"    Erro ao deletar duplicata {c['id']}: {str(e)}")
    
    print(f"    ✓ Removidas {count_duplicatas} comissões duplicadas")
    
    # 3. VERIFICAR CONTRATOS ÓRFÃOS (sem comissões válidas)
    print("\n[3/3] Verificando contratos órfãos...")
    
    # Buscar todos os contratos
    result_contratos = supabase.table('sienge_contratos').select('id, numero_contrato, building_id').execute()
    
    # Buscar todas as comissões restantes
    result_comissoes = supabase.table('sienge_comissoes').select('numero_contrato, building_id').execute()
    
    # Criar set de contratos com comissões
    contratos_com_comissoes = set()
    for c in (result_comissoes.data or []):
        chave = f"{c.get('numero_contrato')}_{c.get('building_id')}"
        contratos_com_comissoes.add(chave)
    
    # Identificar contratos órfãos
    contratos_orfaos = []
    for c in (result_contratos.data or []):
        chave = f"{c.get('numero_contrato')}_{c.get('building_id')}"
        if chave not in contratos_com_comissoes:
            contratos_orfaos.append(c)
    
    print(f"    Encontrados {len(contratos_orfaos)} contratos sem comissões válidas")
    # Não deletar contratos órfãos automaticamente - podem ter comissões futuras
    
    # RESUMO FINAL
    print("\n" + "="*60)
    print("  LIMPEZA CONCLUÍDA!")
    print("="*60)
    print(f"  ✓ Comissões canceladas removidas: {count_canceladas}")
    print(f"  ✓ Duplicatas removidas: {count_duplicatas}")
    print(f"  ℹ Contratos órfãos (não removidos): {len(contratos_orfaos)}")
    print("="*60)
    
    return {
        'canceladas_removidas': count_canceladas,
        'duplicatas_removidas': count_duplicatas,
        'contratos_orfaos': len(contratos_orfaos)
    }


if __name__ == '__main__':
    import sys
    
    # Salvar saída em arquivo
    log_file = open('resultado_limpeza_final.txt', 'w', encoding='utf-8')
    
    class TeeOutput:
        def __init__(self, *files):
            self.files = files
        def write(self, text):
            for f in self.files:
                f.write(text)
                f.flush()
        def flush(self):
            for f in self.files:
                f.flush()
    
    sys.stdout = TeeOutput(sys.__stdout__, log_file)
    
    try:
        resultado = executar_limpeza()
        print(f"\nResultado: {resultado}")
    finally:
        log_file.close()
        sys.stdout = sys.__stdout__
        print("Log salvo em resultado_limpeza_final.txt")

