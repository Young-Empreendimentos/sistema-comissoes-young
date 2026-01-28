/**
 * JavaScript para Dashboard da Direção
 * Sistema de Comissões Young Empreendimentos
 */

// Estado global
let comissoesSelecionadasDirecao = [];

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
        const response = await fetch('/api/comissoes/aprovar', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                comissoes_ids: comissoesSelecionadasDirecao
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
        const response = await fetch('/api/comissoes/rejeitar', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                comissoes_ids: comissoesSelecionadasDirecao,
                motivo: motivo
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

// ==================== INICIALIZAÇÃO ====================

document.addEventListener('DOMContentLoaded', function() {
    carregarComissoesPendentes();
    
    // Fechar modal ao clicar fora
    document.getElementById('modalRejeitar').addEventListener('click', function(e) {
        if (e.target === this) {
            fecharModalRejeitar();
        }
    });
    
    // Fechar modal com ESC
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape') {
            fecharModalRejeitar();
        }
    });
    
    // Auto-refresh a cada 60 segundos
    setInterval(() => {
        if (!document.getElementById('modalRejeitar').classList.contains('active')) {
            carregarComissoesPendentes();
        }
    }, 60000);
});
