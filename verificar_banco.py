"""
Script para verificar comissões no banco
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
    result = supabase.table('sienge_comissoes').select('*').execute()
    comissoes = result.data or []
    
    print(f"Total de comissões no banco: {len(comissoes)}")
    
    # Agrupar por contrato + empreendimento
    grupos = {}
    for c in comissoes:
        chave = f"{c.get('numero_contrato')}_{c.get('enterprise_name')}"
        if chave not in grupos:
            grupos[chave] = []
        grupos[chave].append(c)
    
    # Verificar contratos com múltiplas comissões (múltiplos corretores)
    print(f"\nContratos únicos: {len(grupos)}")
    
    multiplos = {k: v for k, v in grupos.items() if len(v) > 1}
    print(f"Contratos com múltiplas comissões: {len(multiplos)}")
    
    if multiplos:
        print("\nExemplos de contratos com múltiplas comissões:")
        for chave, lista in list(multiplos.items())[:5]:
            print(f"\n  {chave}:")
            for c in lista:
                print(f"    - Corretor: {c.get('broker_nome')} | Sienge ID: {c.get('sienge_id')} | R$ {c.get('commission_value')}")

if __name__ == '__main__':
    main()
