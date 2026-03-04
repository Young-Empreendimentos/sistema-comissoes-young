"""
Script para remover registros duplicados/errados do Supabase
Remove registros onde unit_name > 1000 (que são billNumber errados)
"""
import os
import sys
from dotenv import load_dotenv

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

load_dotenv()

from supabase import create_client

supabase = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_KEY'))

def main():
    print("=" * 70)
    print("REMOVENDO REGISTROS DUPLICADOS/ERRADOS")
    print("=" * 70)
    
    # 1. Buscar registros com unit_name errado (> 1000)
    print("\n[1/2] Buscando registros com unit_name > 1000...")
    result = supabase.table('sienge_comissoes').select('id, sienge_id, unit_name, broker_nome, numero_contrato').execute()
    
    registros = result.data or []
    print(f"      {len(registros)} registros no banco")
    
    # Filtrar os que têm unit_name errado
    registros_errados = []
    for reg in registros:
        unit = reg.get('unit_name')
        if unit:
            try:
                if int(unit) > 1000:
                    registros_errados.append(reg)
            except:
                pass
    
    print(f"      {len(registros_errados)} registros com unit_name > 1000 (duplicados/errados)")
    
    if not registros_errados:
        print("\nNenhum registro para remover!")
        return
    
    # 2. Remover registros errados
    print("\n[2/2] Removendo registros...")
    removidos = 0
    erros = 0
    
    for reg in registros_errados:
        try:
            supabase.table('sienge_comissoes').delete().eq('id', reg['id']).execute()
            print(f"  [REMOVIDO] ID {reg['id']}: unit_name={reg.get('unit_name')}, corretor={reg.get('broker_nome')}, contrato={reg.get('numero_contrato')}")
            removidos += 1
        except Exception as e:
            print(f"  [ERRO] ID {reg['id']}: {str(e)[:50]}")
            erros += 1
    
    print("\n" + "=" * 70)
    print("RESULTADO")
    print("=" * 70)
    print(f"Registros removidos: {removidos}")
    print(f"Erros: {erros}")
    print("=" * 70)

if __name__ == '__main__':
    main()
