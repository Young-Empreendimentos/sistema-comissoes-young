"""
Verifica estado da sincronização
"""
from supabase import create_client
import os
from dotenv import load_dotenv
load_dotenv()

supabase = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_KEY'))

NOMES = {
    2003: 'Montecarlo',
    2004: 'Ilha dos Acores', 
    2005: 'Aurora',
    2007: 'Parque Lorena I',
    2009: 'Parque Lorena II',
    2010: 'Erico Verissimo',
    2011: 'Algarve',
    2014: 'Morada da Coxilha'
}

print('=== EMPREENDIMENTOS NO BANCO ===')
print()

for bid, nome in sorted(NOMES.items()):
    result = supabase.table('comissoes_sienge_contratos').select('*', count='exact').eq('building_id', bid).execute()
    print(f'{nome} ({bid}): {result.count} contratos')

# Total
result_total = supabase.table('comissoes_sienge_contratos').select('*', count='exact').execute()
print()
print(f'TOTAL: {result_total.count} contratos')
