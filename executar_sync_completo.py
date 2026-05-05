"""
Script para executar sincronização completa com Sienge
"""
import sys
sys.stdout.reconfigure(line_buffering=True)

from sync_sienge_supabase import SiengeSupabaseSync

print("=" * 60)
print("SINCRONIZAÇÃO COMPLETA COM SIENGE")
print("=" * 60)
print()

sync = SiengeSupabaseSync()

print("Iniciando sincronização completa...")
print()

resultado = sync.sync_all()

print()
print("=" * 60)
print("RESULTADO FINAL:")
print("=" * 60)
for chave, valor in resultado.items():
    print(f"  {chave}: {valor}")
print()
print("Sincronização concluída!")
