"""
Cliente da API Sienge - Sistema de Comissões Young
Gerencia comunicação com a API do Sienge para buscar dados de contratos, comissões, etc.
"""

import os
import requests
from requests.auth import HTTPBasicAuth
from typing import Optional, List, Dict
from dotenv import load_dotenv

load_dotenv()


class SiengeClient:
    """Cliente para API do Sienge"""
    
    def __init__(self):
        # URL atualizada para v1 (mudança do Sienge em 2026)
        self.base_url = os.getenv('SIENGE_BASE_URL', 'https://api.sienge.com.br/youngemp/public/api/v1')
        self.username = os.getenv('SIENGE_USERNAME')
        self.password = os.getenv('SIENGE_PASSWORD')
        self.company_id = os.getenv('SIENGE_COMPANY_ID', '5')
        # Lista de todas as empresas para sincronizar
        company_ids_str = os.getenv('SIENGE_COMPANY_IDS', '5')
        self.all_company_ids = [c.strip() for c in company_ids_str.split(',') if c.strip()]
        self.auth = HTTPBasicAuth(self.username, self.password)
        self.timeout = 30
    
    def _make_request(self, endpoint: str, params: dict = None) -> Optional[dict]:
        """Faz requisição à API do Sienge"""
        try:
            url = f"{self.base_url}/{endpoint}"
            response = requests.get(
                url,
                auth=self.auth,
                params=params,
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Erro na requisição Sienge: {str(e)}")
            return None
    
    def get_buildings(self) -> List[Dict]:
        """Busca todos os empreendimentos"""
        try:
            # Endpoint renomeado de 'buildings' para 'enterprises' na v1
            result = self._make_request('enterprises', {'companyId': self.company_id})
            if result and 'resultSetMetadata' in result:
                return result.get('results', [])
            return result if isinstance(result, list) else []
        except Exception as e:
            print(f"Erro ao buscar empreendimentos: {str(e)}")
            return []
    
    def get_building_units(self, building_id: int) -> List[Dict]:
        """Busca unidades de um empreendimento"""
        try:
            # Endpoint mudou na v1: de 'buildings/{id}/units' para 'units?enterpriseId={id}'
            result = self._make_request('units', {
                'companyId': self.company_id,
                'enterpriseId': building_id
            })
            if result and 'resultSetMetadata' in result:
                return result.get('results', [])
            return result if isinstance(result, list) else []
        except Exception as e:
            print(f"Erro ao buscar unidades: {str(e)}")
            return []
    
    def get_contracts(self, building_id: int = None, offset: int = 0, limit: int = 100) -> List[Dict]:
        """Busca contratos"""
        try:
            params = {
                'companyId': self.company_id,
                'offset': offset,
                'limit': limit
            }
            if building_id:
                params['buildingId'] = building_id
            
            result = self._make_request('sales-contracts', params)
            if result and 'resultSetMetadata' in result:
                return result.get('results', [])
            return result if isinstance(result, list) else []
        except Exception as e:
            print(f"Erro ao buscar contratos: {str(e)}")
            return []
    
    def get_contract_details(self, contract_id: int) -> Optional[Dict]:
        """Busca detalhes de um contrato específico"""
        try:
            return self._make_request(f'sales-contracts/{contract_id}')
        except Exception as e:
            print(f"Erro ao buscar detalhes do contrato: {str(e)}")
            return None
    
    def get_contract_by_number(self, contract_number: str, building_id: int) -> Optional[Dict]:
        """Busca contrato pelo número"""
        try:
            contracts = self.get_contracts(building_id=building_id, limit=500)
            for contract in contracts:
                if str(contract.get('contractNumber')) == str(contract_number):
                    return contract
            return None
        except Exception as e:
            print(f"Erro ao buscar contrato por número: {str(e)}")
            return None
    
    def get_brokers(self, building_id: int = None) -> List[Dict]:
        """Busca corretores - Usa endpoint /commissions/configurations/brokers na v1"""
        try:
            # Na v1, corretores ficam em /commissions/configurations/brokers
            result = self._make_request('commissions/configurations/brokers', {
                'companyId': self.company_id
            })
            if result and 'resultSetMetadata' in result:
                return result.get('results', [])
            return result if isinstance(result, list) else []
        except Exception as e:
            print(f"Erro ao buscar corretores: {str(e)}")
            return []
    
    def get_broker_commissions(self, broker_id: int, building_id: int = None) -> List[Dict]:
        """Busca comissões de um corretor"""
        try:
            params = {
                'companyId': self.company_id,
                'brokerId': broker_id
            }
            if building_id:
                params['enterpriseId'] = building_id
            
            # Na v1, endpoint mudou de 'broker-commissions' para 'commissions'
            result = self._make_request('commissions', params)
            if result and 'resultSetMetadata' in result:
                return result.get('results', [])
            return result if isinstance(result, list) else []
        except Exception as e:
            print(f"Erro ao buscar comissões do corretor: {str(e)}")
            return []
    
    def get_commissions(self, building_id: int = None, offset: int = 0, limit: int = 100) -> List[Dict]:
        """Busca todas as comissões"""
        try:
            params = {
                'companyId': self.company_id,
                'offset': offset,
                'limit': limit
            }
            if building_id:
                params['enterpriseId'] = building_id
            
            # Na v1, endpoint mudou de 'broker-commissions' para 'commissions'
            result = self._make_request('commissions', params)
            if result and 'resultSetMetadata' in result:
                return result.get('results', [])
            return result if isinstance(result, list) else []
        except Exception as e:
            print(f"Erro ao buscar comissões: {str(e)}")
            return []
    
    def get_customers(self, building_id: int = None) -> List[Dict]:
        """Busca clientes"""
        try:
            params = {'companyId': self.company_id}
            if building_id:
                params['buildingId'] = building_id
            
            result = self._make_request('customers', params)
            if result and 'resultSetMetadata' in result:
                return result.get('results', [])
            return result if isinstance(result, list) else []
        except Exception as e:
            print(f"Erro ao buscar clientes: {str(e)}")
            return []
    
    def get_receivables(self, contract_id: int) -> List[Dict]:
        """Busca parcelas/recebíveis de um contrato - Endpoint não disponível na v1"""
        # Na v1 da API Sienge, o endpoint de receivables não está disponível
        # Os dados de parcelas vêm através de broker-commissions (paymentBills)
        print(f"[AVISO] Endpoint receivables não disponível na v1 da API Sienge")
        return []
    
    def get_all_contracts_paginated(self, building_id: int = None) -> List[Dict]:
        """Busca todos os contratos com paginação automática"""
        all_contracts = []
        offset = 0
        limit = 100
        
        while True:
            contracts = self.get_contracts(building_id=building_id, offset=offset, limit=limit)
            if not contracts:
                break
            all_contracts.extend(contracts)
            if len(contracts) < limit:
                break
            offset += limit
        
        return all_contracts
    
    def get_all_commissions_paginated(self, building_id: int = None) -> List[Dict]:
        """Busca todas as comissões com paginação automática"""
        all_commissions = []
        offset = 0
        limit = 100
        
        while True:
            commissions = self.get_commissions(building_id=building_id, offset=offset, limit=limit)
            if not commissions:
                break
            all_commissions.extend(commissions)
            if len(commissions) < limit:
                break
            offset += limit
        
        return all_commissions
    
    def get_commissions_all_companies(self) -> List[Dict]:
        """Busca comissões de TODAS as empresas cadastradas"""
        all_commissions = []
        original_company_id = self.company_id
        
        for company_id in self.all_company_ids:
            self.company_id = company_id
            try:
                commissions = self.get_all_commissions_paginated()
                if commissions:
                    print(f"[Sienge] Empresa {company_id}: {len(commissions)} comissões")
                    all_commissions.extend(commissions)
            except Exception as e:
                print(f"[Sienge] Erro na empresa {company_id}: {str(e)}")
        
        self.company_id = original_company_id
        print(f"[Sienge] Total de comissões (todas empresas): {len(all_commissions)}")
        return all_commissions
    
    def get_contracts_all_companies(self) -> List[Dict]:
        """Busca contratos de TODAS as empresas cadastradas"""
        all_contracts = []
        original_company_id = self.company_id
        
        for company_id in self.all_company_ids:
            self.company_id = company_id
            try:
                contracts = self.get_all_contracts_paginated()
                if contracts:
                    print(f"[Sienge] Empresa {company_id}: {len(contracts)} contratos")
                    all_contracts.extend(contracts)
            except Exception as e:
                print(f"[Sienge] Erro na empresa {company_id}: {str(e)}")
        
        self.company_id = original_company_id
        print(f"[Sienge] Total de contratos (todas empresas): {len(all_contracts)}")
        return all_contracts
    
    def get_buildings_all_companies(self) -> List[Dict]:
        """Busca empreendimentos de TODAS as empresas cadastradas"""
        all_buildings = []
        original_company_id = self.company_id
        
        for company_id in self.all_company_ids:
            self.company_id = company_id
            try:
                buildings = self.get_buildings()
                if buildings:
                    print(f"[Sienge] Empresa {company_id}: {len(buildings)} empreendimentos")
                    all_buildings.extend(buildings)
            except Exception as e:
                print(f"[Sienge] Erro na empresa {company_id}: {str(e)}")
        
        self.company_id = original_company_id
        print(f"[Sienge] Total de empreendimentos (todas empresas): {len(all_buildings)}")
        return all_buildings
    
    def get_bill_prv(self, document_number: str) -> Optional[Dict]:
        """Busca título a pagar PRV (ITBI) pelo número do documento"""
        try:
            params = {
                'companyId': self.company_id,
                'documentId': 'PRV',
                'documentNumber': document_number,
                'startDate': '2020-01-01',
                'endDate': '2030-12-31',
                'limit': 10
            }
            result = self._make_request('bills', params)
            if result and 'results' in result and result['results']:
                return result['results'][0]
            return None
        except Exception as e:
            print(f"Erro ao buscar PRV: {str(e)}")
            return None
    
    def get_bills_prv_all_companies(self, document_number: str) -> Optional[Dict]:
        """Busca título PRV em TODAS as empresas"""
        original_company_id = self.company_id
        
        for company_id in self.all_company_ids:
            self.company_id = company_id
            try:
                bill = self.get_bill_prv(document_number)
                if bill:
                    self.company_id = original_company_id
                    return bill
            except:
                pass
        
        self.company_id = original_company_id
        return None
    
    def get_receivable_bills(self, offset: int = 0, limit: int = 100) -> List[Dict]:
        """Busca títulos a receber (valores pagos)"""
        try:
            params = {
                'companyId': self.company_id,
                'offset': offset,
                'limit': limit
            }
            result = self._make_request('accounts-receivable/receivable-bills', params)
            if result and 'results' in result:
                return result.get('results', [])
            return result if isinstance(result, list) else []
        except Exception as e:
            print(f"Erro ao buscar receivable-bills: {str(e)}")
            return []
    
    def get_all_receivable_bills_paginated(self) -> List[Dict]:
        """Busca todos os títulos a receber com paginação"""
        all_bills = []
        offset = 0
        limit = 100
        
        while True:
            bills = self.get_receivable_bills(offset=offset, limit=limit)
            if not bills:
                break
            all_bills.extend(bills)
            if len(bills) < limit:
                break
            offset += limit
        
        return all_bills
    
    def get_receivable_bills_all_companies(self) -> List[Dict]:
        """Busca títulos a receber de TODAS as empresas"""
        all_bills = []
        original_company_id = self.company_id
        
        for company_id in self.all_company_ids:
            self.company_id = company_id
            try:
                bills = self.get_all_receivable_bills_paginated()
                if bills:
                    print(f"[Sienge] Empresa {company_id}: {len(bills)} títulos a receber")
                    all_bills.extend(bills)
            except Exception as e:
                print(f"[Sienge] Erro na empresa {company_id}: {str(e)}")
        
        self.company_id = original_company_id
        print(f"[Sienge] Total de títulos a receber (todas empresas): {len(all_bills)}")
        return all_bills


# Instância global
sienge_client = SiengeClient()
