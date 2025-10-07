// Market Manus - Interface Web JavaScript

// Inicializar WebSocket
const socket = io();

// Conexão estabelecida
socket.on('connect', () => {
    console.log('✅ Conectado ao servidor WebSocket');
    updateConnectionStatus(true);
});

// Conexão perdida
socket.on('disconnect', () => {
    console.log('❌ Desconectado do servidor WebSocket');
    updateConnectionStatus(false);
});

// Status do servidor
socket.on('status', (data) => {
    console.log('Status:', data.message);
});

// Atualizar indicador de conexão
function updateConnectionStatus(connected) {
    const statusEl = document.getElementById('connection-status');
    if (connected) {
        statusEl.innerHTML = '<i class="bi bi-circle-fill text-success"></i> Online';
    } else {
        statusEl.innerHTML = '<i class="bi bi-circle-fill text-danger"></i> Offline';
    }
}

// Função para mostrar notificações toast
function showToast(title, message, type = 'info') {
    const toastHTML = `
        <div class="toast align-items-center text-white bg-${type} border-0" role="alert">
            <div class="d-flex">
                <div class="toast-body">
                    <strong>${title}</strong><br>${message}
                </div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
            </div>
        </div>
    `;
    
    let container = document.querySelector('.toast-container');
    if (!container) {
        container = document.createElement('div');
        container.className = 'toast-container';
        document.body.appendChild(container);
    }
    
    container.insertAdjacentHTML('beforeend', toastHTML);
    const toastElement = container.lastElementChild;
    const toast = new bootstrap.Toast(toastElement);
    toast.show();
    
    toastElement.addEventListener('hidden.bs.toast', () => {
        toastElement.remove();
    });
}

// Função para formatar valores monetários
function formatCurrency(value) {
    return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'USD',
        minimumFractionDigits: 2
    }).format(value);
}

// Função para formatar percentuais
function formatPercent(value) {
    return `${value >= 0 ? '+' : ''}${value.toFixed(2)}%`;
}

// Função para carregar dados de estratégias
async function loadStrategies() {
    try {
        const response = await fetch('/api/strategies');
        const data = await response.json();
        return data.strategies;
    } catch (error) {
        console.error('Erro ao carregar estratégias:', error);
        showToast('Erro', 'Não foi possível carregar as estratégias', 'danger');
        return [];
    }
}

// Função para carregar combinações
async function loadCombinations() {
    try {
        const response = await fetch('/api/combinations');
        const data = await response.json();
        return data.combinations;
    } catch (error) {
        console.error('Erro ao carregar combinações:', error);
        showToast('Erro', 'Não foi possível carregar as combinações', 'danger');
        return [];
    }
}

// Função para executar backtest
async function runBacktest(config) {
    try {
        const response = await fetch('/api/backtest', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(config)
        });
        const data = await response.json();
        return data;
    } catch (error) {
        console.error('Erro ao executar backtest:', error);
        showToast('Erro', 'Não foi possível executar o backtest', 'danger');
        return null;
    }
}

// Spinner de carregamento
function showSpinner(containerId) {
    const container = document.getElementById(containerId);
    if (container) {
        container.innerHTML = `
            <div class="spinner-container">
                <div class="spinner-border text-primary" role="status">
                    <span class="visually-hidden">Carregando...</span>
                </div>
            </div>
        `;
    }
}

// Ocultar spinner
function hideSpinner(containerId) {
    const container = document.getElementById(containerId);
    if (container) {
        container.innerHTML = '';
    }
}

// Função utilitária para debounce
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// Log global de erros
window.addEventListener('error', (event) => {
    console.error('Erro global:', event.error);
});

// Confirmação antes de sair durante operações importantes
let hasUnsavedChanges = false;
window.addEventListener('beforeunload', (event) => {
    if (hasUnsavedChanges) {
        event.preventDefault();
        event.returnValue = '';
    }
});

console.log('🚀 Market Manus Web Interface carregada!');
