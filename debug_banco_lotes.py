"""
Debug: verificar o que está no banco para os lotes com números estranhos
"""
import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

supabase = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_KEY'))

def main():
    print("=" * 80)
    print("VERIFICANDO DADOS NO SUPABASE")
    print("=" * 80)
    
    # Buscar comissões que têm unit_name com valores altos (parecem ser billNumber)
    result = supabase.table('sienge_comissoes').select('*').limit(20).execute()
    
    print(f"\nTotal de registros retornados: {len(result.data)}")
    
    for c in result.data[:10]:
        print(f"\n--- ID: {c.get('id')} | Sienge ID: {c.get('sienge_id')} ---")
        print(f"  Corretor: {c.get('broker_nome')}")
        print(f"  Empreendimento: {c.get('enterprise_name')}")
        print(f"  unit_name: {c.get('unit_name')}")
        print(f"  numero_contrato: {c.get('numero_contrato')}")
        print(f"  installment_status: {c.get('installment_status')}")
    
    # Buscar especificamente os que têm unit_name > 1000 (provavelmente billNumber)
    print("\n" + "=" * 80)
    print("COMISSÕES COM unit_name > 1000 (possíveis billNumber errados)")
    print("=" * 80)
    
    result2 = supabase.table('sienge_comissoes').select('*').execute()
    
    errados = []
    for c in result2.data:
        unit = c.get('unit_name')
        if unit:
            try:
                if int(unit) > 1000:
                    errados.append(c)
            except:
                pass
    
    print(f"\nEncontrados {len(errados)} registros com unit_name > 1000:")
    for c in errados[:15]:
        print(f"  ID {c.get('id')}: unit_name={c.get('unit_name')}, corretor={c.get('broker_nome')}, emp={c.get('enterprise_name')}")

if __name__ == '__main__':
    main()
