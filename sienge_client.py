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
        # URL da API v1 do Sienge
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
            print(f"Erro na requisicao Sienge: {str(e)}")
            return None
    
    def get_buildings(self) -> List[Dict]:
        """Busca todos os empreendimentos"""
        try:
            # Na API v1, o endpoint é 'enterprises'
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
        """Busca contratos com dados completos incluindo paymentConditions"""
        try:
            params = {
                'companyId': self.company_id,
                'offset': offset,
                'limit': limit
            }
            if building_id:
                params['enterpriseId'] = building_id
            
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
                if str(contract.get('number')) == str(contract_number):
                    return contract
            return None
        except Exception as e:
            print(f"Erro ao buscar contrato por numero: {str(e)}")
            return None
    
    def get_brokers(self, building_id: int = None) -> List[Dict]:
        """Busca corretores"""
        try:
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
            
            result = self._make_request('commissions', params)
            if result and 'resultSetMetadata' in result:
                return result.get('results', [])
            return result if isinstance(result, list) else []
        except Exception as e:
            print(f"Erro ao buscar comissoes do corretor: {str(e)}")
            return []
    
    def get_commissions(self, building_id: int = None, offset: int = 0, limit: int = 100, include_cancelled: bool = True) -> List[Dict]:
        """Busca todas as comissões (incluindo canceladas por padrão)"""
        try:
            params = {
                'companyId': self.company_id,
                'offset': offset,
                'limit': limit
            }
            if building_id:
                params['enterpriseId'] = building_id
            
            result = self._make_request('commissions', params)
            if result and 'resultSetMetadata' in result:
                return result.get('results', [])
            return result if isinstance(result, list) else []
        except Exception as e:
            print(f"Erro ao buscar comissoes: {str(e)}")
            return []
    
    def get_commission_details(self, commission_id: int) -> Optional[Dict]:
        """Busca detalhes de uma comissão específica (inclui baseValue)"""
        try:
            return self._make_request(f'commissions/{commission_id}')
        except Exception as e:
            print(f"Erro ao buscar detalhes da comissao {commission_id}: {str(e)}")
            return None
    
    def get_commissions_by_contract(self, contract_id: int) -> List[Dict]:
        """Busca comissões de um contrato específico pelo linkedCommissions"""
        try:
            contract = self.get_contract_details(contract_id)
            if contract:
                return contract.get('linkedCommissions', [])
            return []
        except Exception as e:
            print(f"Erro ao buscar comissoes do contrato: {str(e)}")
            return []
    
    def get_customers(self, building_id: int = None) -> List[Dict]:
        """Busca clientes"""
        try:
            params = {'companyId': self.company_id}
            if building_id:
                params['enterpriseId'] = building_id
            
            result = self._make_request('customers', params)
            if result and 'resultSetMetadata' in result:
                return result.get('results', [])
            return result if isinstance(result, list) else []
        except Exception as e:
            print(f"Erro ao buscar clientes: {str(e)}")
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
    
    def get_commissions_all_companies(self) -> List[Dict]:
        """Busca comissões de TODAS as empresas cadastradas"""
        all_commissions = []
        original_company_id = self.company_id
        
        for company_id in self.all_company_ids:
            self.company_id = company_id
            try:
                commissions = self.get_all_commissions_paginated()
                if commissions:
                    print(f"[Sienge] Empresa {company_id}: {len(commissions)} comissoes")
                    all_commissions.extend(commissions)
            except Exception as e:
                print(f"[Sienge] Erro na empresa {company_id}: {str(e)}")
        
        self.company_id = original_company_id
        print(f"[Sienge] Total de comissoes (todas empresas): {len(all_commissions)}")
        return all_commissions
    
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
    
    def extract_itbi_from_contract(self, contract: Dict) -> Optional[Dict]:
        """Extrai dados de ITBI do paymentConditions de um contrato
        
        Retorna dict com:
        - valor_itbi: valor total do ITBI
        - valor_pago: valor já pago
        - data_vencimento: primeira data de vencimento
        - documento: descrição
        """
        payment_conditions = contract.get('paymentConditions', [])
        if not payment_conditions:
            return None
        
        # Buscar condições do tipo "DC" (Despesa de Registro e ITBI)
        itbi_total = 0
        itbi_pago = 0
        data_vencimento = None
        
        for pc in payment_conditions:
            if pc.get('conditionTypeId') == 'DC':
                itbi_total += float(pc.get('totalValue', 0) or 0)
                itbi_pago += float(pc.get('amountPaid', 0) or 0)
                if not data_vencimento and pc.get('firstPayment'):
                    data_vencimento = pc.get('firstPayment')
        
        if itbi_total > 0:
            return {
                'valor_itbi': itbi_total,
                'valor_pago': itbi_pago,
                'data_vencimento': data_vencimento,
                'documento': f"ITBI Contrato {contract.get('number')}"
            }
        return None
    
    def extract_valor_pago_from_contract(self, contract: Dict) -> float:
        """Extrai valor total pago de todas as condições de pagamento"""
        payment_conditions = contract.get('paymentConditions', [])
        if not payment_conditions:
            return 0
        
        total_pago = 0
        for pc in payment_conditions:
            total_pago += float(pc.get('amountPaid', 0) or 0)
        
        return total_pago


# Instância global
sienge_client = SiengeClient()
