"""
Sincronização Sienge → Supabase - Sistema de Comissões Young
Sincroniza dados do Sienge para o banco Supabase
"""

import os
from datetime import datetime
from typing import List, Dict, Optional
from supabase import create_client
from dotenv import load_dotenv
from sienge_client import sienge_client

load_dotenv()

# Conexão global do Supabase (evita criar nova conexão a cada requisição)
_supabase_client = None

def get_supabase_client():
    """Retorna cliente Supabase singleton (reutiliza conexão)"""
    global _supabase_client
    if _supabase_client is None:
        _supabase_client = create_client(
            os.getenv('SUPABASE_URL'),
            os.getenv('SUPABASE_KEY')
        )
    return _supabase_client


class SiengeSupabaseSync:
    """Sincroniza dados do Sienge para Supabase"""
    
    def __init__(self):
        self.supabase = get_supabase_client()
        self.sienge = sienge_client
    
    def sync_empreendimentos(self) -> dict:
        """Sincroniza empreendimentos do Sienge (todas as empresas)"""
        try:
            # Buscar empreendimentos de TODAS as empresas
            buildings = self.sienge.get_buildings_all_companies()
            count = 0
            
            for building in buildings:
                data = {
                    'sienge_id': building.get('id'),
                    'nome': building.get('name'),
                    'codigo': building.get('code'),
                    'company_id': building.get('companyId'),
                    'atualizado_em': datetime.now().isoformat()
                }
                
                # Upsert (insert ou update)
                self.supabase.table('sienge_empreendimentos').upsert(
                    data, 
                    on_conflict='sienge_id'
                ).execute()
                count += 1
            
            return {'sucesso': True, 'total': count}
        except Exception as e:
            print(f"Erro ao sincronizar empreendimentos: {str(e)}")
            return {'sucesso': False, 'erro': str(e)}
    
    def sync_contratos(self, building_id: int = None) -> dict:
        """Sincroniza contratos do Sienge (ignora cancelados/distratados) - todas as empresas"""
        try:
            # Buscar contratos de TODAS as empresas
            contracts = self.sienge.get_contracts_all_companies()
            count = 0
            cancelados = 0
            
            for contract in contracts:
                # Na v1, campo mudou de 'status' para 'situation'
                status = (contract.get('situation') or contract.get('status') or '').lower()
                if any(x in status for x in ['cancel', 'distrat', 'rescind']):
                    # Deletar do Supabase se existir
                    try:
                        self.supabase.table('sienge_contratos').delete()\
                            .eq('sienge_id', contract.get('id')).execute()
                        numero = contract.get('number') or contract.get('contractNumber')
                        enterprise = contract.get('enterpriseId') or contract.get('buildingId')
                        self.supabase.table('sienge_comissoes').delete()\
                            .eq('numero_contrato', numero)\
                            .eq('building_id', enterprise).execute()
                    except:
                        pass
                    cancelados += 1
                    continue
                
                # Extrair nome do cliente de salesContractCustomers (v1)
                customers = contract.get('salesContractCustomers') or []
                customer_name = customers[0].get('name') if customers else contract.get('customerName')
                
                # Extrair unidade de salesContractUnits (v1)
                units = contract.get('salesContractUnits') or []
                unit_name = units[0].get('name') if units else contract.get('unitName')
                
                data = {
                    'sienge_id': contract.get('id'),
                    'numero_contrato': contract.get('number') or contract.get('contractNumber'),
                    'building_id': contract.get('enterpriseId') or contract.get('buildingId'),
                    'company_id': contract.get('companyId'),
                    'nome_cliente': customer_name,
                    'data_contrato': contract.get('contractDate'),
                    'valor_total': contract.get('totalSellingValue') or contract.get('value') or contract.get('totalValue'),
                    'valor_a_vista': contract.get('value') or contract.get('totalSellingValue'),
                    'status': contract.get('situation') or contract.get('status'),
                    'unidade': unit_name,
                    'atualizado_em': datetime.now().isoformat()
                }
                
                self.supabase.table('sienge_contratos').upsert(
                    data,
                    on_conflict='sienge_id'
                ).execute()
                count += 1
            
            print(f"[Sync] Contratos: {count} sincronizados, {cancelados} cancelados ignorados")
            return {'sucesso': True, 'total': count, 'cancelados': cancelados}
        except Exception as e:
            print(f"Erro ao sincronizar contratos: {str(e)}")
            return {'sucesso': False, 'erro': str(e)}
    
    def sync_corretores(self, building_id: int = None) -> dict:
        """Sincroniza corretores do Sienge"""
        try:
            brokers = self.sienge.get_brokers(building_id=building_id)
            count = 0
            
            for broker in brokers:
                data = {
                    'sienge_id': broker.get('id'),
                    'nome': broker.get('name'),
                    'cpf': broker.get('cpf'),
                    'email': broker.get('email'),
                    'telefone': broker.get('phone'),
                    'ativo': broker.get('active', True),
                    'atualizado_em': datetime.now().isoformat()
                }
                
                self.supabase.table('sienge_corretores').upsert(
                    data,
                    on_conflict='sienge_id'
                ).execute()
                count += 1
            
            return {'sucesso': True, 'total': count}
        except Exception as e:
            print(f"Erro ao sincronizar corretores: {str(e)}")
            return {'sucesso': False, 'erro': str(e)}
    
    def sync_comissoes(self, building_id: int = None) -> dict:
        """Sincroniza comissões do Sienge (ignora cancelados) - todas as empresas"""
        try:
            # Buscar comissões de TODAS as empresas
            commissions = self.sienge.get_commissions_all_companies()
            count = 0
            cancelados = 0
            
            pagos = 0
            
            for commission in commissions:
                # Na API v1, os campos usam ID maiúsculo: commissionID, enterpriseID, brokerID, etc
                sienge_id = commission.get('commissionID') or commission.get('commissionId') or commission.get('id')
                
                # Verificar se a comissão está cancelada ou paga
                status = (commission.get('installmentStatus') or commission.get('status') or '').upper()
                cancelled_value = commission.get('cancelledValue') or 0
                
                # Ignorar comissões canceladas (por status ou por valor cancelado)
                is_cancelled = 'CANCEL' in status or cancelled_value > 0
                if is_cancelled:
                    # Deletar do Supabase se existir
                    try:
                        if sienge_id:
                            self.supabase.table('sienge_comissoes').delete()\
                                .eq('sienge_id', sienge_id).execute()
                    except:
                        pass
                    cancelados += 1
                    continue
                
                # Pular se não tem ID válido
                if not sienge_id:
                    print(f"[Sync AVISO] Comissão sem ID válido: {commission.get('brokerName')} - {commission.get('salesContractNumber')}")
                    continue
                
                # Comissões pagas são automaticamente marcadas como Aprovadas
                release_value = commission.get('releaseValue') or 0
                payment_bills = commission.get('paymentBills') or []
                is_paga = 'PAID' in status or 'PAGO' in status or release_value > 0 or len(payment_bills) > 0
                if is_paga:
                    pagos += 1
                
                # Buscar status de aprovação existente (para não sobrescrever)
                if is_paga:
                    status_aprovacao = 'Aprovada'
                else:
                    status_aprovacao = 'Pendente'
                    try:
                        existing = self.supabase.table('sienge_comissoes')\
                            .select('status_aprovacao')\
                            .eq('sienge_id', sienge_id)\
                            .limit(1).execute()
                        if existing.data and existing.data[0].get('status_aprovacao'):
                            status_aprovacao = existing.data[0]['status_aprovacao']
                    except:
                        pass
                
                # Valor da comissão - na v1 o campo é 'value'
                valor_comissao = (
                    commission.get('value') or 
                    commission.get('commissionValue') or 
                    commission.get('installmentValue') or 
                    commission.get('totalValue') or
                    0
                )
                
                # Log para debug (apenas primeira comissão não cancelada)
                if count == 0:
                    print(f"[Sync DEBUG] Campos da comissão: {list(commission.keys())}")
                    print(f"[Sync DEBUG] sienge_id={sienge_id}, valor={valor_comissao}")
                
                data = {
                    'sienge_id': sienge_id,
                    'numero_contrato': commission.get('salesContractNumber') or commission.get('contractNumber'),
                    'building_id': commission.get('enterpriseID') or commission.get('enterpriseId') or commission.get('buildingId'),
                    'company_id': commission.get('companyId'),
                    'broker_id': commission.get('brokerID') or commission.get('brokerId'),
                    'broker_nome': commission.get('brokerName'),
                    'customer_name': commission.get('customerName'),
                    'enterprise_name': commission.get('enterpriseName') or commission.get('buildingName'),
                    'unit_name': commission.get('unitName'),
                    'commission_value': valor_comissao,
                    'installment_status': commission.get('installmentStatus') or commission.get('status') or 'PENDING',
                    'commission_date': commission.get('dueDate') or commission.get('contractDate'),
                    'status_aprovacao': status_aprovacao,
                    'atualizado_em': datetime.now().isoformat()
                }
                
                self.supabase.table('sienge_comissoes').upsert(
                    data,
                    on_conflict='sienge_id'
                ).execute()
                count += 1
            
            print(f"[Sync] Comissões: {count} sincronizadas, {cancelados} canceladas ignoradas, {pagos} pagas ignoradas")
            return {'sucesso': True, 'total': count, 'cancelados': cancelados, 'pagos': pagos}
        except Exception as e:
            print(f"Erro ao sincronizar comissões: {str(e)}")
            return {'sucesso': False, 'erro': str(e)}
    
    def sync_itbi(self, building_id: int = None) -> dict:
        """Sincroniza valores de ITBI - todas as empresas (busca detalhes de cada contrato)"""
        try:
            # Buscar lista de contratos
            contracts = self.sienge.get_contracts_all_companies()
            count = 0
            total = len(contracts)
            
            for idx, contract in enumerate(contracts, 1):
                contract_id = contract.get('id')
                if not contract_id:
                    continue
                
                # Buscar detalhes do contrato para obter ITBI
                try:
                    details = self.sienge.get_contract_details(contract_id)
                    if not details:
                        continue
                    
                    # ITBI pode estar em vários campos possíveis
                    itbi_value = (
                        details.get('itbiValue') or 
                        details.get('taxValue') or 
                        details.get('transferTaxValue') or
                        0
                    )
                    
                    if itbi_value and float(itbi_value) > 0:
                        data = {
                            'numero_contrato': details.get('number') or details.get('contractNumber'),
                            'building_id': details.get('enterpriseId') or details.get('buildingId'),
                            'valor_itbi': float(itbi_value),
                            'atualizado_em': datetime.now().isoformat()
                        }
                        
                        self.supabase.table('sienge_itbi').upsert(
                            data,
                            on_conflict='numero_contrato,building_id'
                        ).execute()
                        count += 1
                        
                except Exception as e:
                    # Erro ao buscar detalhes, continuar com próximo
                    pass
                
                # Progresso a cada 100 contratos
                if idx % 100 == 0:
                    print(f"[ITBI] Processados {idx}/{total} contratos, {count} com ITBI")
            
            print(f"[ITBI] Concluído: {count} contratos com ITBI de {total} total")
            return {'sucesso': True, 'total': count}
        except Exception as e:
            print(f"Erro ao sincronizar ITBI: {str(e)}")
            return {'sucesso': False, 'erro': str(e)}
    
    def sync_valores_pagos(self, building_id: int = None) -> dict:
        """Sincroniza valores pagos dos contratos - busca detalhes de cada contrato para obter paymentConditions"""
        try:
            # Buscar lista de contratos
            contracts = self.sienge.get_contracts_all_companies()
            count = 0
            total = len(contracts)
            
            for idx, contract in enumerate(contracts, 1):
                contract_id = contract.get('id')
                if not contract_id:
                    continue
                
                # Buscar detalhes do contrato para obter paymentConditions
                try:
                    details = self.sienge.get_contract_details(contract_id)
                    if not details:
                        continue
                    
                    # Calcular valor pago a partir de paymentConditions
                    payment_conditions = details.get('paymentConditions') or []
                    valor_pago = sum(
                        float(pc.get('amountPaid', 0) or 0)
                        for pc in payment_conditions
                    )
                    
                    if valor_pago > 0:
                        data = {
                            'numero_contrato': details.get('number') or details.get('contractNumber'),
                            'building_id': details.get('enterpriseId') or details.get('buildingId'),
                            'valor_pago': valor_pago,
                            'atualizado_em': datetime.now().isoformat()
                        }
                        
                        self.supabase.table('sienge_valor_pago').upsert(
                            data,
                            on_conflict='numero_contrato,building_id'
                        ).execute()
                        count += 1
                        
                except Exception as e:
                    # Erro ao buscar detalhes, continuar com próximo
                    pass
                
                # Progresso a cada 100 contratos
                if idx % 100 == 0:
                    print(f"[Valores Pagos] Processados {idx}/{total} contratos, {count} com valor pago")
            
            print(f"[Valores Pagos] Concluído: {count} contratos com valor pago de {total} total")
            return {'sucesso': True, 'total': count}
        except Exception as e:
            print(f"Erro ao sincronizar valores pagos: {str(e)}")
            return {'sucesso': False, 'erro': str(e)}
    
    def sync_all(self, building_id: int = None) -> dict:
        """Executa sincronização completa"""
        resultados = {}
        
        print("Sincronizando empreendimentos...")
        resultados['empreendimentos'] = self.sync_empreendimentos()
        
        print("Sincronizando contratos...")
        resultados['contratos'] = self.sync_contratos(building_id)
        
        print("Sincronizando corretores...")
        resultados['corretores'] = self.sync_corretores(building_id)
        
        print("Sincronizando comissões...")
        resultados['comissoes'] = self.sync_comissoes(building_id)
        
        print("Sincronizando ITBI...")
        resultados['itbi'] = self.sync_itbi(building_id)
        
        print("Sincronizando valores pagos...")
        resultados['valores_pagos'] = self.sync_valores_pagos(building_id)
        
        # Registrar última sincronização
        self.registrar_sincronizacao(resultados)
        
        return resultados
    
    def registrar_sincronizacao(self, resultados: dict):
        """Registra log de sincronização"""
        try:
            self.supabase.table('log_sincronizacoes').insert({
                'data_sincronizacao': datetime.now().isoformat(),
                'resultados': resultados,
                'sucesso': all(r.get('sucesso', False) for r in resultados.values())
            }).execute()
        except Exception as e:
            print(f"Erro ao registrar sincronização: {str(e)}")
    
    def get_ultima_sincronizacao(self) -> Optional[dict]:
        """Retorna data da última sincronização"""
        try:
            result = self.supabase.table('log_sincronizacoes')\
                .select('*')\
                .order('data_sincronizacao', desc=True)\
                .limit(1)\
                .execute()
            
            if result.data:
                return result.data[0]
            return None
        except Exception as e:
            print(f"Erro ao buscar última sincronização: {str(e)}")
            return None
    
    # ==================== MÉTODOS DE CONSULTA ====================
    
    def get_empreendimentos(self) -> List[Dict]:
        """Retorna todos os empreendimentos"""
        # Mapeamento de building_id para nome do empreendimento (strings e inteiros)
        EMPREENDIMENTOS = {
            '2003': 'Montecarlo',
            '2004': 'Ilha dos Açores',
            '2005': 'Aurora',
            '2007': 'Parque Lorena I',
            '2009': 'Parque Lorena II',
            '2010': 'Erico Verissimo',
            '2011': 'Algarve',
            '2014': 'Morada da Coxilha',
            2003: 'Montecarlo',
            2004: 'Ilha dos Açores',
            2005: 'Aurora',
            2007: 'Parque Lorena I',
            2009: 'Parque Lorena II',
            2010: 'Erico Verissimo',
            2011: 'Algarve',
            2014: 'Morada da Coxilha'
        }
        
        try:
            # Buscar building_ids unicos de sienge_contratos
            result = self.supabase.table('sienge_contratos')\
                .select('building_id')\
                .execute()
            
            if result.data:
                # Extrair building_ids unicos
                building_ids = set()
                for c in result.data:
                    bid = c.get('building_id')
                    if bid:
                        building_ids.add(bid)
                
                print(f"[Sync] building_ids encontrados: {sorted(building_ids, key=str)}")
                
                # Criar lista de empreendimentos
                empreendimentos = []
                for bid in building_ids:
                    nome = EMPREENDIMENTOS.get(bid, f'Empreendimento {bid}')
                    empreendimentos.append({
                        'sienge_id': bid,
                        'id': bid,
                        'nome': nome
                    })
                
                # Ordenar por nome
                empreendimentos.sort(key=lambda x: x['nome'])
                print(f"[Sync] get_empreendimentos: {len(empreendimentos)} registros")
                return empreendimentos
            return []
        except Exception as e:
            print(f"[Sync] Erro ao buscar empreendimentos: {str(e)}")
            return []
    
    def get_contratos_por_empreendimento(self, building_id: int) -> List[Dict]:
        """Retorna contratos de um empreendimento da tabela sienge_contratos (exclui cancelados)"""
        try:
            result = self.supabase.table('sienge_contratos')\
                .select('*')\
                .eq('building_id', building_id)\
                .order('numero_contrato')\
                .execute()
            data = result.data if result.data else []
            
            # Buscar comissões para identificar contratos cancelados
            result_comissoes = self.supabase.table('sienge_comissoes')\
                .select('numero_contrato, installment_status')\
                .eq('building_id', building_id)\
                .execute()
            
            # Agrupar comissões por contrato e verificar se todas estão canceladas
            contratos_cancelados = set()
            contratos_comissoes = {}
            for c in (result_comissoes.data or []):
                nc = c.get('numero_contrato')
                if nc not in contratos_comissoes:
                    contratos_comissoes[nc] = []
                contratos_comissoes[nc].append(c.get('installment_status') or '')
            
            for nc, statuses in contratos_comissoes.items():
                # Contrato cancelado se TODAS as comissões estão canceladas
                if statuses and all('CANCEL' in s.upper() for s in statuses):
                    contratos_cancelados.add(nc)
            
            # Filtrar contratos cancelados
            data_filtrada = []
            for c in data:
                nc = c.get('numero_contrato')
                if nc in contratos_cancelados:
                    continue
                # Mapear unidades -> unidade
                if 'unidades' in c and 'unidade' not in c:
                    c['unidade'] = c.get('unidades')
                data_filtrada.append(c)
            
            print(f"[Sync] get_contratos_por_empreendimento({building_id}): {len(data_filtrada)} registros (excluídos {len(contratos_cancelados)} cancelados)")
            return data_filtrada
        except Exception as e:
            print(f"[Sync] Erro ao buscar contratos: {str(e)}")
            return []
    
    def get_contrato_por_numero(self, numero_contrato: str, building_id) -> Optional[Dict]:
        """Retorna um contrato pelo numero da tabela sienge_contratos"""
        try:
            print(f"[Sync] get_contrato_por_numero: numero_contrato={numero_contrato}, building_id={building_id}")
            result = self.supabase.table('sienge_contratos')\
                .select('*')\
                .eq('numero_contrato', numero_contrato)\
                .eq('building_id', building_id)\
                .limit(1)\
                .execute()
            contrato = result.data[0] if result.data else None
            if contrato:
                print(f"[Sync] Contrato encontrado: {contrato.get('numero_contrato')}")
            else:
                print(f"[Sync] Contrato NAO encontrado")
            return contrato
        except Exception as e:
            print(f"[Sync] Erro ao buscar contrato: {str(e)}")
            return None
    
    def get_corretores(self) -> List[Dict]:
        """Retorna todos os corretores extraidos de sienge_contratos"""
        try:
            # Tentar tabela sienge_corretores primeiro
            result = self.supabase.table('sienge_corretores')\
                .select('*')\
                .eq('ativo', True)\
                .order('nome')\
                .execute()
            data = result.data if result.data else []
            if data:
                print(f"[Sync] get_corretores: {len(data)} registros")
                return data
        except Exception as e:
            print(f"[Sync] Tabela sienge_corretores nao encontrada...")
        
        # Fallback: extrair corretores unicos de sienge_contratos
        try:
            result = self.supabase.table('sienge_contratos')\
                .select('corretor_id, corretor')\
                .execute()
            
            if result.data:
                corretores_map = {}
                for c in result.data:
                    cid = c.get('corretor_id')
                    nome = c.get('corretor')
                    if cid and nome and cid not in corretores_map:
                        corretores_map[cid] = {
                            'sienge_id': cid,
                            'id': cid,
                            'nome': nome,
                            'ativo': True
                        }
                
                data = sorted(corretores_map.values(), key=lambda x: x['nome'] or '')
                print(f"[Sync] get_corretores (de sienge_contratos): {len(data)} registros")
                return data
            return []
        except Exception as e2:
            print(f"[Sync] Erro ao buscar corretores: {str(e2)}")
            return []
    
    def get_comissoes_por_corretor(self, corretor_id: int = None, corretor_nome: str = None) -> List[Dict]:
        """Retorna comissões de um corretor"""
        try:
            query = self.supabase.table('sienge_comissoes').select('*')
            
            if corretor_id:
                query = query.eq('broker_id', corretor_id)
            elif corretor_nome:
                query = query.ilike('broker_nome', f'%{corretor_nome}%')
            
            result = query.execute()
            return result.data if result.data else []
        except Exception as e:
            print(f"Erro ao buscar comissões do corretor: {str(e)}")
            return []
    
    def get_itbi_por_contrato(self, numero_contrato: str, building_id: int) -> Optional[float]:
        """Retorna valor ITBI de um contrato"""
        try:
            result = self.supabase.table('sienge_itbi')\
                .select('valor_itbi')\
                .eq('numero_contrato', numero_contrato)\
                .eq('building_id', building_id)\
                .limit(1)\
                .execute()
            
            if result.data:
                return result.data[0].get('valor_itbi')
            return None
        except Exception as e:
            print(f"Erro ao buscar ITBI: {str(e)}")
            return None
    
    def get_valor_pago_por_contrato(self, numero_contrato: str, building_id: int) -> Optional[float]:
        """Retorna valor pago de um contrato"""
        try:
            result = self.supabase.table('sienge_valor_pago')\
                .select('valor_pago')\
                .eq('numero_contrato', numero_contrato)\
                .eq('building_id', building_id)\
                .limit(1)\
                .execute()
            
            if result.data:
                return result.data[0].get('valor_pago')
            return None
        except Exception as e:
            print(f"Erro ao buscar valor pago: {str(e)}")
            return None
    
    def buscar_contratos_por_lote(self, numero_lote: str) -> List[Dict]:
        """Busca contratos que contenham o numero do lote na tabela sienge_contratos"""
        import json
        
        # Mapeamento de building_id para nome do empreendimento (strings e inteiros)
        EMPREENDIMENTOS = {
            '2003': 'Montecarlo',
            '2004': 'Ilha dos Açores',
            '2005': 'Aurora',
            '2007': 'Parque Lorena I',
            '2009': 'Parque Lorena II',
            '2010': 'Erico Verissimo',
            '2011': 'Algarve',
            '2014': 'Morada da Coxilha',
            2003: 'Montecarlo',
            2004: 'Ilha dos Açores',
            2005: 'Aurora',
            2007: 'Parque Lorena I',
            2009: 'Parque Lorena II',
            2010: 'Erico Verissimo',
            2011: 'Algarve',
            2014: 'Morada da Coxilha'
        }
        
        def extrair_numero_lote(unidades_data):
            """Extrai numeros de lote do campo unidades (pode ser jsonb)"""
            if not unidades_data:
                return []
            
            if isinstance(unidades_data, list):
                # Ja e uma lista de objetos
                return [str(u.get('name', '')) for u in unidades_data if isinstance(u, dict)]
            elif isinstance(unidades_data, str):
                try:
                    parsed = json.loads(unidades_data)
                    if isinstance(parsed, list):
                        return [str(u.get('name', '')) for u in parsed if isinstance(u, dict)]
                except:
                    return [unidades_data]
            return [str(unidades_data)]
        
        try:
            # Buscar por numero_contrato ou nome_cliente (campos texto)
            result = self.supabase.table('sienge_contratos')\
                .select('*')\
                .or_(f'numero_contrato.ilike.%{numero_lote}%,nome_cliente.ilike.%{numero_lote}%')\
                .limit(100)\
                .execute()
            
            contratos_texto = result.data if result.data else []
            
            # Tambem buscar todos e filtrar pelo campo unidades em Python
            result_all = self.supabase.table('sienge_contratos')\
                .select('*')\
                .limit(2000)\
                .execute()
            
            contratos_por_unidade = []
            if result_all.data:
                for c in result_all.data:
                    lotes = extrair_numero_lote(c.get('unidades'))
                    # Verificar se algum lote contem o termo buscado
                    if any(numero_lote.lower() in lote.lower() for lote in lotes):
                        contratos_por_unidade.append(c)
            
            # Buscar comissões para identificar contratos cancelados
            result_comissoes = self.supabase.table('sienge_comissoes')\
                .select('numero_contrato, building_id, installment_status')\
                .execute()
            
            # Agrupar comissões por contrato e verificar se todas estão canceladas
            contratos_cancelados = set()
            contratos_comissoes = {}
            for c in (result_comissoes.data or []):
                chave = f"{c.get('numero_contrato')}_{c.get('building_id')}"
                if chave not in contratos_comissoes:
                    contratos_comissoes[chave] = []
                contratos_comissoes[chave].append(c.get('installment_status') or '')
            
            for chave, statuses in contratos_comissoes.items():
                if statuses and all('CANCEL' in s.upper() for s in statuses):
                    contratos_cancelados.add(chave)
            
            # Combinar resultados sem duplicatas e filtrar cancelados
            contratos_ids = set()
            contratos = []
            
            for c in contratos_texto + contratos_por_unidade:
                # Filtrar cancelados (baseado nas comissões)
                chave = f"{c.get('numero_contrato')}_{c.get('building_id')}"
                if chave in contratos_cancelados:
                    continue
                    
                cid = c.get('sienge_id') or c.get('id') or c.get('numero_contrato')
                if cid not in contratos_ids:
                    contratos_ids.add(cid)
                    contratos.append(c)
            
            # Limitar a 50 resultados
            contratos = contratos[:50]
            
            # Mapear campos para o formato esperado pelo frontend
            for c in contratos:
                # Mapear unidades -> unidade
                if 'unidades' in c and 'unidade' not in c:
                    c['unidade'] = c.get('unidades')
                # Adicionar nome do empreendimento
                bid = c.get('building_id')
                c['sienge_empreendimentos'] = {'nome': EMPREENDIMENTOS.get(bid, f'Empreendimento {bid}')}
            
            print(f"[Sync] buscar_contratos_por_lote('{numero_lote}'): {len(contratos)} registros")
            return contratos
        except Exception as e:
            print(f"[Sync] Erro ao buscar contratos por lote: {str(e)}")
            return []
