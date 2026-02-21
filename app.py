"""
Sistema de Comissões - Young Empreendimentos
Aplicação Flask principal com todas as rotas e funcionalidades
"""

import os
import re
import logging
from datetime import datetime
from flask import Flask, render_template, jsonify, request, redirect, url_for, flash, session
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_cors import CORS
from dotenv import load_dotenv
from apscheduler.schedulers.background import BackgroundScheduler

# Importar módulos do sistema
from auth_manager import AuthManager, traduzir_status, Usuario, CorretorUser
from sienge_client import sienge_client
from sync_sienge_supabase import SiengeSupabaseSync
from aprovacao_comissoes import AprovacaoComissoes

load_dotenv()

# ==================== CONFIGURAÇÃO DE LOGGING ====================
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ==================== VALIDAÇÃO DE AMBIENTE ====================
# Variáveis obrigatórias
REQUIRED_ENV_VARS = ['SUPABASE_URL', 'SUPABASE_KEY', 'SECRET_KEY']
missing_vars = [var for var in REQUIRED_ENV_VARS if not os.getenv(var)]

if missing_vars:
    logger.error(f"Variáveis de ambiente obrigatórias faltando: {', '.join(missing_vars)}")
    logger.error("Execute: python validate_env.py")
    raise EnvironmentError(f"Variáveis faltando: {', '.join(missing_vars)}")

# Validar SECRET_KEY
SECRET_KEY = os.getenv('SECRET_KEY')
if SECRET_KEY == 'young-empreendimentos-comissoes-2024':
    logger.error("SECRET_KEY está usando valor padrão INSEGURO!")
    raise EnvironmentError("SECRET_KEY insegura! Gere uma nova: python -c \"import secrets; print(secrets.token_hex(32))\"")

if len(SECRET_KEY) < 32:
    logger.warning(f"SECRET_KEY muito curta ({len(SECRET_KEY)} caracteres, recomendado 64+)")

# ==================== INICIALIZAR FLASK ====================
app = Flask(__name__)
app.secret_key = SECRET_KEY

# Configurar CORS de forma restritiva
PRODUCTION_URL = os.getenv('PRODUCTION_URL', 'http://localhost:5000')
CORS(app, 
     origins=[PRODUCTION_URL, 'http://localhost:5000', 'http://127.0.0.1:5000'],
     supports_credentials=True,
     allow_headers=['Content-Type', 'Authorization'],
     methods=['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'])

# Limite de tamanho de upload
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB

logger.info(f"Flask app inicializado. CORS configurado para: {PRODUCTION_URL}")

# Configurar Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Por favor, faça login para acessar esta página.'

# Inicializar AuthManager
auth_manager = AuthManager()


# Função para calcular o valor do gatilho a partir da string de regra
def calcular_valor_gatilho(valor_a_vista: float, valor_itbi: float, regra: str) -> float:
    if not regra:
        regra = '10% + ITBI'
    
    regra_lower = regra.lower().strip()
    
    if '10%' in regra_lower and 'itbi' in regra_lower:
        return (valor_a_vista * 0.10) + valor_itbi
    elif '10%' in regra_lower:
        return valor_a_vista * 0.10
    elif '5%' in regra_lower:
        return valor_a_vista * 0.05
    elif '6%' in regra_lower:
        return valor_a_vista * 0.06
    else:
        match = re.search(r'(\d+[,.]?\d*)\s*%', regra)
        if match:
            percentual = float(match.group(1).replace(',', '.')) / 100
            if 'itbi' in regra_lower:
                return (valor_a_vista * percentual) + valor_itbi
            return valor_a_vista * percentual
        return (valor_a_vista * 0.10) + valor_itbi


def obter_gatilho_contrato(sync, numero_contrato, building_id, comissao_record=None):
    """
    Função centralizada que calcula o gatilho de um contrato.
    Garante consistência entre todas as telas (consulta por contrato, visualizar comissões, etc.)
    
    Retorna dict com: valor_gatilho, atingiu_gatilho, valor_pago, regra_gatilho, valor_a_vista, valor_itbi
    """
    resultado = {
        'valor_gatilho': 0,
        'atingiu_gatilho': False,
        'valor_pago': 0,
        'regra_gatilho': '10% + ITBI',
        'valor_a_vista': 0,
        'valor_itbi': 0
    }
    
    if not numero_contrato or not building_id:
        return resultado
    
    # Normalizar building_id para garantir consistência nas buscas
    building_id_str = str(building_id)
    numero_contrato_str = str(numero_contrato)
    
    print(f"[obter_gatilho] Contrato: {numero_contrato_str}, Building: {building_id}")
    
    try:
        # 1. Buscar contrato para pegar valor_a_vista
        contrato = sync.get_contrato_por_numero(numero_contrato_str, building_id)
        if not contrato:
            # Tentar com building_id como int
            try:
                contrato = sync.get_contrato_por_numero(numero_contrato_str, int(building_id_str))
            except (ValueError, TypeError):
                pass
        
        valor_a_vista = 0
        if contrato:
            valor_a_vista = float(contrato.get('valor_a_vista') or contrato.get('valor_total') or 0)
        
        # 2. Buscar ITBI
        valor_itbi = sync.get_itbi_por_contrato(numero_contrato_str, building_id) or 0
        if not valor_itbi:
            try:
                valor_itbi = sync.get_itbi_por_contrato(numero_contrato_str, int(building_id_str)) or 0
            except (ValueError, TypeError):
                pass
        
        # 3. Buscar valor pago
        valor_pago = sync.get_valor_pago_por_contrato(numero_contrato_str, building_id) or 0
        if not valor_pago:
            try:
                valor_pago = sync.get_valor_pago_por_contrato(numero_contrato_str, int(building_id_str)) or 0
            except (ValueError, TypeError):
                pass
        
        # 4. Determinar a regra do gatilho
        # Prioridade: regra_gatilho_id -> regras_gatilho table (dados estruturados)
        #             regra_gatilho text field (campo texto legacy)
        #             Default: 10% + ITBI
        regra_gatilho_texto = '10% + ITBI'
        percentual = None
        inclui_itbi = None
        
        # Se temos o registro da comissão, usar dele
        if not comissao_record:
            try:
                comissao_result = sync.supabase.table('sienge_comissoes')\
                    .select('regra_gatilho, regra_gatilho_id')\
                    .eq('numero_contrato', numero_contrato_str)\
                    .eq('building_id', building_id)\
                    .limit(1)\
                    .execute()
                if comissao_result.data:
                    comissao_record = comissao_result.data[0]
            except Exception:
                pass
        
        if comissao_record:
            # Tentar buscar a regra estruturada pela regra_gatilho_id
            regra_id = comissao_record.get('regra_gatilho_id')
            if regra_id:
                try:
                    regra_result = sync.supabase.table('regras_gatilho')\
                        .select('percentual, inclui_itbi, nome, tipo_regra')\
                        .eq('id', regra_id)\
                        .limit(1)\
                        .execute()
                    if regra_result.data:
                        regra_data = regra_result.data[0]
                        percentual = regra_data.get('percentual')
                        inclui_itbi = regra_data.get('inclui_itbi')
                        nome = regra_data.get('nome', '')
                        tipo_regra = regra_data.get('tipo_regra', 'gatilho')
                        
                        if percentual is not None:
                            if inclui_itbi:
                                regra_gatilho_texto = f"{percentual}% + ITBI"
                            else:
                                regra_gatilho_texto = f"{percentual}%"
                except Exception as e:
                    print(f"[obter_gatilho] Erro ao buscar regra {regra_id}: {str(e)}")
            
            # Se não encontrou pela ID, usar o campo texto
            if percentual is None:
                regra_texto = comissao_record.get('regra_gatilho')
                if regra_texto:
                    regra_gatilho_texto = regra_texto
        
        # 5. Calcular valor do gatilho
        if percentual is not None:
            # Usar dados estruturados (mais confiável)
            perc = float(percentual) / 100.0
            if inclui_itbi:
                valor_gatilho = (valor_a_vista * perc) + float(valor_itbi)
            else:
                valor_gatilho = valor_a_vista * perc
        else:
            # Fallback: usar a função de parse de texto
            valor_gatilho = calcular_valor_gatilho(valor_a_vista, float(valor_itbi), regra_gatilho_texto)
        
        # 6. Verificar se atingiu (valor pago >= valor gatilho)
        atingiu_gatilho = float(valor_pago) >= valor_gatilho if valor_gatilho > 0 else False
        
        resultado = {
            'valor_gatilho': valor_gatilho,
            'atingiu_gatilho': atingiu_gatilho,
            'valor_pago': float(valor_pago),
            'regra_gatilho': regra_gatilho_texto,
            'valor_a_vista': valor_a_vista,
            'valor_itbi': float(valor_itbi)
        }
        
        print(f"[obter_gatilho] Resultado: valor_a_vista={valor_a_vista}, valor_itbi={valor_itbi}, valor_pago={valor_pago}")
        print(f"[obter_gatilho] Regra: {regra_gatilho_texto}, percentual={percentual}, inclui_itbi={inclui_itbi}")
        print(f"[obter_gatilho] valor_gatilho={valor_gatilho}, atingiu={atingiu_gatilho}")
        
    except Exception as e:
        print(f"[obter_gatilho] Erro para contrato {numero_contrato}/{building_id}: {str(e)}")
    
    return resultado


# ==================== FLASK-LOGIN CALLBACKS ====================

@login_manager.user_loader
def load_user(user_id):
    return auth_manager.buscar_usuario_por_id(user_id)


# ==================== ROTAS DE AUTENTICAÇÃO ====================

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        if hasattr(current_user, 'is_corretor') and current_user.is_corretor:
            return redirect(url_for('dashboard_corretor'))
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        senha = request.form.get('senha', '')
        tipo_login = request.form.get('tipo_login', 'gestor')
        
        if tipo_login == 'corretor':
            # Login de corretor (CPF)
            usuario = auth_manager.autenticar_corretor(username, senha)
            if usuario:
                login_user(usuario)
                return redirect(url_for('dashboard_corretor'))
        else:
            # Login de gestor
            usuario = auth_manager.autenticar(username, senha)
            if usuario:
                login_user(usuario)
                # Redirecionar direção para página específica
                if usuario.perfil == 'Direção':
                    return redirect(url_for('dashboard_direcao'))
                return redirect(url_for('dashboard'))
        
        flash('Credenciais inválidas', 'error')
    
    return render_template('login_unificado.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))


# ==================== ROTAS DE SAÚDE E MONITORAMENTO ====================

@app.route('/health')
def health_check():
    """Endpoint de healthcheck para monitoramento"""
    try:
        # Testar conexão com Supabase
        sync = SiengeSupabaseSync()
        sync.supabase.table('usuarios').select('id').limit(1).execute()
        
        return jsonify({
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'service': 'Sistema de Comissões Young',
            'database': 'connected'
        }), 200
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return jsonify({
            'status': 'unhealthy',
            'timestamp': datetime.now().isoformat(),
            'service': 'Sistema de Comissões Young',
            'error': str(e)
        }), 503

@app.route('/api/health')
def api_health_check():
    """Endpoint de healthcheck da API"""
    return health_check()

# ==================== ROTAS PRINCIPAIS ====================

@app.route('/')
def index():
    if current_user.is_authenticated:
        if hasattr(current_user, 'is_corretor') and current_user.is_corretor:
            return redirect(url_for('dashboard_corretor'))
        if hasattr(current_user, 'perfil') and current_user.perfil == 'Direção':
            return redirect(url_for('dashboard_direcao'))
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))


@app.route('/dashboard')
@login_required
def dashboard():
    if hasattr(current_user, 'is_corretor') and current_user.is_corretor:
        return redirect(url_for('dashboard_corretor'))
    if hasattr(current_user, 'perfil') and current_user.perfil == 'Direção':
        return redirect(url_for('dashboard_direcao'))
    return render_template('dashboard.html', user=current_user)


@app.route('/dashboard/corretor')
@login_required
def dashboard_corretor():
    if not hasattr(current_user, 'is_corretor') or not current_user.is_corretor:
        return redirect(url_for('dashboard'))
    return render_template('dashboard_corretor.html', user=current_user)


@app.route('/dashboard/direcao')
@login_required
def dashboard_direcao():
    if not hasattr(current_user, 'perfil') or current_user.perfil != 'Direção':
        return redirect(url_for('dashboard'))
    return render_template('dashboard_direcao.html', user=current_user)


# ==================== API - EMPREENDIMENTOS ====================

@app.route('/api/empreendimentos', methods=['GET'])
@login_required
def listar_empreendimentos():
    try:
        sync = SiengeSupabaseSync()
        empreendimentos = sync.get_empreendimentos()
        if empreendimentos is None:
            empreendimentos = []
        print(f"[API] Empreendimentos encontrados: {len(empreendimentos)}")
        return jsonify(empreendimentos), 200
    except Exception as e:
        print(f"[API] Erro ao listar empreendimentos: {str(e)}")
        return jsonify({'erro': str(e)}), 500


# ==================== API - CONTRATOS ====================

@app.route('/api/contratos', methods=['GET'])
@login_required
def listar_contratos():
    try:
        building_id = request.args.get('building_id', type=int)
        sync = SiengeSupabaseSync()
        
        if building_id:
            contratos = sync.get_contratos_por_empreendimento(building_id)
        else:
            result = sync.supabase.table('sienge_contratos').select('*').execute()
            contratos = result.data if result.data else []
        
        if contratos is None:
            contratos = []
        
        print(f"[API] Contratos encontrados para building_id={building_id}: {len(contratos)}")
        return jsonify(contratos), 200
    except Exception as e:
        print(f"[API] Erro ao listar contratos: {str(e)}")
        return jsonify({'erro': str(e)}), 500


@app.route('/api/contrato-info', methods=['GET'])
@login_required
def get_contrato_info():
    try:
        numero_contrato = request.args.get('numero_contrato')
        building_id = request.args.get('building_id')
        
        if not numero_contrato or not building_id:
            return jsonify({'erro': 'Parâmetros obrigatórios: numero_contrato, building_id'}), 400
        
        # Manter building_id como string (assim está no banco)
        print(f"[API] get_contrato_info: numero_contrato={numero_contrato}, building_id={building_id}")
        
        sync = SiengeSupabaseSync()
        
        # 1. Buscar contrato
        contrato = sync.get_contrato_por_numero(numero_contrato, building_id)
        if not contrato:
            return jsonify({'erro': 'Contrato não encontrado'}), 404
        
        # 2. Buscar corretor do contrato (campo pode estar no proprio contrato)
        corretor_principal = contrato.get('corretor') or contrato.get('broker_nome') or contrato.get('broker_name')
        valor_comissao = None
        status_parcela = None
        comissao_record = None
        
        # 3. Buscar comissao da tabela sienge_comissoes
        try:
            comissao_result = sync.supabase.table('sienge_comissoes')\
                .select('*')\
                .eq('numero_contrato', numero_contrato)\
                .eq('building_id', building_id)\
                .limit(1)\
                .execute()
            
            if comissao_result.data:
                comissao_record = comissao_result.data[0]
                if not corretor_principal:
                    corretor_principal = comissao_record.get('broker_nome') or comissao_record.get('broker_name') or comissao_record.get('corretor')
                valor_comissao = comissao_record.get('commission_value') or comissao_record.get('valor_comissao') or comissao_record.get('value')
                status_parcela = comissao_record.get('installment_status') or comissao_record.get('status') or comissao_record.get('status_parcela')
                print(f"[API] Comissao encontrada: corretor={corretor_principal}, valor={valor_comissao}")
        except Exception as e:
            print(f"[API] Erro ao buscar comissao (ignorando): {str(e)}")
        
        # 4. Se ainda nao tem corretor, tentar buscar pelo brokers do contrato
        if not corretor_principal:
            brokers = contrato.get('brokers') or contrato.get('corretores')
            if brokers and isinstance(brokers, list) and len(brokers) > 0:
                # Pegar o primeiro corretor principal
                for b in brokers:
                    if isinstance(b, dict):
                        if b.get('main') or b.get('principal'):
                            corretor_principal = b.get('name') or b.get('nome')
                            break
                # Se nao achou principal, pegar o primeiro
                if not corretor_principal and isinstance(brokers[0], dict):
                    corretor_principal = brokers[0].get('name') or brokers[0].get('nome')
            elif brokers and isinstance(brokers, str):
                try:
                    import json
                    parsed = json.loads(brokers)
                    if isinstance(parsed, list) and len(parsed) > 0:
                        for b in parsed:
                            if b.get('main') or b.get('principal'):
                                corretor_principal = b.get('name') or b.get('nome')
                                break
                        if not corretor_principal:
                            corretor_principal = parsed[0].get('name') or parsed[0].get('nome')
                except:
                    pass
        
        print(f"[API] Dados finais: corretor={corretor_principal}, comissao={valor_comissao}")
        
        # Traduzir status
        status_parcela_traduzido = traduzir_status(status_parcela) if status_parcela else None
        
        # Calcular gatilho usando função centralizada
        gatilho = obter_gatilho_contrato(sync, numero_contrato, building_id, comissao_record)
        
        # Mapeamento de building_id para nome do empreendimento
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
        empreendimento_nome = EMPREENDIMENTOS.get(building_id, f'Empreendimento {building_id}')
        
        # Montar resposta
        info = {
            'numero_contrato': contrato.get('numero_contrato'),
            'nome_cliente': contrato.get('nome_cliente'),
            'data_contrato': contrato.get('data_contrato'),
            'valor_total': contrato.get('valor_total'),
            'valor_a_vista': contrato.get('valor_a_vista'),
            'corretor_principal': corretor_principal,
            'valor_comissao': valor_comissao,
            'status_parcela': status_parcela_traduzido,
            'valor_itbi': gatilho['valor_itbi'],
            'valor_pago': gatilho['valor_pago'],
            'building_id': building_id,
            'empreendimento_nome': empreendimento_nome,
            'company_id': contrato.get('company_id'),
            'regra_gatilho': gatilho['regra_gatilho'],
            'valor_gatilho': gatilho['valor_gatilho'],
            'atingiu_gatilho': gatilho['atingiu_gatilho']
        }
        
        return jsonify(info), 200
    except Exception as e:
        return jsonify({'erro': str(e)}), 500


@app.route('/api/buscar-por-lote', methods=['GET'])
@login_required
def buscar_por_lote():
    try:
        numero_lote = request.args.get('lote', '')
        if len(numero_lote) < 2:
            return jsonify([]), 200
        
        sync = SiengeSupabaseSync()
        contratos = sync.buscar_contratos_por_lote(numero_lote)
        
        if contratos is None:
            contratos = []
        
        print(f"[API] Busca por lote '{numero_lote}': {len(contratos)} resultados")
        return jsonify(contratos), 200
    except Exception as e:
        print(f"[API] Erro na busca por lote: {str(e)}")
        return jsonify({'erro': str(e)}), 500


# ==================== API - CORRETORES ====================

@app.route('/api/corretores', methods=['GET'])
@login_required
def listar_corretores():
    try:
        sync = SiengeSupabaseSync()
        corretores = sync.get_corretores()
        return jsonify(corretores), 200
    except Exception as e:
        return jsonify({'erro': str(e)}), 500


@app.route('/api/corretores-usuarios', methods=['GET'])
@login_required
def listar_corretores_usuarios():
    try:
        corretores = auth_manager.listar_corretores_usuarios()
        return jsonify({'sucesso': True, 'corretores': corretores}), 200
    except Exception as e:
        return jsonify({'sucesso': False, 'erro': str(e)}), 500


@app.route('/api/corretor/buscar-por-documento', methods=['GET'])
def buscar_corretor_por_documento():
    """Busca corretor pelo CPF ou CNPJ na tabela sienge_corretores"""
    try:
        documento = request.args.get('documento', '').strip()
        
        if not documento:
            return jsonify({'sucesso': False, 'erro': 'Documento não informado'}), 400
        
        # Limpar documento (remover pontos, traços, barras)
        documento_limpo = documento.replace('.', '').replace('-', '').replace('/', '').strip()
        
        if len(documento_limpo) < 11:
            return jsonify({'sucesso': False, 'erro': 'Documento incompleto'}), 400
        
        sync = SiengeSupabaseSync()
        
        print(f"[API] Buscando corretor por documento: {documento_limpo}")
        
        # Buscar todos os corretores - usando apenas colunas que existem
        result = sync.supabase.table('sienge_corretores')\
            .select('*')\
            .execute()
        
        corretor = None
        if result.data:
            for c in result.data:
                # Limpar CPF/CNPJ do banco para comparação
                cpf_banco = (c.get('cpf') or '').replace('.', '').replace('-', '').replace('/', '').strip()
                cnpj_banco = (c.get('cnpj') or '').replace('.', '').replace('-', '').replace('/', '').strip()
                
                if cpf_banco == documento_limpo or cnpj_banco == documento_limpo:
                    corretor = c
                    print(f"[API] Corretor encontrado: {corretor.get('nome')}")
                    break
        
        if corretor:
            return jsonify({
                'sucesso': True,
                'encontrado': True,
                'corretor': {
                    'sienge_id': corretor.get('sienge_id'),
                    'cpf': corretor.get('cpf'),
                    'cnpj': corretor.get('cnpj'),
                    'nome': corretor.get('nome'),
                    'email': corretor.get('email') or '',
                    'telefone': corretor.get('telefone') or ''
                }
            }), 200
        
        print(f"[API] Corretor não encontrado com documento: {documento_limpo}")
        return jsonify({
            'sucesso': True,
            'encontrado': False,
            'mensagem': 'Corretor não encontrado no sistema SIENGE. Verifique se o CPF/CNPJ está correto.'
        }), 200
        
    except Exception as e:
        print(f"[API] Erro ao buscar corretor por documento: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'sucesso': False, 'erro': str(e)}), 500


@app.route('/api/contratos-por-corretor', methods=['GET'])
@login_required
def contratos_por_corretor():
    try:
        corretor_id = request.args.get('corretor_id', type=int)
        corretor_nome = request.args.get('corretor_nome')
        
        sync = SiengeSupabaseSync()
        comissoes = sync.get_comissoes_por_corretor(corretor_id=corretor_id, corretor_nome=corretor_nome)
        
        return jsonify(comissoes), 200
    except Exception as e:
        return jsonify({'erro': str(e)}), 500


# ==================== API - SINCRONIZAÇÃO ====================

@app.route('/api/sincronizar', methods=['POST'])
@login_required
def sincronizar():
    if not current_user.is_admin:
        return jsonify({'erro': 'Apenas administradores podem sincronizar'}), 403
    
    try:
        building_id = None
        if request.is_json and request.data:
            data = request.get_json(silent=True)
            if data:
                building_id = data.get('building_id')
        
        sync = SiengeSupabaseSync()
        resultado = sync.sync_all(building_id=building_id)
        return jsonify({'sucesso': True, 'resultado': resultado}), 200
    except Exception as e:
        import traceback
        print(f"[ERRO SINCRONIZAÇÃO] {str(e)}")
        traceback.print_exc()
        return jsonify({'erro': str(e)}), 500


@app.route('/api/ultima-sincronizacao', methods=['GET'])
@login_required
def ultima_sincronizacao():
    try:
        sync = SiengeSupabaseSync()
        ultima = sync.get_ultima_sincronizacao()
        return jsonify(ultima), 200
    except Exception as e:
        return jsonify({'erro': str(e)}), 500


@app.route('/api/sincronizar-itbi-faltantes', methods=['POST'])
@login_required
def sincronizar_itbi_faltantes():
    """Sincroniza ITBIs apenas para contratos que não possuem ITBI ainda"""
    if not current_user.is_admin:
        return jsonify({'erro': 'Apenas administradores podem executar esta ação'}), 403
    
    try:
        sync = SiengeSupabaseSync()
        resultado = sync.sync_itbi_faltantes()
        
        return jsonify({
            'sucesso': resultado.get('sucesso', False),
            'mensagem': f"Sincronização de ITBI concluída! {resultado.get('total', 0)} novos ITBIs encontrados.",
            'resultado': resultado
        }), 200
        
    except Exception as e:
        import traceback
        print(f"[ERRO ITBI] {str(e)}")
        traceback.print_exc()
        return jsonify({'sucesso': False, 'erro': str(e)}), 500


@app.route('/api/contratos-sem-itbi', methods=['GET'])
@login_required
def listar_contratos_sem_itbi():
    """Lista contratos que não possuem ITBI cadastrado"""
    try:
        sync = SiengeSupabaseSync()
        
        # Buscar todos os contratos
        contratos_result = sync.supabase.table('sienge_contratos')\
            .select('numero_contrato, building_id, nome_cliente, unidade, data_contrato, company_id')\
            .execute()
        
        contratos = contratos_result.data if contratos_result.data else []
        
        # Buscar ITBIs existentes
        itbi_result = sync.supabase.table('sienge_itbi')\
            .select('numero_contrato, building_id')\
            .execute()
        
        # Criar set de contratos que já têm ITBI
        itbi_existentes = set()
        for item in (itbi_result.data or []):
            chave = f"{item.get('numero_contrato')}_{item.get('building_id')}"
            itbi_existentes.add(chave)
        
        # Mapeamento de building_id para nome do empreendimento
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
        
        # Filtrar contratos sem ITBI
        contratos_sem_itbi = []
        for c in contratos:
            chave = f"{c.get('numero_contrato')}_{c.get('building_id')}"
            if chave not in itbi_existentes:
                bid = c.get('building_id')
                contratos_sem_itbi.append({
                    'numero_contrato': c.get('numero_contrato'),
                    'building_id': bid,
                    'empreendimento': EMPREENDIMENTOS.get(bid, f'Empreendimento {bid}'),
                    'nome_cliente': c.get('nome_cliente'),
                    'unidade': c.get('unidade'),
                    'data_contrato': c.get('data_contrato'),
                    'company_id': c.get('company_id')
                })
        
        # Ordenar por empreendimento e número do contrato
        contratos_sem_itbi.sort(key=lambda x: (x.get('empreendimento', ''), str(x.get('numero_contrato', ''))))
        
        return jsonify({
            'sucesso': True,
            'contratos': contratos_sem_itbi,
            'total': len(contratos_sem_itbi),
            'total_com_itbi': len(itbi_existentes),
            'total_contratos': len(contratos)
        }), 200
        
    except Exception as e:
        import traceback
        print(f"[ERRO] Erro ao listar contratos sem ITBI: {str(e)}")
        traceback.print_exc()
        return jsonify({'sucesso': False, 'erro': str(e)}), 500


@app.route('/api/limpar-cancelados', methods=['POST'])
@login_required
def limpar_cancelados():
    """Remove comissões canceladas e duplicatas do banco de dados"""
    if not current_user.is_admin:
        return jsonify({'erro': 'Apenas administradores podem executar esta ação'}), 403
    
    try:
        sync = SiengeSupabaseSync()
        resultado = {
            'canceladas_antes': 0,
            'canceladas_deletadas': 0,
            'duplicatas_antes': 0,
            'duplicatas_deletadas': 0
        }
        
        # 1. Deletar comissões canceladas (pagas devem permanecer com status Aprovada)
        result = sync.supabase.table('sienge_comissoes').select('id, installment_status').execute()
        canceladas = [c for c in (result.data or []) if 'CANCEL' in (c.get('installment_status') or '').upper()]
        
        resultado['canceladas_antes'] = len(canceladas)
        
        for c in canceladas:
            try:
                sync.supabase.table('sienge_comissoes').delete().eq('id', c['id']).execute()
                resultado['canceladas_deletadas'] += 1
            except:
                pass
        
        # Atualizar comissões pagas para status Aprovada
        pagas = [c for c in (result.data or []) 
                 if 'PAID' in (c.get('installment_status') or '').upper() 
                 or 'PAGO' in (c.get('installment_status') or '').upper()]
        
        resultado['pagas_atualizadas'] = 0
        for c in pagas:
            try:
                sync.supabase.table('sienge_comissoes').update({'status_aprovacao': 'Aprovada'}).eq('id', c['id']).execute()
                resultado['pagas_atualizadas'] += 1
            except:
                pass
        
        # 2. Remover duplicatas
        result2 = sync.supabase.table('sienge_comissoes').select('*').execute()
        grupos = {}
        for c in (result2.data or []):
            chave = f"{c.get('numero_contrato')}_{c.get('unit_name')}_{c.get('building_id')}"
            if chave not in grupos:
                grupos[chave] = []
            grupos[chave].append(c)
        
        duplicatas = {k: v for k, v in grupos.items() if len(v) > 1}
        resultado['duplicatas_antes'] = len(duplicatas)
        
        for chave, comissoes in duplicatas.items():
            # Ordenar: não-canceladas primeiro, depois por ID
            comissoes.sort(key=lambda x: ('CANCEL' in (x.get('installment_status') or '').upper(), x.get('id', 0)))
            # Manter a primeira, deletar as outras
            for c in comissoes[1:]:
                try:
                    sync.supabase.table('sienge_comissoes').delete().eq('id', c['id']).execute()
                    resultado['duplicatas_deletadas'] += 1
                except:
                    pass
        
        return jsonify({
            'sucesso': True,
            'mensagem': f"Limpeza concluída! Removidas {resultado['canceladas_deletadas']} canceladas e {resultado['duplicatas_deletadas']} duplicatas.",
            'resultado': resultado
        }), 200
        
    except Exception as e:
        return jsonify({'sucesso': False, 'erro': str(e)}), 500


# ==================== API - USUÁRIOS ====================

@app.route('/api/usuarios', methods=['GET'])
@login_required
def listar_usuarios():
    if not current_user.is_admin:
        return jsonify({'erro': 'Acesso negado'}), 403
    
    try:
        usuarios = auth_manager.listar_usuarios()
        return jsonify(usuarios), 200
    except Exception as e:
        return jsonify({'erro': str(e)}), 500


@app.route('/api/usuarios', methods=['POST'])
@app.route('/api/usuarios/criar', methods=['POST'])
@login_required
def criar_usuario():
    if not current_user.is_admin:
        return jsonify({'erro': 'Acesso negado'}), 403
    
    try:
        data = request.get_json()
        resultado = auth_manager.criar_usuario(
            username=data.get('username'),
            senha=data.get('senha'),
            nome_completo=data.get('nome_completo'),
            is_admin=data.get('is_admin', False),
            perfil=data.get('perfil', 'Gestor')
        )
        
        if resultado['sucesso']:
            return jsonify(resultado), 201
        return jsonify(resultado), 400
    except Exception as e:
        return jsonify({'erro': str(e)}), 500


@app.route('/api/usuarios/<int:user_id>/perfil', methods=['PUT'])
@login_required
def atualizar_perfil_usuario(user_id):
    if not current_user.is_admin:
        return jsonify({'erro': 'Acesso negado'}), 403
    
    try:
        data = request.get_json()
        novo_perfil = data.get('perfil')
        
        sync = SiengeSupabaseSync()
        sync.supabase.table('usuarios')\
            .update({'perfil': novo_perfil})\
            .eq('id', user_id)\
            .execute()
        
        return jsonify({'sucesso': True}), 200
    except Exception as e:
        return jsonify({'erro': str(e)}), 500


@app.route('/api/usuarios/<int:user_id>/senha', methods=['PUT'])
@login_required
def atualizar_senha_usuario(user_id):
    """Redefine a senha de um usuário"""
    if not current_user.is_admin:
        return jsonify({'erro': 'Acesso negado'}), 403
    
    try:
        data = request.get_json()
        nova_senha = data.get('nova_senha')
        
        if not nova_senha or len(nova_senha) < 6:
            return jsonify({'erro': 'Senha deve ter pelo menos 6 caracteres'}), 400
        
        resultado = auth_manager.atualizar_senha(user_id, nova_senha, is_corretor=False)
        
        if resultado['sucesso']:
            return jsonify({'sucesso': True}), 200
        return jsonify({'erro': resultado.get('erro', 'Erro ao atualizar senha')}), 400
    except Exception as e:
        return jsonify({'erro': str(e)}), 500


@app.route('/api/usuarios/<int:user_id>', methods=['DELETE'])
@login_required
def desativar_usuario(user_id):
    """Desativa um usuário"""
    if not current_user.is_admin:
        return jsonify({'erro': 'Acesso negado'}), 403
    
    try:
        resultado = auth_manager.desativar_usuario(user_id, is_corretor=False)
        
        if resultado['sucesso']:
            return jsonify({'sucesso': True}), 200
        return jsonify({'erro': resultado.get('erro', 'Erro ao desativar usuário')}), 400
    except Exception as e:
        return jsonify({'erro': str(e)}), 500


# ==================== API - CORRETORES (EDIÇÃO) ====================

@app.route('/api/corretores/<int:sienge_id>/senha', methods=['PUT'])
@login_required
def atualizar_senha_corretor(sienge_id):
    """Redefine a senha de um corretor"""
    if not current_user.is_admin:
        return jsonify({'erro': 'Acesso negado'}), 403
    
    try:
        data = request.get_json()
        nova_senha = data.get('nova_senha')
        
        if not nova_senha or len(nova_senha) < 6:
            return jsonify({'erro': 'Senha deve ter pelo menos 6 caracteres'}), 400
        
        resultado = auth_manager.atualizar_senha(sienge_id, nova_senha, is_corretor=True)
        
        if resultado['sucesso']:
            return jsonify({'sucesso': True}), 200
        return jsonify({'erro': resultado.get('erro', 'Erro ao atualizar senha')}), 400
    except Exception as e:
        return jsonify({'erro': str(e)}), 500


@app.route('/api/corretores/<int:sienge_id>/email', methods=['PUT'])
@login_required
def atualizar_email_corretor(sienge_id):
    """Atualiza o e-mail de um corretor"""
    if not current_user.is_admin:
        return jsonify({'erro': 'Acesso negado'}), 403
    
    try:
        data = request.get_json()
        novo_email = data.get('email')
        
        sync = SiengeSupabaseSync()
        sync.supabase.table('sienge_corretores')\
            .update({'email': novo_email})\
            .eq('sienge_id', sienge_id)\
            .execute()
        
        return jsonify({'sucesso': True}), 200
    except Exception as e:
        return jsonify({'erro': str(e)}), 500


@app.route('/api/corretores/<int:sienge_id>', methods=['DELETE'])
@login_required
def remover_acesso_corretor(sienge_id):
    """Remove o acesso de um corretor (limpa a senha)"""
    if not current_user.is_admin:
        return jsonify({'erro': 'Acesso negado'}), 403
    
    try:
        resultado = auth_manager.desativar_usuario(sienge_id, is_corretor=True)
        
        if resultado['sucesso']:
            return jsonify({'sucesso': True}), 200
        return jsonify({'erro': resultado.get('erro', 'Erro ao remover acesso')}), 400
    except Exception as e:
        return jsonify({'erro': str(e)}), 500


# ==================== API - REGRAS DE GATILHO ====================

@app.route('/api/regras-gatilho', methods=['GET'])
@login_required
def listar_regras_gatilho():
    try:
        sync = SiengeSupabaseSync()
        result = sync.supabase.table('regras_gatilho')\
            .select('*')\
            .eq('ativo', True)\
            .order('nome')\
            .execute()
        return jsonify(result.data if result.data else []), 200
    except Exception as e:
        return jsonify({'status': 'erro', 'mensagem': str(e)}), 500


@app.route('/api/regras-gatilho', methods=['POST'])
@login_required
def criar_regra_gatilho():
    try:
        data = request.get_json()
        sync = SiengeSupabaseSync()
        
        nova_regra = {
            'nome': data.get('nome'),
            'descricao': data.get('descricao'),
            'tipo_regra': data.get('tipo_regra', 'gatilho'),  # 'gatilho' ou 'faturamento'
            'percentual': data.get('percentual'),
            'inclui_itbi': data.get('inclui_itbi', False),
            'faturamento_minimo': data.get('faturamento_minimo'),  # Valor mínimo para regra de faturamento
            'percentual_auditoria': data.get('percentual_auditoria'),  # Percentual extra se passar na auditoria
            'ativo': True,
            'criado_em': datetime.now().isoformat()
        }
        
        result = sync.supabase.table('regras_gatilho').insert(nova_regra).execute()
        
        if result.data:
            return jsonify({'status': 'sucesso', 'regra': result.data[0]}), 201
        return jsonify({'status': 'erro', 'mensagem': 'Erro ao criar regra'}), 400
    except Exception as e:
        return jsonify({'status': 'erro', 'mensagem': str(e)}), 500


@app.route('/api/regras-gatilho/<int:regra_id>', methods=['PUT'])
@login_required
def atualizar_regra_gatilho(regra_id):
    try:
        data = request.get_json()
        sync = SiengeSupabaseSync()
        
        atualizacao = {
            'nome': data.get('nome'),
            'descricao': data.get('descricao'),
            'tipo_regra': data.get('tipo_regra', 'gatilho'),
            'percentual': data.get('percentual'),
            'inclui_itbi': data.get('inclui_itbi'),
            'faturamento_minimo': data.get('faturamento_minimo'),
            'percentual_auditoria': data.get('percentual_auditoria'),
            'atualizado_em': datetime.now().isoformat()
        }
        
        result = sync.supabase.table('regras_gatilho')\
            .update(atualizacao)\
            .eq('id', regra_id)\
            .execute()
        
        if result.data:
            return jsonify({'status': 'sucesso', 'regra': result.data[0]}), 200
        return jsonify({'status': 'erro', 'mensagem': 'Regra não encontrada'}), 404
    except Exception as e:
        return jsonify({'status': 'erro', 'mensagem': str(e)}), 500


@app.route('/api/regras-gatilho/<int:regra_id>', methods=['DELETE'])
@login_required
def excluir_regra_gatilho(regra_id):
    try:
        sync = SiengeSupabaseSync()
        sync.supabase.table('regras_gatilho')\
            .update({'ativo': False})\
            .eq('id', regra_id)\
            .execute()
        return jsonify({'status': 'sucesso', 'mensagem': 'Regra excluída'}), 200
    except Exception as e:
        return jsonify({'status': 'erro', 'mensagem': str(e)}), 500


# ==================== API - ATUALIZAR REGRA DE COMISSÃO ====================

@app.route('/api/comissoes/<int:comissao_id>/regra', methods=['PUT'])
@login_required
def atualizar_regra_comissao(comissao_id):
    """Atualiza a regra de gatilho de uma comissão específica e recalcula os valores"""
    try:
        data = request.get_json()
        regra_gatilho_id = data.get('regra_gatilho_id')
        
        sync = SiengeSupabaseSync()
        
        # Buscar a comissão atual
        comissao_result = sync.supabase.table('sienge_comissoes')\
            .select('*')\
            .eq('id', comissao_id)\
            .limit(1)\
            .execute()
        
        if not comissao_result.data:
            return jsonify({'sucesso': False, 'erro': 'Comissão não encontrada'}), 404
        
        comissao = comissao_result.data[0]
        
        # Atualizar o regra_gatilho_id no banco
        update_data = {
            'regra_gatilho_id': regra_gatilho_id if regra_gatilho_id else None,
            'atualizado_em': datetime.now().isoformat()
        }
        
        # Se selecionou uma regra, buscar e atualizar também o campo texto para compatibilidade
        if regra_gatilho_id:
            regra_result = sync.supabase.table('regras_gatilho')\
                .select('percentual, inclui_itbi, nome')\
                .eq('id', regra_gatilho_id)\
                .limit(1)\
                .execute()
            
            if regra_result.data:
                regra = regra_result.data[0]
                percentual = regra.get('percentual')
                inclui_itbi = regra.get('inclui_itbi')
                if percentual is not None:
                    if inclui_itbi:
                        update_data['regra_gatilho'] = f"{percentual}% + ITBI"
                    else:
                        update_data['regra_gatilho'] = f"{percentual}%"
        else:
            update_data['regra_gatilho'] = '10% + ITBI'
        
        sync.supabase.table('sienge_comissoes')\
            .update(update_data)\
            .eq('id', comissao_id)\
            .execute()
        
        # Recalcular o gatilho com a nova regra
        comissao['regra_gatilho_id'] = regra_gatilho_id
        comissao['regra_gatilho'] = update_data.get('regra_gatilho', '10% + ITBI')
        
        gatilho = obter_gatilho_contrato(
            sync, 
            comissao.get('numero_contrato'), 
            comissao.get('building_id'), 
            comissao
        )
        
        return jsonify({
            'sucesso': True,
            'valor_gatilho': gatilho['valor_gatilho'],
            'atingiu_gatilho': gatilho['atingiu_gatilho'],
            'regra_gatilho': gatilho['regra_gatilho'],
            'valor_pago': gatilho['valor_pago']
        }), 200
        
    except Exception as e:
        print(f"[API] Erro ao atualizar regra da comissão {comissao_id}: {str(e)}")
        return jsonify({'sucesso': False, 'erro': str(e)}), 500


# ==================== API - RELATÓRIO DE COMISSÕES ====================

@app.route('/api/relatorio-comissoes', methods=['GET'])
@login_required
def relatorio_comissoes():
    """Relatório completo de comissões com regras aplicadas - Para Gestor e Direção"""
    # Verificar se o usuário tem perfil Gestor, Direção ou é admin
    perfil = getattr(current_user, 'perfil', None)
    is_gestor_ou_direcao = perfil in ['Gestor', 'Direção']
    is_admin = hasattr(current_user, 'is_admin') and current_user.is_admin
    
    if not is_gestor_ou_direcao and not is_admin:
        return jsonify({'erro': 'Apenas gestores e direção podem acessar o relatório'}), 403
    
    try:
        sync = SiengeSupabaseSync()
        
        # Parâmetros de filtro (agora suportam múltiplos valores separados por vírgula)
        empreendimento_param = request.args.get('empreendimento_id', '')
        corretor_param = request.args.get('corretor_id', '')
        regra_param = request.args.get('regra_id', '')
        auditoria_param = request.args.get('auditoria', '')
        data_inicio = request.args.get('data_inicio', '')
        data_fim = request.args.get('data_fim', '')
        
        # Converter para listas (split por vírgula)
        empreendimento_list = [s.strip() for s in empreendimento_param.split(',') if s.strip()]
        corretor_list = [s.strip() for s in corretor_param.split(',') if s.strip()]
        regra_list = [s.strip() for s in regra_param.split(',') if s.strip()]
        auditoria_list = [s.strip() for s in auditoria_param.split(',') if s.strip()]
        
        print(f"[API Relatório] Filtros - empreendimentos: {empreendimento_list}, corretores: {corretor_list}, regras: {regra_list}, auditorias: {auditoria_list}, data: {data_inicio} a {data_fim}")
        
        # Buscar todas as comissões
        query = sync.supabase.table('sienge_comissoes').select('*')
        
        # Filtrar apenas cancelados (pagas devem aparecer)
        result = query.execute()
        comissoes = [c for c in (result.data or []) 
                     if 'cancel' not in (c.get('installment_status') or '').lower()]
        
        # Aplicar filtros (multi-select)
        if empreendimento_list:
            comissoes = [c for c in comissoes if str(c.get('building_id')) in empreendimento_list]
        
        if corretor_list:
            comissoes = [c for c in comissoes if str(c.get('broker_id')) in corretor_list]
        
        if auditoria_list:
            def match_auditoria(comissao):
                auditoria_valor = comissao.get('auditoria_aprovada')
                for a in auditoria_list:
                    if a == 'sim' and auditoria_valor == True:
                        return True
                    elif a == 'nao' and auditoria_valor == False:
                        return True
                    elif a == 'pendente' and auditoria_valor is None:
                        return True
                return False
            comissoes = [c for c in comissoes if match_auditoria(c)]
        
        # Filtrar por regra (multi-select)
        if regra_list:
            comissoes = [c for c in comissoes if str(c.get('regra_gatilho_id')) in regra_list]
        
        # Buscar regras de gatilho para associar
        regras_result = sync.supabase.table('regras_gatilho').select('*').execute()
        regras_dict = {r['id']: r for r in (regras_result.data or [])}
        
        # Buscar contratos para pegar dados do cliente, lote e data_contrato
        contratos_result = sync.supabase.table('sienge_contratos').select('*').execute()
        contratos_dict = {c['numero_contrato']: c for c in (contratos_result.data or [])}
        
        # Filtrar por período de data do contrato
        if data_inicio or data_fim:
            def filtrar_por_data_relatorio(comissao):
                numero_contrato = comissao.get('numero_contrato')
                contrato = contratos_dict.get(numero_contrato, {})
                data_contrato = contrato.get('data_contrato')
                if not data_contrato:
                    return False
                
                try:
                    if 'T' in str(data_contrato):
                        data_str = str(data_contrato).split('T')[0]
                    else:
                        data_str = str(data_contrato)[:10]
                    
                    if data_inicio and data_str < data_inicio:
                        return False
                    if data_fim and data_str > data_fim:
                        return False
                    return True
                except:
                    return False
            
            comissoes = [c for c in comissoes if filtrar_por_data_relatorio(c)]
            print(f"[API Relatório] Após filtro de data: {len(comissoes)} comissões")
        
        # Buscar empreendimentos (usando o método do sync)
        empreendimentos_lista = sync.get_empreendimentos()
        empreendimentos_dict = {str(e['id']): e for e in empreendimentos_lista}
        
        # Montar relatório
        relatorio = []
        corretores_unicos = set()
        total_comissoes = 0
        auditorias_aprovadas = 0
        
        for comissao in comissoes:
            numero_contrato = comissao.get('numero_contrato')
            contrato = contratos_dict.get(numero_contrato, {})
            
            # Dados do empreendimento
            building_id = comissao.get('building_id') or contrato.get('building_id')
            empreendimento = empreendimentos_dict.get(building_id, {})
            
            # Regra aplicada
            regra_id_aplicada = comissao.get('regra_gatilho_id')
            regra = regras_dict.get(regra_id_aplicada, {})
            
            # Formatar regra para exibição
            regra_nome = regra.get('nome', 'Não definida')
            tipo_regra = regra.get('tipo_regra', 'gatilho')
            
            if tipo_regra == 'faturamento':
                regra_descricao = f"Fat. Mín. R$ {regra.get('faturamento_minimo', 0):,.0f} → {regra.get('percentual', 0)}%"
                if regra.get('percentual_auditoria'):
                    regra_descricao += f" (+{regra.get('percentual_auditoria')}% auditoria)"
            else:
                regra_descricao = f"{regra.get('percentual', 0)}%"
                if regra.get('inclui_itbi'):
                    regra_descricao += " + ITBI"
            
            # Valor da comissão
            valor_comissao = float(comissao.get('valor_comissao') or comissao.get('commission_value') or 0)
            total_comissoes += valor_comissao
            
            # Auditoria
            auditoria_status = comissao.get('auditoria_aprovada')
            if auditoria_status == True:
                auditorias_aprovadas += 1
            
            # Corretor
            corretor_nome = comissao.get('broker_nome') or comissao.get('broker_name') or 'Não informado'
            corretores_unicos.add(corretor_nome)
            
            relatorio.append({
                'numero_contrato': numero_contrato,
                'lote': contrato.get('numero_lote') or comissao.get('unit_name') or f"Contrato {numero_contrato}",
                'cliente': contrato.get('nome_cliente') or comissao.get('customer_name') or 'Não informado',
                'empreendimento': empreendimento.get('nome') or comissao.get('building_name') or 'Não informado',
                'empreendimento_id': building_id,
                'corretor': corretor_nome,
                'corretor_id': comissao.get('broker_id'),
                'regra_id': regra_id_aplicada,
                'regra_nome': regra_nome,
                'regra_descricao': regra_descricao,
                'tipo_regra': tipo_regra,
                'auditoria_aprovada': auditoria_status,
                'valor_comissao': valor_comissao,
                'status_aprovacao': comissao.get('status_aprovacao', 'Pendente'),
                'data_contrato': contrato.get('data_contrato')
            })
        
        # Ordenar por empreendimento e lote
        relatorio.sort(key=lambda x: (x.get('empreendimento', ''), x.get('lote', '')))
        
        return jsonify({
            'sucesso': True,
            'dados': relatorio,
            'resumo': {
                'total_vendas': len(relatorio),
                'total_comissoes': total_comissoes,
                'total_corretores': len(corretores_unicos),
                'auditorias_aprovadas': auditorias_aprovadas
            }
        }), 200
        
    except Exception as e:
        import traceback
        print(f"[ERRO RELATÓRIO] {str(e)}")
        traceback.print_exc()
        return jsonify({'sucesso': False, 'erro': str(e)}), 500


@app.route('/api/relatorio-comissoes/corretores', methods=['GET'])
@login_required
def listar_corretores_relatorio():
    """Lista corretores únicos para o filtro do relatório - Para Gestor e Direção"""
    # Verificar se o usuário tem perfil Gestor, Direção ou é admin
    perfil = getattr(current_user, 'perfil', None)
    is_gestor_ou_direcao = perfil in ['Gestor', 'Direção']
    is_admin = hasattr(current_user, 'is_admin') and current_user.is_admin
    
    if not is_gestor_ou_direcao and not is_admin:
        return jsonify({'erro': 'Acesso negado'}), 403
    
    try:
        sync = SiengeSupabaseSync()
        result = sync.supabase.table('sienge_comissoes').select('broker_id, broker_nome').execute()
        
        corretores = {}
        for c in (result.data or []):
            broker_id = c.get('broker_id')
            broker_nome = c.get('broker_nome')
            if broker_id and broker_nome and broker_id not in corretores:
                corretores[broker_id] = broker_nome
        
        lista = [{'id': k, 'nome': v} for k, v in corretores.items()]
        lista.sort(key=lambda x: x['nome'])
        
        return jsonify(lista), 200
    except Exception as e:
        return jsonify([]), 200


# ==================== API - COMISSÕES E APROVAÇÃO ====================

@app.route('/api/comissoes/status-parcela', methods=['GET'])
@login_required
def listar_status_parcela():
    """Lista todos os status de parcela únicos no banco"""
    try:
        sync = SiengeSupabaseSync()
        result = sync.supabase.table('sienge_comissoes').select('installment_status').execute()
        
        status_unicos = set()
        for c in (result.data or []):
            st = c.get('installment_status')
            if st:
                status_unicos.add(st)
        
        return jsonify({
            'sucesso': True,
            'status': sorted(list(status_unicos))
        }), 200
    except Exception as e:
        return jsonify({'sucesso': False, 'erro': str(e)}), 500


@app.route('/api/comissoes/listar', methods=['GET'])
@login_required
def listar_todas_comissoes():
    try:
        sync = SiengeSupabaseSync()
        
        status_parcela_param = request.args.get('status_parcela', '')
        status_aprovacao_param = request.args.get('status_aprovacao', '')
        gatilho_atingido_param = request.args.get('gatilho_atingido', '')
        data_inicio = request.args.get('data_inicio', '')
        data_fim = request.args.get('data_fim', '')
        
        status_parcela_list = [s.strip() for s in status_parcela_param.split(',') if s.strip()]
        status_aprovacao_list = [s.strip() for s in status_aprovacao_param.split(',') if s.strip()]
        gatilho_list = [s.strip() for s in gatilho_atingido_param.split(',') if s.strip()]
        
        print(f"[API] Filtros recebidos - status_parcela: {status_parcela_list}, status_aprovacao: {status_aprovacao_list}, gatilho: {gatilho_list}")
        
        # Buscar comissões
        result = sync.supabase.table('sienge_comissoes').select('*').execute()
        comissoes = result.data if result.data else []
        
        comissoes = [c for c in comissoes 
                     if 'CANCEL' not in (c.get('installment_status') or '').upper()]
        
        # Mapeamento de status PT-BR -> EN
        mapa_status_parcela = {
            'pago': ['paidout', 'paid out', 'paid', 'pago'],
            'pendente': ['pending', 'pendente'],
            'vencido': ['overdue', 'vencido'],
            'aberto': ['open', 'aberto'],
            'parcial': ['partial', 'parcial'],
            'cancelado': ['cancelled', 'canceled', 'cancelado'],
            'aguardando autorização': ['awaiting authorization', 'awaiting_authorization', 'aguardando autorização'],
            'liberado': ['released', 'liberado']
        }
        
        if status_parcela_list:
            def match_status_parcela(comissao):
                status_comissao = (comissao.get('installment_status') or '').lower()
                for status in status_parcela_list:
                    status_lower = status.lower()
                    valores_busca = mapa_status_parcela.get(status_lower, [status_lower])
                    if any(v in status_comissao for v in valores_busca):
                        return True
                return False
            comissoes = [c for c in comissoes if match_status_parcela(c)]
        
        if status_aprovacao_list:
            comissoes = [c for c in comissoes if c.get('status_aprovacao') in status_aprovacao_list]
        
        comissoes.sort(key=lambda x: x.get('commission_date') or '', reverse=True)
        
        # ===== BATCH LOADING: carregar todos os dados auxiliares de uma vez =====
        # Em vez de N queries por comissão, fazemos apenas 4 queries no total
        print(f"[API] Batch-loading dados para {len(comissoes)} comissões...")
        
        # 1. Carregar todos os contratos
        contratos_result = sync.supabase.table('sienge_contratos').select('numero_contrato,building_id,valor_a_vista,valor_total,data_contrato').execute()
        contratos_map = {}
        for ct in (contratos_result.data or []):
            key = (str(ct.get('numero_contrato', '')), str(ct.get('building_id', '')))
            contratos_map[key] = ct
        
        # 2. Carregar todos os ITBIs
        itbi_result = sync.supabase.table('sienge_itbi').select('numero_contrato,building_id,valor_itbi').execute()
        itbi_map = {}
        for it in (itbi_result.data or []):
            key = (str(it.get('numero_contrato', '')), str(it.get('building_id', '')))
            itbi_map[key] = float(it.get('valor_itbi') or 0)
        
        # 3. Carregar todos os valores pagos
        pago_result = sync.supabase.table('sienge_valor_pago').select('numero_contrato,building_id,valor_pago').execute()
        pago_map = {}
        for pg in (pago_result.data or []):
            key = (str(pg.get('numero_contrato', '')), str(pg.get('building_id', '')))
            pago_map[key] = float(pg.get('valor_pago') or 0)
        
        # 4. Carregar todas as regras de gatilho
        regras_result = sync.supabase.table('regras_gatilho').select('id,percentual,inclui_itbi,nome').execute()
        regras_map = {}
        for rg in (regras_result.data or []):
            regras_map[rg['id']] = rg
        
        print(f"[API] Batch-load concluído: {len(contratos_map)} contratos, {len(itbi_map)} ITBIs, {len(pago_map)} pagos, {len(regras_map)} regras")
        
        # ===== Calcular gatilho para cada comissão usando dados pré-carregados =====
        for c in comissoes:
            numero_contrato = str(c.get('numero_contrato') or '')
            building_id = str(c.get('building_id') or '')
            key = (numero_contrato, building_id)
            
            contrato = contratos_map.get(key)
            valor_a_vista = float((contrato.get('valor_a_vista') or contrato.get('valor_total') or 0)) if contrato else 0
            valor_itbi = itbi_map.get(key, 0)
            valor_pago = pago_map.get(key, 0)
            c['data_contrato'] = contrato.get('data_contrato') if contrato else None
            
            # Determinar regra do gatilho
            regra_gatilho_texto = '10% + ITBI'
            percentual = None
            inclui_itbi = None
            
            regra_id = c.get('regra_gatilho_id')
            if regra_id and regra_id in regras_map:
                regra_data = regras_map[regra_id]
                percentual = regra_data.get('percentual')
                inclui_itbi = regra_data.get('inclui_itbi')
                if percentual is not None:
                    regra_gatilho_texto = f"{percentual}% + ITBI" if inclui_itbi else f"{percentual}%"
            
            if percentual is None:
                regra_texto = c.get('regra_gatilho')
                if regra_texto:
                    regra_gatilho_texto = regra_texto
            
            # Calcular valor do gatilho
            if percentual is not None:
                perc = float(percentual) / 100.0
                valor_gatilho = (valor_a_vista * perc) + valor_itbi if inclui_itbi else valor_a_vista * perc
            else:
                valor_gatilho = calcular_valor_gatilho(valor_a_vista, valor_itbi, regra_gatilho_texto)
            
            atingiu_gatilho = float(valor_pago) >= valor_gatilho if valor_gatilho > 0 else False
            
            c['valor_pago'] = valor_pago
            c['valor_itbi'] = valor_itbi
            c['valor_gatilho'] = valor_gatilho
            c['atingiu_gatilho'] = atingiu_gatilho
            c['valor_a_vista'] = valor_a_vista
            c['regra_gatilho'] = regra_gatilho_texto
        
        # Filtro de período de data do contrato
        if data_inicio or data_fim:
            def filtrar_por_data(comissao):
                data_contrato = comissao.get('data_contrato')
                if not data_contrato:
                    return False
                try:
                    if 'T' in str(data_contrato):
                        data_str = str(data_contrato).split('T')[0]
                    else:
                        data_str = str(data_contrato)[:10]
                    
                    if data_inicio and data_str < data_inicio:
                        return False
                    if data_fim and data_str > data_fim:
                        return False
                    return True
                except:
                    return False
            
            comissoes = [c for c in comissoes if filtrar_por_data(c)]
            print(f"[API] Após filtro de data: {len(comissoes)} comissões")
        
        if gatilho_list:
            gatilho_bools = [g.lower() == 'true' for g in gatilho_list]
            comissoes = [c for c in comissoes if c.get('atingiu_gatilho') in gatilho_bools]
            print(f"[API] Após filtro de gatilho: {len(comissoes)} comissões")
        
        return jsonify({
            'sucesso': True,
            'comissoes': comissoes,
            'total': len(comissoes)
        }), 200
        
    except Exception as e:
        return jsonify({'sucesso': False, 'erro': str(e)}), 500


@app.route('/api/comissoes/enviar-aprovacao', methods=['POST'])
@login_required
def enviar_comissoes_aprovacao():
    try:
        if not current_user.is_admin:
            return jsonify({'erro': 'Apenas gestores podem enviar para aprovação'}), 403
        
        data = request.get_json()
        comissoes_ids = data.get('comissoes_ids', [])
        observacoes = data.get('observacoes')
        
        if not comissoes_ids:
            return jsonify({'erro': 'Nenhuma comissão selecionada'}), 400
        
        sync = SiengeSupabaseSync()
        aprovacao = AprovacaoComissoes(sync.supabase)
        
        resultado = aprovacao.enviar_para_aprovacao(comissoes_ids, current_user.id, observacoes)
        
        if resultado['sucesso']:
            return jsonify(resultado), 200
        return jsonify(resultado), 400
        
    except Exception as e:
        return jsonify({'sucesso': False, 'erro': str(e)}), 500


@app.route('/api/comissoes/aprovar', methods=['POST'])
@login_required
def aprovar_comissoes():
    try:
        if not hasattr(current_user, 'perfil') or current_user.perfil != 'Direção':
            return jsonify({'erro': 'Apenas a direção pode aprovar comissões'}), 403
        
        data = request.get_json()
        comissoes_ids = data.get('comissoes_ids', [])
        observacoes = data.get('observacoes')
        
        if not comissoes_ids:
            return jsonify({'erro': 'Nenhuma comissão selecionada'}), 400
        
        sync = SiengeSupabaseSync()
        aprovacao = AprovacaoComissoes(sync.supabase)
        
        resultado = aprovacao.aprovar_comissoes(comissoes_ids, current_user.id, observacoes)
        
        if resultado['sucesso']:
            return jsonify(resultado), 200
        return jsonify(resultado), 400
        
    except Exception as e:
        return jsonify({'sucesso': False, 'erro': str(e)}), 500


@app.route('/api/comissoes/rejeitar', methods=['POST'])
@login_required
def rejeitar_comissoes():
    try:
        if not hasattr(current_user, 'perfil') or current_user.perfil != 'Direção':
            return jsonify({'erro': 'Apenas a direção pode rejeitar comissões'}), 403
        
        data = request.get_json()
        comissoes_ids = data.get('comissoes_ids', [])
        motivo = data.get('motivo', '')
        observacoes = data.get('observacoes')
        
        if not comissoes_ids:
            return jsonify({'erro': 'Nenhuma comissão selecionada'}), 400
        
        if not motivo:
            return jsonify({'erro': 'Motivo é obrigatório para rejeição'}), 400
        
        sync = SiengeSupabaseSync()
        aprovacao = AprovacaoComissoes(sync.supabase)
        
        resultado = aprovacao.rejeitar_comissoes(comissoes_ids, current_user.id, motivo, observacoes)
        
        if resultado['sucesso']:
            return jsonify(resultado), 200
        return jsonify(resultado), 400
        
    except Exception as e:
        return jsonify({'sucesso': False, 'erro': str(e)}), 500


@app.route('/api/comissoes/pendentes-aprovacao', methods=['GET'])
@login_required
def listar_comissoes_pendentes_aprovacao():
    try:
        sync = SiengeSupabaseSync()
        aprovacao = AprovacaoComissoes(sync.supabase)
        
        comissoes = aprovacao.listar_comissoes_por_status('Pendente de Aprovação')
        
        # Calcular gatilho usando a função centralizada (mesma da consulta por contrato)
        for c in comissoes:
            gatilho = obter_gatilho_contrato(sync, c.get('numero_contrato'), c.get('building_id'), c)
            c['valor_gatilho'] = gatilho['valor_gatilho']
            c['atingiu_gatilho'] = gatilho['atingiu_gatilho']
            c['valor_pago'] = gatilho['valor_pago']
        
        return jsonify({
            'sucesso': True,
            'comissoes': comissoes,
            'total': len(comissoes)
        }), 200
        
    except Exception as e:
        return jsonify({'sucesso': False, 'erro': str(e)}), 500


# ==================== API - REVERTER COMISSÕES ====================

@app.route('/api/comissoes/reverter-status', methods=['GET', 'POST'])
@login_required
def reverter_status_comissoes():
    """Reverte todas as comissões com status diferente de 'Pendente' para 'Pendente'"""
    if not current_user.is_admin:
        return jsonify({'erro': 'Apenas administradores podem executar esta ação'}), 403
    
    try:
        sync = SiengeSupabaseSync()
        
        # Buscar comissões que não estão pendentes
        result = sync.supabase.table('sienge_comissoes')\
            .select('id, status_aprovacao, broker_nome')\
            .neq('status_aprovacao', 'Pendente')\
            .execute()
        
        comissoes_para_reverter = result.data if result.data else []
        total = len(comissoes_para_reverter)
        revertidas = 0
        
        print(f"[REVERTER] Encontradas {total} comissões para reverter")
        
        for c in comissoes_para_reverter:
            try:
                sync.supabase.table('sienge_comissoes')\
                    .update({
                        'status_aprovacao': 'Pendente',
                        'data_envio_aprovacao': None,
                        'enviado_por': None,
                        'data_aprovacao': None,
                        'aprovado_por': None,
                        'observacoes': None
                    })\
                    .eq('id', c['id'])\
                    .execute()
                revertidas += 1
                print(f"[REVERTER] Comissão {c['id']} ({c.get('broker_nome', 'N/A')}) revertida de '{c.get('status_aprovacao')}' para 'Pendente'")
            except Exception as e:
                print(f"[REVERTER] Erro ao reverter comissão {c['id']}: {str(e)}")
        
        return jsonify({
            'sucesso': True,
            'mensagem': f'{revertidas} comissões revertidas para status Pendente',
            'total_encontradas': total,
            'revertidas': revertidas
        }), 200
        
    except Exception as e:
        print(f"[REVERTER] Erro: {str(e)}")
        return jsonify({'sucesso': False, 'erro': str(e)}), 500


# ==================== API - CONFIGURAÇÕES DE E-MAILS ====================

@app.route('/api/configuracoes-emails', methods=['GET'])
@login_required
def listar_configuracoes_emails():
    try:
        sync = SiengeSupabaseSync()
        result = sync.supabase.table('configuracoes_emails')\
            .select('*')\
            .order('tipo')\
            .execute()
        
        return jsonify({
            'sucesso': True,
            'configuracoes': result.data if result.data else []
        }), 200
    except Exception as e:
        return jsonify({'sucesso': False, 'erro': str(e)}), 500


@app.route('/api/configuracoes-emails/<string:tipo>', methods=['PUT'])
@login_required
def atualizar_configuracoes_emails(tipo):
    if not current_user.is_admin:
        return jsonify({'erro': 'Acesso negado'}), 403
    
    try:
        data = request.get_json()
        emails = data.get('emails', [])
        
        sync = SiengeSupabaseSync()
        sync.supabase.table('configuracoes_emails')\
            .update({
                'emails': emails,
                'atualizado_por': current_user.id,
                'atualizado_em': datetime.now().isoformat()
            })\
            .eq('tipo', tipo)\
            .execute()
        
        return jsonify({'sucesso': True}), 200
    except Exception as e:
        return jsonify({'sucesso': False, 'erro': str(e)}), 500


# ==================== ROTAS DE CADASTRO ====================

@app.route('/cadastro/corretor', methods=['GET', 'POST'])
def cadastro_corretor():
    if request.method == 'POST':
        data = request.form
        
        # Obter sienge_id do formulário
        sienge_id = data.get('sienge_id')
        if sienge_id:
            try:
                sienge_id = int(sienge_id)
            except:
                sienge_id = None
        
        resultado = auth_manager.criar_corretor(
            cpf=data.get('cpf'),
            senha=data.get('senha'),
            nome=data.get('nome'),
            email=data.get('email'),
            sienge_id=sienge_id
        )
        
        if resultado['sucesso']:
            flash('Cadastro realizado com sucesso! Faça login.', 'success')
            return redirect(url_for('login'))
        else:
            flash(resultado.get('erro', 'Erro no cadastro'), 'error')
    
    return render_template('cadastro_corretor.html')


# ==================== SINCRONIZAÇÃO AUTOMÁTICA ====================

def sincronizacao_diaria():
    """Executa sincronização diária automática"""
    try:
        print(f"[{datetime.now()}] Iniciando sincronização automática...")
        sync = SiengeSupabaseSync()
        resultado = sync.sync_all()
        print(f"[{datetime.now()}] Sincronização concluída: {resultado}")
    except Exception as e:
        print(f"[{datetime.now()}] Erro na sincronização: {str(e)}")


# NOTA: Scheduler foi movido para scheduler.py para evitar duplicação em multi-worker
# Para ativar sincronização diária, execute: python scheduler.py em processo separado
# Ou configure um cron job no servidor para chamar: curl http://localhost:5000/api/sincronizar


# ==================== INICIALIZAÇÃO ====================

if __name__ == '__main__':
    import sys
    import traceback
    try:
        # Configurações do servidor
        port = int(os.getenv('FLASK_PORT', 5000))
        debug = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'  # Padrão False
        
        if debug:
            logger.warning("⚠️  ATENÇÃO: Modo DEBUG está ATIVO! Não use em produção!")
        else:
            logger.info("✅ Modo produção ativo (debug=False)")
        
        logger.info(f"Sistema de Comissões Young iniciando na porta {port}...")
        logger.info(f"Para sincronização automática, execute: python scheduler.py")
        
        app.run(debug=debug, port=port, host='0.0.0.0')
    except Exception as e:
        logger.error(f"ERRO ao iniciar o servidor: {str(e)}")
        traceback.print_exc(file=sys.stderr)
        sys.exit(1)
