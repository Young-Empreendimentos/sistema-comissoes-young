/**
 * JavaScript para Dashboard da Direção
 * Sistema de Comissões Young Empreendimentos
 */

// Estado global
let comissoesSelecionadasDirecao = [];
let observacoesComissoes = {}; // Armazena observações por ID de comissão
let comissaoAtualObservacao = null; // ID da comissão sendo editada

// ==================== FUNÇÕES UTILITÁRIAS ====================

function formatCurrency(value) {
    if (value === null || value === undefined || value === '' || value === '-') {
        return 'R$ 0,00';
    }
    return new Intl.NumberFormat('pt-BR', {
        style: 'currency',
        currency: 'BRL'
    }).format(value);
}

function formatDate(dateStr) {
    if (!dateStr) return '-';
    try {
        const date = new Date(dateStr);
        return date.toLocaleDateString('pt-BR');
    } catch (e) {
        return dateStr;
    }
}

function showAlert(message, type = 'info') {
    const alertsContainer = document.getElementById('alerts');
    if (!alertsContainer) return;
    
    const alert = document.createElement('div');
    alert.className = `alert alert-${type}`;
    alert.textContent = message;
    alertsContainer.appendChild(alert);
    
    setTimeout(() => {
        alert.style.animation = 'slideOut 0.3s ease';
        setTimeout(() => alert.remove(), 300);
    }, 4000);
}

function corrigirEspacamentoNome(nome) {
    if (!nome) return '-';
    // Adiciona espaço antes de letras maiúsculas que seguem letras minúsculas
    return nome.replace(/([a-z])([A-Z])/g, '$1 $2');
}

function getInitials(nome) {
    if (!nome) return '?';
    const parts = corrigirEspacamentoNome(nome).split(' ');
    if (parts.length >= 2) {
        return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase();
    }
    return parts[0].substring(0, 2).toUpperCase();
}

// ==================== CARREGAR COMISSÕES ====================

async function carregarComissoesPendentes() {
    const loading = document.getElementById('loadingDirecao');
    const tabelaContainer = document.getElementById('tabelaContainer');
    const emptyState = document.getElementById('emptyState');
    
    try {
        loading.style.display = 'block';
        tabelaContainer.style.display = 'none';
        emptyState.style.display = 'none';
        
        const response = await fetch('/api/comissoes/pendentes-aprovacao');
        const data = await response.json();
        
        loading.style.display = 'none';
        
        if (!data.sucesso || !data.comissoes || data.comissoes.length === 0) {
            emptyState.style.display = 'block';
            atualizarEstatisticas([]);
            return;
        }
        
        tabelaContainer.style.display = 'block';
        renderizarTabelaComissoesDirecao(data.comissoes);
        atualizarEstatisticas(data.comissoes);
        
    } catch (error) {
        console.error('Erro ao carregar comissões:', error);
        loading.style.display = 'none';
        showAlert('Erro ao carregar comissões pendentes', 'error');
    }
}

function atualizarEstatisticas(comissoes) {
    const total = comissoes.length;
    const valorTotal = comissoes.reduce((sum, c) => sum + parseFloat(c.valor_comissao || c.commission_value || 0), 0);
    
    // Animar contagem
    animateValue('totalPendente', total);
    document.getElementById('valorTotal').textContent = formatCurrency(valorTotal);
}

function animateValue(elementId, endValue) {
    const element = document.getElementById(elementId);
    const duration = 500;
    const startTime = performance.now();
    const startValue = parseInt(element.textContent) || 0;
    
    function update(currentTime) {
        const elapsed = currentTime - startTime;
        const progress = Math.min(elapsed / duration, 1);
        const easeProgress = 1 - Math.pow(1 - progress, 3);
        const currentValue = Math.round(startValue + (endValue - startValue) * easeProgress);
        element.textContent = currentValue;
        
        if (progress < 1) {
            requestAnimationFrame(update);
        }
    }
    
    requestAnimationFrame(update);
}

// ==================== RENDERIZAR TABELA ====================

function renderizarTabelaComissoesDirecao(comissoes) {
    const tbody = document.getElementById('corpoTabelaDirecao');
    
    tbody.innerHTML = comissoes.map((comissao, index) => {
        const atingiuGatilho = comissao.atingiu_gatilho;
        const gatilhoClass = atingiuGatilho ? 'sim' : 'nao';
        const gatilhoText = atingiuGatilho ? 'SIM' : 'NÃO';
        const nomeCorretor = corrigirEspacamentoNome(comissao.broker_nome);
        const initials = getInitials(comissao.broker_nome);
        
        return `
            <tr style="animation: fadeInRow 0.3s ease ${index * 0.05}s both;">
                <td>
                    <input type="checkbox" 
                           class="checkbox-direcao checkbox-comissao-direcao" 
                           data-id="${comissao.id}"
                           data-valor="${comissao.valor_comissao || comissao.commission_value || 0}"
                           onchange="toggleComissaoSelecionadaDirecao(this)">
                </td>
                <td>
                    <div class="corretor-cell">
                        <div class="corretor-avatar">${initials}</div>
                        <div class="corretor-info">
                            <span class="corretor-nome">${nomeCorretor}</span>
                        </div>
                    </div>
                </td>
                <td>${comissao.enterprise_name || '-'}</td>
                <td>${comissao.unit_name || '-'}</td>
                <td>${corrigirEspacamentoNome(comissao.customer_name)}</td>
                <td class="valor-cell">${formatCurrency(comissao.valor_comissao || comissao.commission_value)}</td>
                <td><span class="gatilho-badge ${gatilhoClass}">${gatilhoText}</span></td>
                <td>${formatDate(comissao.data_envio_aprovacao)}</td>
                <td style="text-align: center;">
                    <button 
                        class="btn-observacao ${observacoesComissoes[comissao.id] ? 'tem-observacao' : ''}" 
                        onclick="abrirModalObservacao(${comissao.id}, '${nomeCorretor}', '${comissao.unit_name || '-'}')"
                        title="Adicionar observações para o financeiro">
                        💬
                    </button>
                </td>
            </tr>
        `;
    }).join('');
    
    // Adicionar estilo de animação
    if (!document.getElementById('rowAnimation')) {
        const style = document.createElement('style');
        style.id = 'rowAnimation';
        style.textContent = `
            @keyframes fadeInRow {
                from {
                    opacity: 0;
                    transform: translateY(10px);
                }
                to {
                    opacity: 1;
                    transform: translateY(0);
                }
            }
        `;
        document.head.appendChild(style);
    }
}

// ==================== SELEÇÃO DE COMISSÕES ====================

function toggleComissaoSelecionadaDirecao(checkbox) {
    const id = parseInt(checkbox.dataset.id);
    const row = checkbox.closest('tr');
    
    if (checkbox.checked) {
        if (!comissoesSelecionadasDirecao.includes(id)) {
            comissoesSelecionadasDirecao.push(id);
        }
        row.classList.add('selected');
    } else {
        comissoesSelecionadasDirecao = comissoesSelecionadasDirecao.filter(cId => cId !== id);
        row.classList.remove('selected');
    }
    
    atualizarAcoesLoteDirecao();
}

function toggleTodasDirecao() {
    const checkboxPrincipal = document.getElementById('selecionarTodasDirecao');
    const checkboxes = document.querySelectorAll('.checkbox-comissao-direcao');
    
    comissoesSelecionadasDirecao = [];
    
    checkboxes.forEach(cb => {
        cb.checked = checkboxPrincipal.checked;
        const row = cb.closest('tr');
        
        if (checkboxPrincipal.checked) {
            comissoesSelecionadasDirecao.push(parseInt(cb.dataset.id));
            row.classList.add('selected');
        } else {
            row.classList.remove('selected');
        }
    });
    
    atualizarAcoesLoteDirecao();
}

function atualizarAcoesLoteDirecao() {
    const acoesLote = document.getElementById('acoesLoteDirecao');
    const qtdSelecionadas = document.getElementById('qtdSelecionadas');
    
    if (comissoesSelecionadasDirecao.length > 0) {
        acoesLote.classList.remove('hidden');
        qtdSelecionadas.textContent = comissoesSelecionadasDirecao.length;
    } else {
        acoesLote.classList.add('hidden');
    }
}

// ==================== APROVAR/REJEITAR ====================

async function aprovarComissoesSelecionadas() {
    if (comissoesSelecionadasDirecao.length === 0) {
        showAlert('Selecione ao menos uma comissão', 'error');
        return;
    }
    
    if (!confirm(`Confirma a aprovação de ${comissoesSelecionadasDirecao.length} comissão(ões)?\n\nUm e-mail será enviado ao financeiro.`)) {
        return;
    }
    
    // Mostrar loading nos botões
    const btnAprovar = document.querySelector('.btn-aprovar');
    const originalText = btnAprovar.innerHTML;
    btnAprovar.innerHTML = '<span class="loading-spinner" style="width:20px;height:20px;border-width:2px;margin:0;"></span> Aprovando...';
    btnAprovar.disabled = true;
    
    try {
        // Preparar observações das comissões selecionadas
        const observacoes = {};
        comissoesSelecionadasDirecao.forEach(id => {
            if (observacoesComissoes[id]) {
                observacoes[id] = observacoesComissoes[id];
            }
        });
        
        const response = await fetch('/api/comissoes/aprovar', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                comissoes_ids: comissoesSelecionadasDirecao,
                observacoes: observacoes
            })
        });
        
        const data = await response.json();
        
        if (data.sucesso) {
            showAlert(data.mensagem || 'Comissões aprovadas com sucesso!', 'success');
            if (data.email_enviado) {
                showAlert('E-mail enviado ao financeiro!', 'info');
            }
            comissoesSelecionadasDirecao = [];
            document.getElementById('selecionarTodasDirecao').checked = false;
            carregarComissoesPendentes();
        } else {
            showAlert(data.erro || data.mensagem || 'Erro ao aprovar', 'error');
        }
    } catch (error) {
        console.error('Erro ao aprovar:', error);
        showAlert('Erro ao aprovar comissões', 'error');
    } finally {
        btnAprovar.innerHTML = originalText;
        btnAprovar.disabled = false;
    }
}

function abrirModalRejeitar() {
    if (comissoesSelecionadasDirecao.length === 0) {
        showAlert('Selecione ao menos uma comissão', 'error');
        return;
    }
    
    document.getElementById('modalRejeitar').classList.add('active');
    document.getElementById('motivoRejeicao').value = '';
    setTimeout(() => {
        document.getElementById('motivoRejeicao').focus();
    }, 100);
}

function fecharModalRejeitar() {
    document.getElementById('modalRejeitar').classList.remove('active');
}

async function confirmarRejeicao() {
    const motivo = document.getElementById('motivoRejeicao').value.trim();
    
    if (!motivo) {
        showAlert('Informe o motivo da rejeição', 'error');
        document.getElementById('motivoRejeicao').focus();
        return;
    }
    
    // Mostrar loading
    const btnConfirmar = document.querySelector('.modal-buttons .btn-rejeitar');
    const originalText = btnConfirmar.innerHTML;
    btnConfirmar.innerHTML = '<span class="loading-spinner" style="width:20px;height:20px;border-width:2px;margin:0;"></span> Rejeitando...';
    btnConfirmar.disabled = true;
    
    try {
        // Preparar observações das comissões selecionadas
        const observacoes = {};
        comissoesSelecionadasDirecao.forEach(id => {
            if (observacoesComissoes[id]) {
                observacoes[id] = observacoesComissoes[id];
            }
        });
        
        const response = await fetch('/api/comissoes/rejeitar', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                comissoes_ids: comissoesSelecionadasDirecao,
                motivo: motivo,
                observacoes: observacoes
            })
        });
        
        const data = await response.json();
        
        if (data.sucesso) {
            showAlert(data.mensagem || 'Comissões rejeitadas', 'success');
            comissoesSelecionadasDirecao = [];
            document.getElementById('selecionarTodasDirecao').checked = false;
            fecharModalRejeitar();
            carregarComissoesPendentes();
        } else {
            showAlert(data.erro || data.mensagem || 'Erro ao rejeitar', 'error');
        }
    } catch (error) {
        console.error('Erro ao rejeitar:', error);
        showAlert('Erro ao rejeitar comissões', 'error');
    } finally {
        btnConfirmar.innerHTML = originalText;
        btnConfirmar.disabled = false;
    }
}

// ==================== OBSERVAÇÕES ====================

function abrirModalObservacao(comissaoId, nomeCorretor, lote) {
    comissaoAtualObservacao = comissaoId;
    const modal = document.getElementById('modalObservacao');
    const textarea = document.getElementById('textareaObservacao');
    const info = document.getElementById('infoComissaoModal');
    
    // Preencher informações da comissão
    info.innerHTML = `<strong>Corretor:</strong> ${nomeCorretor} | <strong>Lote:</strong> ${lote}`;
    
    // Carregar observação existente se houver
    textarea.value = observacoesComissoes[comissaoId] || '';
    
    modal.classList.add('active');
    setTimeout(() => textarea.focus(), 100);
}

function fecharModalObservacao() {
    const modal = document.getElementById('modalObservacao');
    modal.classList.remove('active');
    comissaoAtualObservacao = null;
}

function salvarObservacao() {
    if (!comissaoAtualObservacao) return;
    
    const textarea = document.getElementById('textareaObservacao');
    const observacao = textarea.value.trim();
    
    if (observacao) {
        observacoesComissoes[comissaoAtualObservacao] = observacao;
        showAlert('Observação salva! Será enviada ao financeiro.', 'success');
    } else {
        // Remove observação se o campo estiver vazio
        delete observacoesComissoes[comissaoAtualObservacao];
    }
    
    // Atualizar visual do botão
    const btn = document.querySelector(`.btn-observacao[onclick*="${comissaoAtualObservacao}"]`);
    if (btn) {
        if (observacao) {
            btn.classList.add('tem-observacao');
        } else {
            btn.classList.remove('tem-observacao');
        }
    }
    
    fecharModalObservacao();
}

// ==================== NAVEGAÇÃO ENTRE ABAS ====================

function setupNavegacaoDirecao() {
    const tabs = document.querySelectorAll('.nav-tab-direcao');
    const pages = document.querySelectorAll('.page-direcao');
    
    tabs.forEach(tab => {
        tab.addEventListener('click', function() {
            const pageName = this.dataset.page;
            
            // Atualizar abas ativas
            tabs.forEach(t => t.classList.remove('active'));
            this.classList.add('active');
            
            // Atualizar páginas ativas
            pages.forEach(p => p.classList.remove('active'));
            const targetPage = document.getElementById(`page-${pageName}`);
            if (targetPage) {
                targetPage.classList.add('active');
                
                // Carregar conteúdo específico da página
                if (pageName === 'relatorio') {
                    carregarRelatorioComissoesDir();
                }
            }
        });
    });
}

async function carregarFiltrosRelatorioDir() {
    try {
        // Carregar empreendimentos
        const respEmp = await fetch('/api/empreendimentos');
        const empreendimentos = await respEmp.json();
        const selectEmp = document.getElementById('filtroEmpreendimentoDir');
        if (selectEmp && empreendimentos) {
            selectEmp.innerHTML = '<option value="">Todos</option>' + 
                empreendimentos.map(e => `<option value="${e.id}">${e.nome}</option>`).join('');
        }
        
        // Carregar corretores
        const respCorr = await fetch('/api/relatorio-comissoes/corretores');
        const corretores = await respCorr.json();
        const selectCorr = document.getElementById('filtroCorretorDir');
        if (selectCorr && corretores && Array.isArray(corretores)) {
            selectCorr.innerHTML = '<option value="">Todos</option>' + 
                corretores.map(c => `<option value="${c.id}">${c.nome}</option>`).join('');
        }
        
        // Carregar regras
        const respRegras = await fetch('/api/regras-gatilho');
        const regras = await respRegras.json();
        const selectRegra = document.getElementById('filtroRegraDir');
        if (selectRegra && regras) {
            selectRegra.innerHTML = '<option value="">Todas</option>' + 
                regras.map(r => `<option value="${r.id}">${r.nome}</option>`).join('');
        }
    } catch (error) {
        console.error('Erro ao carregar filtros:', error);
    }
}

function carregarRelatorioComissoesDir() {
    carregarFiltrosRelatorioDir();
    buscarRelatorioDir();
}

function buscarRelatorioDir() {
    const container = document.getElementById('conteudoRelatorio');
    if (!container) return;
    
    // Mostrar loading
    container.innerHTML = `
        <div style="text-align: center; padding: 4rem; color: #999;">
            <div class="loading-spinner" style="margin: 0 auto 1.5rem;"></div>
            <p>Carregando relatório...</p>
        </div>
    `;
    
    // Montar URL com filtros
    let url = '/api/relatorio-comissoes?';
    
    const empreendimento = document.getElementById('filtroEmpreendimentoDir')?.value;
    const corretor = document.getElementById('filtroCorretorDir')?.value;
    const regra = document.getElementById('filtroRegraDir')?.value;
    const auditoria = document.getElementById('filtroAuditoriaDir')?.value;
    
    if (empreendimento) url += `empreendimento_id=${empreendimento}&`;
    if (corretor) url += `corretor_id=${corretor}&`;
    if (regra) url += `regra_id=${regra}&`;
    if (auditoria) url += `auditoria=${auditoria}&`;
    
    fetch(url)
        .then(response => response.json())
        .then(data => {
            renderizarRelatorioDir(data);
        })
        .catch(error => {
            console.error('Erro ao carregar relatório:', error);
            container.innerHTML = `
                <div style="text-align: center; padding: 4rem; color: #f87171;">
                    <p>Erro ao carregar relatório.</p>
                </div>
            `;
        });
}

function limparFiltrosDir() {
    document.getElementById('filtroEmpreendimentoDir').value = '';
    document.getElementById('filtroCorretorDir').value = '';
    document.getElementById('filtroRegraDir').value = '';
    document.getElementById('filtroAuditoriaDir').value = '';
    buscarRelatorioDir();
}

function renderizarRelatorioDir(data) {
    const container = document.getElementById('conteudoRelatorio');
    if (!container) return;
    
    // A API retorna 'dados', não 'vendas'
    const vendas = data.dados || [];
    const resumo = data.resumo || {};
    
    if (vendas.length === 0) {
        container.innerHTML = `
            <div style="text-align: center; padding: 4rem; color: #999;">
                <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="#444" stroke-width="1.5" style="margin-bottom: 1rem;">
                    <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
                    <polyline points="14 2 14 8 20 8"/>
                    <line x1="16" y1="13" x2="8" y2="13"/>
                    <line x1="16" y1="17" x2="8" y2="17"/>
                </svg>
                <p style="font-size: 1.1rem; margin-top: 1rem;">Nenhuma venda encontrada</p>
            </div>
        `;
        return;
    }
    
    const linhasHTML = vendas.map(v => {
        // Formatar regra aplicada
        const regraTexto = v.regra_descricao || v.regra_nome || '-';
        
        return `
        <tr>
            <td style="padding: 1rem; border-bottom: 1px solid #333;">${v.lote || '-'}</td>
            <td style="padding: 1rem; border-bottom: 1px solid #333;">${corrigirEspacamentoNome(v.cliente) || '-'}</td>
            <td style="padding: 1rem; border-bottom: 1px solid #333;">${v.empreendimento || '-'}</td>
            <td style="padding: 1rem; border-bottom: 1px solid #333;">${corrigirEspacamentoNome(v.corretor) || '-'}</td>
            <td style="padding: 1rem; border-bottom: 1px solid #333;">
                <div style="display: flex; flex-direction: column; gap: 0.25rem;">
                    <span style="font-weight: 600; color: #FE5009;">${v.regra_nome || 'Não definida'}</span>
                    <span style="font-size: 0.85rem; color: #888;">${regraTexto}</span>
                </div>
            </td>
            <td style="padding: 1rem; border-bottom: 1px solid #333; text-align: center;">
                ${v.auditoria_aprovada ? '<span style="color: #4ade80; font-size: 1.2rem;">✓</span>' : '<span style="color: #666;">-</span>'}
            </td>
            <td style="padding: 1rem; border-bottom: 1px solid #333; text-align: right; font-weight: 600; color: #4ade80;">
                ${formatCurrency(v.valor_comissao)}
            </td>
        </tr>
    `}).join('');
    
    container.innerHTML = `
        <div style="background: #1a1a1a; border: 1px solid #333; border-radius: 12px; padding: 1.5rem;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1.5rem;">
                <div>
                    <h3 style="color: #fff; font-size: 1.2rem; margin-bottom: 0.5rem;">Total de Vendas: ${resumo.total_vendas || vendas.length}</h3>
                    <p style="color: #888; font-size: 0.9rem;">Total em Comissões: ${formatCurrency(resumo.total_comissoes || 0)}</p>
                    <p style="color: #888; font-size: 0.85rem;">Corretores: ${resumo.total_corretores || 0} | Auditorias Aprovadas: ${resumo.auditorias_aprovadas || 0}</p>
                </div>
            </div>
            
            <div style="overflow-x: auto; border: 1px solid #333; border-radius: 8px;">
                <table style="width: 100%; border-collapse: collapse;">
                    <thead>
                        <tr style="background: #0a0a0a;">
                            <th style="padding: 1rem; text-align: left; font-weight: 600; font-size: 0.8rem; text-transform: uppercase; color: #888; border-bottom: 1px solid #333;">Lote</th>
                            <th style="padding: 1rem; text-align: left; font-weight: 600; font-size: 0.8rem; text-transform: uppercase; color: #888; border-bottom: 1px solid #333;">Cliente</th>
                            <th style="padding: 1rem; text-align: left; font-weight: 600; font-size: 0.8rem; text-transform: uppercase; color: #888; border-bottom: 1px solid #333;">Empreendimento</th>
                            <th style="padding: 1rem; text-align: left; font-weight: 600; font-size: 0.8rem; text-transform: uppercase; color: #888; border-bottom: 1px solid #333;">Corretor</th>
                            <th style="padding: 1rem; text-align: left; font-weight: 600; font-size: 0.8rem; text-transform: uppercase; color: #888; border-bottom: 1px solid #333;">Regra Aplicada</th>
                            <th style="padding: 1rem; text-align: center; font-weight: 600; font-size: 0.8rem; text-transform: uppercase; color: #888; border-bottom: 1px solid #333;">Auditoria</th>
                            <th style="padding: 1rem; text-align: right; font-weight: 600; font-size: 0.8rem; text-transform: uppercase; color: #888; border-bottom: 1px solid #333;">Valor Comissão</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${linhasHTML}
                    </tbody>
                </table>
            </div>
        </div>
    `;
}

// ==================== INICIALIZAÇÃO ====================

document.addEventListener('DOMContentLoaded', function() {
    // Setup navegação
    setupNavegacaoDirecao();
    
    // Carregar comissões pendentes
    carregarComissoesPendentes();
    
    // Fechar modais ao clicar fora
    document.getElementById('modalRejeitar').addEventListener('click', function(e) {
        if (e.target === this) {
            fecharModalRejeitar();
        }
    });
    
    document.getElementById('modalObservacao').addEventListener('click', function(e) {
        if (e.target === this) {
            fecharModalObservacao();
        }
    });
    
    // Fechar modais com ESC
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape') {
            fecharModalRejeitar();
            fecharModalObservacao();
        }
    });
    
    // Auto-refresh a cada 60 segundos
    setInterval(function() {
        if (!document.getElementById('modalRejeitar').classList.contains('active') && 
            !document.getElementById('modalObservacao').classList.contains('active')) {
            carregarComissoesPendentes();
        }
    }, 60000);
});
