// Viana e Moura - Main JavaScript File
// Professional Recruitment Platform

document.addEventListener('DOMContentLoaded', function() {
    // Initialize all components
    initializeFormValidation();
    initializeFileUpload();
    initializeTooltips();
    initializeRealTimeUpdates();
    initializeSearchAndFilter();
    initializeDashboardCharts();
    initializeNotifications();
    initializeThemeToggle();
    initializeLanguageSelector();
});

// Form Validation Enhancement
function initializeFormValidation() {
    const forms = document.querySelectorAll('form');
    
    forms.forEach(form => {
        form.addEventListener('submit', function(e) {
            if (!validateForm(this)) {
                e.preventDefault();
                e.stopPropagation();
            }
            this.classList.add('was-validated');
        });
    });
}

function validateForm(form) {
    const requiredFields = form.querySelectorAll('[required]');
    let isValid = true;
    
    requiredFields.forEach(field => {
        if (!field.value.trim()) {
            showFieldError(field, 'Este campo é obrigatório');
            isValid = false;
        } else {
            hideFieldError(field);
        }
        
        // Email validation
        if (field.type === 'email' && field.value) {
            const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
            if (!emailRegex.test(field.value)) {
                showFieldError(field, 'Por favor, insira um email válido');
                isValid = false;
            }
        }
        
        // Password validation
        if (field.type === 'password' && field.value) {
            if (field.value.length < 6) {
                showFieldError(field, 'A senha deve ter pelo menos 6 caracteres');
                isValid = false;
            }
        }
    });
    
    return isValid;
}

function showFieldError(field, message) {
    hideFieldError(field);
    
    const errorDiv = document.createElement('div');
    errorDiv.className = 'invalid-feedback';
    errorDiv.textContent = message;
    
    field.classList.add('is-invalid');
    field.parentNode.appendChild(errorDiv);
}

function hideFieldError(field) {
    field.classList.remove('is-invalid');
    const errorDiv = field.parentNode.querySelector('.invalid-feedback');
    if (errorDiv) {
        errorDiv.remove();
    }
}

// Enhanced File Upload with Drag & Drop
function initializeFileUpload() {
    const fileInputs = document.querySelectorAll('input[type="file"]');
    
    fileInputs.forEach(input => {
        const container = input.closest('.modal-body') || input.parentNode;
        
        // Create drop zone
        const dropZone = document.createElement('div');
        dropZone.className = 'file-upload-area mt-3';
        dropZone.innerHTML = `
            <i class="fas fa-cloud-upload-alt fa-3x text-muted mb-3"></i>
            <p class="text-muted mb-2">Arraste e solte os arquivos aqui ou clique para selecionar</p>
            <p class="text-muted small">Formatos aceitos: PDF, DOCX, TXT</p>
        `;
        
        input.parentNode.insertBefore(dropZone, input.nextSibling);
        
        // Drag and drop events
        dropZone.addEventListener('dragover', function(e) {
            e.preventDefault();
            this.classList.add('dragover');
        });
        
        dropZone.addEventListener('dragleave', function(e) {
            e.preventDefault();
            this.classList.remove('dragover');
        });
        
        dropZone.addEventListener('drop', function(e) {
            e.preventDefault();
            this.classList.remove('dragover');
            
            const files = e.dataTransfer.files;
            handleFileSelection(files, input);
        });
        
        dropZone.addEventListener('click', function() {
            input.click();
        });
        
        input.addEventListener('change', function(e) {
            handleFileSelection(e.target.files, input);
        });
    });
}

function handleFileSelection(files, input) {
    const validTypes = ['application/pdf', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document', 'text/plain'];
    const maxSize = 16 * 1024 * 1024; // 16MB
    
    let validFiles = [];
    let errors = [];
    
    Array.from(files).forEach(file => {
        if (!validTypes.includes(file.type)) {
            errors.push(`${file.name}: Tipo de arquivo não suportado`);
            return;
        }
        
        if (file.size > maxSize) {
            errors.push(`${file.name}: Arquivo muito grande (máximo 16MB)`);
            return;
        }
        
        validFiles.push(file);
    });
    
    if (errors.length > 0) {
        showNotification('Erros nos arquivos:\n' + errors.join('\n'), 'error');
    }
    
    if (validFiles.length > 0) {
        // Update file input
        const dataTransfer = new DataTransfer();
        validFiles.forEach(file => dataTransfer.items.add(file));
        input.files = dataTransfer.files;
        
        // Update UI
        updateFileList(validFiles, input);
        showNotification(`${validFiles.length} arquivo(s) selecionado(s)`, 'success');
    }
}

function updateFileList(files, input) {
    const existingList = input.parentNode.querySelector('.selected-files');
    if (existingList) {
        existingList.remove();
    }
    
    const fileList = document.createElement('div');
    fileList.className = 'selected-files mt-3';
    fileList.innerHTML = '<h6>Arquivos Selecionados:</h6>';
    
    const list = document.createElement('ul');
    list.className = 'list-group list-group-flush';
    
    Array.from(files).forEach(file => {
        const listItem = document.createElement('li');
        listItem.className = 'list-group-item d-flex justify-content-between align-items-center';
        listItem.innerHTML = `
            <span>
                <i class="fas fa-file-alt me-2"></i>${file.name}
                <small class="text-muted ms-2">(${formatFileSize(file.size)})</small>
            </span>
            <span class="badge bg-primary rounded-pill">${getFileIcon(file.type)}</span>
        `;
        list.appendChild(listItem);
    });
    
    fileList.appendChild(list);
    input.parentNode.appendChild(fileList);
}

function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

function getFileIcon(type) {
    switch (type) {
        case 'application/pdf':
            return 'PDF';
        case 'application/vnd.openxmlformats-officedocument.wordprocessingml.document':
            return 'DOCX';
        case 'text/plain':
            return 'TXT';
        default:
            return 'FILE';
    }
}

// Initialize Bootstrap Tooltips
function initializeTooltips() {
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function(tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
}

// Real-time Updates for Analysis Status
function initializeRealTimeUpdates() {
    const candidateStatusElements = document.querySelectorAll('[data-candidate-id]');
    
    candidateStatusElements.forEach(element => {
        const candidateId = element.getAttribute('data-candidate-id');
        if (candidateId) {
            // Check status every 30 seconds for processing candidates
            setInterval(() => checkCandidateStatus(candidateId), 30000);
        }
    });
}

function checkCandidateStatus(candidateId) {
    // This would typically make an AJAX call to check status
    // For now, we'll just update the UI based on existing data
    const statusElement = document.querySelector(`[data-candidate-id="${candidateId}"] .analysis-status`);
    if (statusElement && statusElement.textContent.includes('Processando')) {
        // Add pulse animation to processing indicators
        statusElement.classList.add('status-indicator', 'processing');
    }
}

// Enhanced Search and Filter
function initializeSearchAndFilter() {
    const searchInputs = document.querySelectorAll('input[type="search"], input[placeholder*="buscar"]');
    
    searchInputs.forEach(input => {
        input.addEventListener('input', debounce(function(e) {
            performSearch(e.target.value, e.target);
        }, 300));
    });
    
    // Filter dropdowns
    const filterSelects = document.querySelectorAll('select[id*="Filter"]');
    filterSelects.forEach(select => {
        select.addEventListener('change', function(e) {
            applyFilters();
        });
    });
}

function performSearch(query, input) {
    const searchableElements = document.querySelectorAll('.searchable');
    
    searchableElements.forEach(element => {
        const text = element.textContent.toLowerCase();
        const matches = text.includes(query.toLowerCase());
        
        const container = element.closest('.card, tr, .list-group-item');
        if (container) {
            container.style.display = matches ? '' : 'none';
        }
    });
}

function applyFilters() {
    // This function is called when filters are changed
    // It works with the existing filterCandidates function
    if (typeof filterCandidates === 'function') {
        filterCandidates();
    }
}

// Dashboard Charts Enhancement
function initializeDashboardCharts() {
    // Add chart responsiveness
    const charts = document.querySelectorAll('canvas');
    
    charts.forEach(canvas => {
        const ctx = canvas.getContext('2d');
        
        // Add hover effects
        canvas.addEventListener('mouseover', function() {
            this.style.cursor = 'pointer';
        });
        
        canvas.addEventListener('mouseout', function() {
            this.style.cursor = 'default';
        });
    });
}

// Notification System
function initializeNotifications() {
    // Create notification container if it doesn't exist
    if (!document.querySelector('.notification-container')) {
        const container = document.createElement('div');
        container.className = 'notification-container position-fixed top-0 end-0 p-3';
        container.style.zIndex = '9999';
        document.body.appendChild(container);
    }
}

function showNotification(message, type = 'info', duration = 5000) {
    const container = document.querySelector('.notification-container');
    
    const notification = document.createElement('div');
    notification.className = `alert alert-${type} alert-dismissible fade show`;
    notification.setAttribute('role', 'alert');
    notification.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    container.appendChild(notification);
    
    // Auto-dismiss after duration
    setTimeout(() => {
        if (notification.parentNode) {
            notification.classList.remove('show');
            setTimeout(() => {
                if (notification.parentNode) {
                    notification.remove();
                }
            }, 300);
        }
    }, duration);
}

// Utility Functions
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

function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString('pt-BR', {
        day: '2-digit',
        month: '2-digit',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}

function formatScore(score) {
    return parseFloat(score).toFixed(1);
}

// Enhanced Table Interactions
function initializeTableFeatures() {
    const tables = document.querySelectorAll('table');
    
    tables.forEach(table => {
        // Add sorting capability
        const headers = table.querySelectorAll('th');
        headers.forEach(header => {
            if (header.textContent.trim()) {
                header.style.cursor = 'pointer';
                header.addEventListener('click', function() {
                    sortTable(table, Array.from(headers).indexOf(this));
                });
            }
        });
        
        // Add row selection
        const rows = table.querySelectorAll('tbody tr');
        rows.forEach(row => {
            row.addEventListener('click', function() {
                // Remove selection from other rows
                rows.forEach(r => r.classList.remove('table-active'));
                // Add selection to clicked row
                this.classList.add('table-active');
            });
        });
    });
}

function sortTable(table, column) {
    const tbody = table.querySelector('tbody');
    const rows = Array.from(tbody.rows);
    
    const sorted = rows.sort((a, b) => {
        const aText = a.cells[column].textContent.trim();
        const bText = b.cells[column].textContent.trim();
        
        // Try to parse as numbers first
        const aNum = parseFloat(aText);
        const bNum = parseFloat(bText);
        
        if (!isNaN(aNum) && !isNaN(bNum)) {
            return aNum - bNum;
        }
        
        // Sort as strings
        return aText.localeCompare(bText);
    });
    
    // Re-append sorted rows
    sorted.forEach(row => tbody.appendChild(row));
}

// Modal Enhancements
function initializeModalFeatures() {
    const modals = document.querySelectorAll('.modal');
    
    modals.forEach(modal => {
        // Reset forms when modal is closed
        modal.addEventListener('hidden.bs.modal', function() {
            const forms = this.querySelectorAll('form');
            forms.forEach(form => {
                form.reset();
                form.classList.remove('was-validated');
                
                // Remove validation messages
                const errorMessages = form.querySelectorAll('.invalid-feedback');
                errorMessages.forEach(msg => msg.remove());
                
                // Remove validation classes
                const inputs = form.querySelectorAll('.is-invalid, .is-valid');
                inputs.forEach(input => input.classList.remove('is-invalid', 'is-valid'));
            });
        });
        
        // Focus first input when modal opens
        modal.addEventListener('shown.bs.modal', function() {
            const firstInput = this.querySelector('input:not([type="hidden"]), textarea, select');
            if (firstInput) {
                firstInput.focus();
            }
        });
    });
}

// Loading States
function showLoadingState(element, message = 'Carregando...') {
    const originalContent = element.innerHTML;
    element.dataset.originalContent = originalContent;
    
    element.innerHTML = `
        <div class="d-flex align-items-center">
            <div class="spinner-border spinner-border-sm me-2" role="status">
                <span class="visually-hidden">Loading...</span>
            </div>
            ${message}
        </div>
    `;
    
    element.disabled = true;
}

function hideLoadingState(element) {
    if (element.dataset.originalContent) {
        element.innerHTML = element.dataset.originalContent;
        delete element.dataset.originalContent;
    }
    element.disabled = false;
}

// Enhanced Form Submission
function enhanceFormSubmission() {
    const forms = document.querySelectorAll('form');
    
    forms.forEach(form => {
        form.addEventListener('submit', function(e) {
            const submitBtn = this.querySelector('button[type="submit"]');
            if (submitBtn) {
                showLoadingState(submitBtn, 'Enviando...');
                
                // Re-enable button after 10 seconds (fallback)
                setTimeout(() => {
                    hideLoadingState(submitBtn);
                }, 10000);
            }
        });
    });
}

// Keyboard Shortcuts
function initializeKeyboardShortcuts() {
    document.addEventListener('keydown', function(e) {
        // Ctrl/Cmd + K for search
        if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
            e.preventDefault();
            const searchInput = document.querySelector('input[type="search"]');
            if (searchInput) {
                searchInput.focus();
            }
        }
        
        // Escape to close modals
        if (e.key === 'Escape') {
            const openModal = document.querySelector('.modal.show');
            if (openModal) {
                const bsModal = bootstrap.Modal.getInstance(openModal);
                if (bsModal) {
                    bsModal.hide();
                }
            }
        }
    });
}

// Initialize all features when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    initializeTableFeatures();
    initializeModalFeatures();
    enhanceFormSubmission();
    initializeKeyboardShortcuts();
    
    // Add fade-in animation to cards
    const cards = document.querySelectorAll('.card');
    cards.forEach((card, index) => {
        card.style.opacity = '0';
        card.style.transform = 'translateY(20px)';
        
        setTimeout(() => {
            card.style.transition = 'opacity 0.6s ease, transform 0.6s ease';
            card.style.opacity = '1';
            card.style.transform = 'translateY(0)';
        }, index * 100);
    });
});

// Theme Toggle System
function initializeThemeToggle() {
    console.log('🔍 Iniciando sistema de tema...');
    
    // Aguarda um pouco para garantir que o DOM esteja pronto
    setTimeout(() => {
        const themeToggle = document.getElementById('themeToggle');
        const themeIcon = document.getElementById('themeIcon');
        
        console.log('🔍 Elementos encontrados:');
        console.log('Theme toggle:', themeToggle);
        console.log('Theme icon:', themeIcon);
        
        if (!themeToggle) {
            console.error('❌ Botão de tema não encontrado!');
            return;
        }
        
        // Carrega tema salvo
        const savedTheme = localStorage.getItem('theme') || 'light';
        console.log('📱 Tema salvo:', savedTheme);
        
        // Aplica tema imediatamente
        document.documentElement.setAttribute('data-theme', savedTheme);
        updateThemeIcon(savedTheme);
        
        // Força atualização do navbar
        updateNavbarTheme(savedTheme);
        
        // Adiciona evento de clique
        themeToggle.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();
            
            console.log('🖱️ Botão de tema clicado!');
            
            const currentTheme = document.documentElement.getAttribute('data-theme') || 'light';
            const newTheme = currentTheme === 'light' ? 'dark' : 'light';
            
            console.log('🔄 Alterando tema de', currentTheme, 'para', newTheme);
            
            // Aplica novo tema
            document.documentElement.setAttribute('data-theme', newTheme);
            localStorage.setItem('theme', newTheme);
            updateThemeIcon(newTheme);
            
            // Força atualização do navbar
            updateNavbarTheme(newTheme);
            
            // Mostra notificação
            const themeName = newTheme === 'light' ? 'Claro' : 'Escuro';
            showNotification(`Tema alterado para ${themeName}`, 'success', 2000);
            
            console.log('✅ Tema alterado com sucesso para:', newTheme);
        });
        
        console.log('✅ Sistema de tema inicializado com sucesso');
    }, 100);
}

function updateThemeIcon(theme) {
    const themeIcon = document.getElementById('themeIcon');
    if (themeIcon) {
        if (theme === 'dark') {
            themeIcon.className = 'fas fa-sun';
            themeIcon.title = 'Mudar para tema claro';
        } else {
            themeIcon.className = 'fas fa-moon';
            themeIcon.title = 'Mudar para tema escuro';
        }
    }
}

function updateNavbarTheme(theme) {
    const navbar = document.querySelector('.navbar');
    if (navbar) {
        // Remove classes de tema anteriores
        navbar.classList.remove('navbar-light', 'navbar-dark');
        
        // Adiciona classe apropriada
        if (theme === 'dark') {
            navbar.classList.add('navbar-dark');
        } else {
            navbar.classList.add('navbar-light');
        }
        
        // Força re-renderização
        navbar.style.transition = 'all 0.3s ease';
        
        console.log('🎨 Navbar atualizado para tema:', theme);
    }
}

// Language Selector System
function initializeLanguageSelector() {
    const languageDropdown = document.getElementById('languageDropdown');
    const currentLanguageSpan = document.getElementById('currentLanguage');
    const languageOptions = document.querySelectorAll('.language-option');
    
    if (!languageDropdown) {
        console.log('❌ Seletor de idioma não encontrado');
        return;
    }
    
    console.log('🌍 Iniciando seletor de idioma...');
    
    // Load saved language from localStorage
    const savedLanguage = localStorage.getItem('language') || 'pt';
    console.log('📱 Idioma salvo:', savedLanguage);
    
    updateCurrentLanguage(savedLanguage);
    
            // Apply saved language translations
        applyTranslations(savedLanguage);
        
        // Apply score colors after language initialization
        // setTimeout(() => {
        //     applyScoreColors();
        // }, 500);
        
        languageOptions.forEach(option => {
        option.addEventListener('click', function(e) {
            e.preventDefault();
            const lang = this.getAttribute('data-lang');
            console.log('🌍 Idioma selecionado:', lang);
            changeLanguage(lang);
        });
    });
    
    console.log('✅ Seletor de idioma inicializado com sucesso');
}

function changeLanguage(lang) {
    // Save language preference
    localStorage.setItem('language', lang);
    
    // Update UI
    updateCurrentLanguage(lang);
    
    // Show notification
    const langNames = {
        'pt': 'Português',
        'en': 'English',
        'es': 'Español'
    };
    
    showNotification(`Idioma alterado para ${langNames[lang]}`, 'success', 2000);
    
    // Apply translations immediately
    applyTranslations(lang);
}

function applyTranslations(lang) {
    console.log('🌍 Aplicando traduções para:', lang);
    
    // Dicionário de traduções expandido
    const translations = {
        'pt': {
            'Dashboard': 'Dashboard',
            'Vagas': 'Vagas',
            'Candidatos': 'Candidatos',
            'Dashboard de Recrutamento': 'Dashboard de Recrutamento',
            'Visão geral do processo de recrutamento inteligente com IA': 'Visão geral do processo de recrutamento inteligente com IA',
            'Sobre o Sistema': 'Sobre o Sistema',
            'Viana e Moura - Sistema de Recrutamento Inteligente': 'Viana e Moura - Sistema de Recrutamento Inteligente',
            'Funcionalidades Principais': 'Funcionalidades Principais',
            'Upload em lote de currículos': 'Upload em lote de currículos',
            'Análise automática com IA': 'Análise automática com IA',
            'Pontuação inteligente': 'Pontuação inteligente',
            'Filtros avançados': 'Filtros avançados',
            'Objetivos': 'Objetivos',
            'Reduzir tempo de triagem': 'Reduzir tempo de triagem',
            'Melhorar qualidade da seleção': 'Melhorar qualidade da seleção',
            'Otimizar processo de recrutamento': 'Otimizar processo de recrutamento',
            'Identificar melhores candidatos': 'Identificar melhores candidatos',
            'VAGAS ATIVAS': 'VAGAS ATIVAS',
            'TOTAL CANDIDATOS': 'TOTAL CANDIDATOS',
            'ANÁLISES CONCLUÍDAS': 'ANÁLISES CONCLUÍDAS',
            'TAXA DE ANÁLISE': 'TAXA DE ANÁLISE',
            'Gerenciamento de Vagas': 'Gerenciamento de Vagas',
            'Crie e gerencie vagas de emprego com análise automática de candidatos': 'Crie e gerencie vagas de emprego com análise automática de candidatos',
            'Nova Vaga': 'Nova Vaga',
            'Todos os Candidatos': 'Todos os Candidatos',
            'Pesquisar por nome do candidato...': 'Pesquisar por nome do candidato...',
            'Ver Detalhes': 'Ver Detalhes',
            'PENDENTE': 'PENDENTE',
            'ANALISADO': 'ANALISADO',
            'INFORMAÇÕES PESSOAIS': 'INFORMAÇÕES PESSOAIS',
            'Nome Completo': 'Nome Completo',
            'INFORMAÇÕES DE CONTATO': 'INFORMAÇÕES DE CONTATO',
            'Expandir Todos': 'Expandir Todos',
            'Colapsar Todos': 'Colapsar Todos',
            'Score minim': 'Score mínimo',
            'Todos os Stat': 'Todos os Status',
            'Vagas Recentes': 'Vagas Recentes',
            'Top Candidatos': 'Top Candidatos',
            'Ver Todas as Vagas': 'Ver Todas as Vagas',
            'ATIVA': 'ATIVA',
            'candidatos': 'candidatos',
            'analisados': 'analisados',
            'CANDIDATOS': 'CANDIDATOS',
            'ANALISADOS': 'ANALISADOS',
            'Monitor de Processamento': 'Monitor de Processamento',
            'Voltar': 'Voltar',
            'Total de Currículos': 'Total de Currículos',
            'Pendentes': 'Pendentes',
            'Processando': 'Processando',
            'Concluídos': 'Concluídos',
            'Progresso da Análise': 'Progresso da Análise',
            'Progresso Geral': 'Progresso Geral',
            'Iniciar Processamento': 'Iniciar Processamento',
            'Resetar Presos': 'Resetar Presos',
            'Status em Tempo Real': 'Status em Tempo Real',
            'Monitoramento Ativo': 'Monitoramento Ativo',
            'Última atualização': 'Última atualização',
            'Lista de Candidatos': 'Lista de Candidatos',
            'CONCLUÍDO': 'CONCLUÍDO',
            'Descrição da Vaga': 'Descrição da Vaga',
            'Habilidades e Requisitos': 'Habilidades e Requisitos',
            'Estatísticas': 'Estatísticas',
            'Candidates': 'Candidatos',
            'Analisados': 'Analisados',
            'Processamento IA': 'Processamento IA',
            'Processando': 'Processando',
            'Concluído': 'Concluído',
            'Falhou': 'Falhou',
            'Pendente': 'Pendente',
            'Editar': 'Editar',
            'Monitor IA': 'Monitor IA',
            'Excluir Vaga': 'Excluir Vaga',
            'Criada em': 'Criada em',
            'Formatos aceitos': 'Formatos aceitos',
            'máximo 16MB por arquivo': 'máximo 16MB por arquivo',
            'Clique para expandir': 'Clique para expandir',
            'Auxiliar de Vendas': 'Auxiliar de Vendas',
            'Panel': 'Dashboard',
            'Trabajos': 'Vagas',
            'Panel de Reclutamiento': 'Dashboard de Recrutamento',
            'Vista general del proceso de reclutamiento inteligente con IA': 'Visão geral do processo de recrutamento inteligente com IA',
            'Sobre el Sistema': 'Sobre o Sistema',
            'Sistema de Reclutamiento Inteligente': 'Sistema de Recrutamento Inteligente',
            'Características Principales': 'Funcionalidades Principais',
            'Carga masiva de currículos': 'Upload em lote de currículos',
            'Análisis automático con IA': 'Análise automática com IA',
            'Puntuación inteligente': 'Pontuação inteligente',
            'Filtros avanzados': 'Filtros avançados',
            'Objetivos': 'Objetivos',
            'Reducir tiempo de cribado': 'Reduzir tempo de triagem',
            'Mejorar calidad de selección': 'Melhorar qualidade da seleção',
            'Optimizar proceso de reclutamiento': 'Otimizar processo de recrutamento',
            'Identificar mejores candidatos': 'Identificar melhores candidatos',
            'TRABAJOS ACTIVOS': 'VAGAS ATIVAS',
            'TOTAL CANDIDATOS': 'TOTAL CANDIDATOS',
            'ANÁLISIS COMPLETADOS': 'ANÁLISES CONCLUÍDAS',
            'TASA DE ANÁLISIS': 'TAXA DE ANÁLISE',
            'Gestión de Trabajos': 'Gerenciamento de Vagas',
            'Cree y gestione puestos de trabajo con análisis automático de candidatos': 'Crie e gerencie vagas de emprego com análise automática de candidatos',
            'Nuevo Trabajo': 'Nova Vaga',
            'Todos los Candidatos': 'Todos os Candidatos',
            'Buscar por nombre del candidato...': 'Pesquisar por nome do candidato...',
            'Ver Detalles': 'Ver Detalhes',
            'PENDIENTE': 'PENDENTE',
            'ANALIZADO': 'ANALISADO',
            'INFORMACIÓN PERSONAL': 'INFORMAÇÕES PESSOAIS',
            'Nombre Completo': 'Nome Completo',
            'INFORMACIÓN DE CONTACTO': 'INFORMAÇÕES DE CONTATO',
            'Expandir Todos': 'Expandir Todos',
            'Colapsar Todos': 'Colapsar Todos',
            'Puntuación Mín': 'Score mínimo',
            'Todos los Estados': 'Todos os Status',
            'Trabajos Recientes': 'Vagas Recentes',
            'Mejores Candidatos': 'Top Candidatos',
            'Ver Todos los Trabajos': 'Ver Todas as Vagas',
            'ACTIVA': 'ATIVA',
            'candidatos': 'candidatos',
            'analizados': 'analisados',
            'CANDIDATOS': 'CANDIDATOS',
            'ANALIZADOS': 'ANALISADOS',
            'Monitor de Procesamiento': 'Monitor de Processamento',
            'Volver': 'Voltar',
            'Total de Currículos': 'Total de Currículos',
            'Pendientes': 'Pendentes',
            'Procesando': 'Processando',
            'Completados': 'Concluídos',
            'Progreso del Análisis': 'Progresso da Análise',
            'Progreso General': 'Progresso Geral',
            'Iniciar Procesamiento': 'Iniciar Processamento',
            'Reiniciar Bloqueados': 'Resetar Presos',
            'Estado en Tiempo Real': 'Status em Tempo Real',
            'Monitoreo Activo': 'Monitoramento Ativo',
            'Última actualización': 'Última atualização',
            'Lista de Candidatos': 'Lista de Candidatos',
            'COMPLETADO': 'CONCLUÍDO',
            'Descripción del Trabajo': 'Descrição da Vaga',
            'Habilidades y Requisitos': 'Habilidades e Requisitos',
            'Estadísticas': 'Estatísticas',
            'Candidatos': 'Candidatos',
            'Analizados': 'Analisados',
            'Procesamiento IA': 'Processamento IA',
            'Procesando': 'Processando',
            'Completado': 'Concluído',
            'Falló': 'Falhou',
            'Pendiente': 'Pendente',
            'Editar': 'Editar',
            'Monitor IA': 'Monitor IA',
            'Eliminar Trabajo': 'Excluir Vaga',
            'Creado el': 'Criada em',
            'Formatos aceptados': 'Formatos aceitos',
            'máximo 16MB por archivo': 'máximo 16MB por arquivo',
            'Haga clic para expandir': 'Clique para expandir',
            'Asistente de Ventas': 'Auxiliar de Vendas'
        },
        'en': {
            'Dashboard': 'Dashboard',
            'Vagas': 'Jobs',
            'Candidatos': 'Candidates',
            'Dashboard de Recrutamento': 'Recruitment Dashboard',
            'Visão geral do processo de recrutamento inteligente com IA': 'Overview of the intelligent recruitment process with AI',
            'Sobre o Sistema': 'About the System',
            'Viana e Moura - Sistema de Recrutamento Inteligente': 'Viana e Moura - Intelligent Recruitment System',
            'Funcionalidades Principais': 'Main Features',
            'Upload em lote de currículos': 'Batch resume upload',
            'Análise automática com IA': 'Automatic AI analysis',
            'Pontuação inteligente': 'Intelligent scoring',
            'Filtros avançados': 'Advanced filters',
            'Objetivos': 'Objectives',
            'Reduzir tempo de triagem': 'Reduce screening time',
            'Melhorar qualidade da seleção': 'Improve selection quality',
            'Otimizar processo de recrutamento': 'Optimize recruitment process',
            'Identificar melhores candidatos': 'Identify best candidates',
            'VAGAS ATIVAS': 'ACTIVE JOBS',
            'TOTAL CANDIDATOS': 'TOTAL CANDIDATES',
            'ANÁLISES CONCLUÍDAS': 'COMPLETED ANALYSES',
            'TAXA DE ANÁLISE': 'ANALYSIS RATE',
            'Gerenciamento de Vagas': 'Job Management',
            'Crie e gerencie vagas de emprego com análise automática de candidatos': 'Create and manage job positions with automatic candidate analysis',
            'Nova Vaga': 'New Job',
            'Todos os Candidatos': 'All Candidates',
            'Pesquisar por nome do candidato...': 'Search by candidate name...',
            'Ver Detalhes': 'View Details',
            'PENDENTE': 'PENDING',
            'ANALISADO': 'ANALYZED',
            'INFORMAÇÕES PESSOAIS': 'PERSONAL INFORMATION',
            'Nome Completo': 'Full Name',
            'INFORMAÇÕES DE CONTATO': 'CONTACT INFORMATION',
            'Expandir Todos': 'Expand All',
            'Colapsar Todos': 'Collapse All',
            'Score minim': 'Min Score',
            'Todos os Stat': 'All Status',
            'Vagas Recentes': 'Recent Jobs',
            'Top Candidatos': 'Top Candidates',
            'Ver Todas as Vagas': 'View All Jobs',
            'ATIVA': 'ACTIVE',
            'candidatos': 'candidates',
            'analisados': 'analyzed',
            'CANDIDATOS': 'CANDIDATES',
            'ANALISADOS': 'ANALYZED',
            'Monitor de Processamento': 'Processing Monitor',
            'Voltar': 'Back',
            'Total de Currículos': 'Total Resumes',
            'Pendentes': 'Pending',
            'Processando': 'Processing',
            'Concluídos': 'Completed',
            'Progresso da Análise': 'Analysis Progress',
            'Progresso Geral': 'General Progress',
            'Iniciar Processamento': 'Start Processing',
            'Resetar Presos': 'Reset Stuck',
            'Status em Tempo Real': 'Real-time Status',
            'Monitoramento Ativo': 'Active Monitoring',
            'Última atualização': 'Last update',
            'Lista de Candidatos': 'Candidate List',
            'CONCLUÍDO': 'COMPLETED',
            'Descrição da Vaga': 'Job Description',
            'Habilidades e Requisitos': 'Skills and Requirements',
            'Estatísticas': 'Statistics',
            'Candidates': 'Candidates',
            'Analisados': 'Analyzed',
            'Processamento IA': 'AI Processing',
            'Processando': 'Processing',
            'Concluído': 'Completed',
            'Falhou': 'Failed',
            'Pendente': 'Pending',
            'Editar': 'Edit',
            'Monitor IA': 'AI Monitor',
            'Excluir Vaga': 'Delete Job',
            'Criada em': 'Created on',
            'Formatos aceitos': 'Accepted formats',
            'máximo 16MB por arquivo': 'maximum 16MB per file',
            'Clique para expandir': 'Click to expand',
            'Auxiliar de Vendas': 'Sales Assistant',
            'Panel': 'Dashboard',
            'Trabajos': 'Jobs',
            'Panel de Reclutamiento': 'Recruitment Dashboard',
            'Vista general del proceso de reclutamiento inteligente con IA': 'Overview of the intelligent recruitment process with AI',
            'Sobre el Sistema': 'About the System',
            'Sistema de Reclutamiento Inteligente': 'Intelligent Recruitment System',
            'Características Principales': 'Main Features',
            'Carga masiva de currículos': 'Batch resume upload',
            'Análisis automático con IA': 'Automatic AI analysis',
            'Puntuación inteligente': 'Intelligent scoring',
            'Filtros avanzados': 'Advanced filters',
            'Objetivos': 'Objectives',
            'Reducir tiempo de cribado': 'Reduce screening time',
            'Mejorar calidad de selección': 'Improve selection quality',
            'Optimizar proceso de reclutamiento': 'Optimize recruitment process',
            'Identificar mejores candidatos': 'Identify best candidates',
            'TRABAJOS ACTIVOS': 'ACTIVE JOBS',
            'TOTAL CANDIDATOS': 'TOTAL CANDIDATES',
            'ANÁLISIS COMPLETADOS': 'COMPLETED ANALYSES',
            'TASA DE ANÁLISIS': 'ANALYSIS RATE',
            'Gestión de Trabajos': 'Job Management',
            'Cree y gestione puestos de trabajo con análisis automático de candidatos': 'Create and manage job positions with automatic candidate analysis',
            'Nuevo Trabajo': 'New Job',
            'Todos los Candidatos': 'All Candidates',
            'Buscar por nombre del candidato...': 'Search by candidate name...',
            'Ver Detalles': 'View Details',
            'PENDIENTE': 'PENDING',
            'ANALIZADO': 'ANALYZED',
            'INFORMACIÓN PERSONAL': 'PERSONAL INFORMATION',
            'Nombre Completo': 'Full Name',
            'INFORMACIÓN DE CONTACTO': 'CONTACT INFORMATION',
            'Expandir Todos': 'Expand All',
            'Colapsar Todos': 'Collapse All',
            'Puntuación Mín': 'Min Score',
            'Todos los Estados': 'All Status',
            'Trabajos Recientes': 'Recent Jobs',
            'Mejores Candidatos': 'Top Candidates',
            'Ver Todos los Trabajos': 'View All Jobs',
            'ACTIVA': 'ACTIVE',
            'candidatos': 'candidates',
            'analizados': 'analyzed',
            'CANDIDATOS': 'CANDIDATES',
            'ANALIZADOS': 'ANALYZED',
            'Monitor de Procesamiento': 'Processing Monitor',
            'Volver': 'Back',
            'Total de Currículos': 'Total Resumes',
            'Pendientes': 'Pending',
            'Procesando': 'Processing',
            'Completados': 'Completed',
            'Progreso del Análisis': 'Analysis Progress',
            'Progreso General': 'General Progress',
            'Iniciar Procesamiento': 'Start Processing',
            'Reiniciar Bloqueados': 'Reset Stuck',
            'Estado en Tiempo Real': 'Real-time Status',
            'Monitoreo Activo': 'Active Monitoring',
            'Última actualización': 'Last update',
            'Lista de Candidatos': 'Candidate List',
            'COMPLETADO': 'COMPLETED',
            'Descripción del Trabajo': 'Job Description',
            'Habilidades y Requisitos': 'Skills and Requirements',
            'Estadísticas': 'Statistics',
            'Candidatos': 'Candidates',
            'Analizados': 'Analyzed',
            'Procesamiento IA': 'AI Processing',
            'Procesando': 'Processing',
            'Completado': 'Completed',
            'Falló': 'Failed',
            'Pendiente': 'Pending',
            'Editar': 'Edit',
            'Monitor IA': 'AI Monitor',
            'Eliminar Trabajo': 'Delete Job',
            'Creado el': 'Created on',
            'Formatos aceptados': 'Accepted formats',
            'máximo 16MB por archivo': 'maximum 16MB per file',
            'Haga clic para expandir': 'Click to expand',
            'Asistente de Ventas': 'Sales Assistant'
        },
        'es': {
            'Dashboard': 'Panel',
            'Vagas': 'Trabajos',
            'Candidatos': 'Candidatos',
            'Dashboard de Recrutamento': 'Panel de Reclutamiento',
            'Visão geral do processo de recrutamento inteligente com IA': 'Vista general del proceso de reclutamiento inteligente con IA',
            'Sobre o Sistema': 'Sobre el Sistema',
            'Viana e Moura - Sistema de Recrutamento Inteligente': 'Viana e Moura - Sistema de Reclutamiento Inteligente',
            'Funcionalidades Principais': 'Características Principales',
            'Upload em lote de currículos': 'Carga masiva de currículos',
            'Análise automática com IA': 'Análisis automático con IA',
            'Pontuação inteligente': 'Puntuación inteligente',
            'Filtros avançados': 'Filtros avanzados',
            'Objetivos': 'Objetivos',
            'Reduzir tempo de triagem': 'Reducir tiempo de cribado',
            'Melhorar qualidade da seleção': 'Mejorar calidad de selección',
            'Otimizar processo de recrutamento': 'Optimizar proceso de reclutamiento',
            'Identificar melhores candidatos': 'Identificar mejores candidatos',
            'VAGAS ATIVAS': 'TRABAJOS ACTIVOS',
            'TOTAL CANDIDATOS': 'TOTAL CANDIDATOS',
            'ANÁLISES CONCLUÍDAS': 'ANÁLISIS COMPLETADOS',
            'TAXA DE ANÁLISE': 'TASA DE ANÁLISIS',
            'Gerenciamento de Vagas': 'Gestión de Trabajos',
            'Crie e gerencie vagas de emprego com análise automática de candidatos': 'Cree y gestione puestos de trabajo con análisis automático de candidatos',
            'Nova Vaga': 'Nuevo Trabajo',
            'Todos os Candidatos': 'Todos los Candidatos',
            'Pesquisar por nome do candidato...': 'Buscar por nombre del candidato...',
            'Ver Detalhes': 'Ver Detalles',
            'PENDENTE': 'PENDIENTE',
            'ANALISADO': 'ANALIZADO',
            'INFORMAÇÕES PESSOAIS': 'INFORMACIÓN PERSONAL',
            'Nome Completo': 'Nombre Completo',
            'INFORMAÇÕES DE CONTATO': 'INFORMACIÓN DE CONTACTO',
            'Expandir Todos': 'Expandir Todos',
            'Colapsar Todos': 'Colapsar Todos',
            'Score minim': 'Puntuación Mín',
            'Todos os Stat': 'Todos los Estados',
            'Vagas Recentes': 'Trabajos Recientes',
            'Top Candidatos': 'Mejores Candidatos',
            'Ver Todas as Vagas': 'Ver Todos los Trabajos',
            'ATIVA': 'ACTIVA',
            'candidatos': 'candidatos',
            'analisados': 'analizados',
            'CANDIDATOS': 'CANDIDATOS',
            'ANALISADOS': 'ANALIZADOS',
            'Monitor de Processamento': 'Monitor de Procesamiento',
            'Voltar': 'Volver',
            'Total de Currículos': 'Total de Currículos',
            'Pendentes': 'Pendientes',
            'Processando': 'Procesando',
            'Concluídos': 'Completados',
            'Progresso da Análise': 'Progreso del Análisis',
            'Progresso Geral': 'Progreso General',
            'Iniciar Processamento': 'Iniciar Procesamiento',
            'Resetar Presos': 'Reiniciar Bloqueados',
            'Status em Tempo Real': 'Estado en Tiempo Real',
            'Monitoramento Ativo': 'Monitoreo Activo',
            'Última atualização': 'Última actualización',
            'Lista de Candidatos': 'Lista de Candidatos',
            'CONCLUÍDO': 'COMPLETADO',
            'Descrição da Vaga': 'Descripción del Trabajo',
            'Habilidades y Requisitos': 'Habilidades y Requisitos',
            'Estadísticas': 'Estadísticas',
            'Candidatos': 'Candidatos',
            'Analisados': 'Analizados',
            'Processamento IA': 'Procesamiento IA',
            'Processando': 'Procesando',
            'Concluído': 'Completado',
            'Falhou': 'Falló',
            'Pendiente': 'Pendiente',
            'Editar': 'Editar',
            'Monitor IA': 'Monitor IA',
            'Excluir Vaga': 'Eliminar Trabajo',
            'Criada em': 'Creado el',
            'Formatos aceitos': 'Formatos aceptados',
            'máximo 16MB por arquivo': 'máximo 16MB por archivo',
            'Clique para expandir': 'Haga clic para expandir',
            'Auxiliar de Vendas': 'Asistente de Ventas'
        }
    };
    
    // Aplicar traduções aos elementos visíveis
    const elementsToTranslate = document.querySelectorAll('[data-translate]');
    elementsToTranslate.forEach(element => {
        const key = element.getAttribute('data-translate');
        if (translations[lang] && translations[lang][key]) {
            element.textContent = translations[lang][key];
        }
    });
    
    // Função para traduzir texto recursivamente
    function translateTextRecursively(element) {
        if (element.nodeType === Node.TEXT_NODE) {
            const text = element.textContent.trim();
            if (text && translations[lang][text]) {
                element.textContent = translations[lang][text];
            }
        } else if (element.nodeType === Node.ELEMENT_NODE) {
            // Traduzir placeholders
            if (element.hasAttribute('placeholder')) {
                const placeholder = element.getAttribute('placeholder');
                if (translations[lang][placeholder]) {
                    element.setAttribute('placeholder', translations[lang][placeholder]);
                }
            }
            
            // Traduzir títulos
            if (element.hasAttribute('title')) {
                const title = element.getAttribute('title');
                if (translations[lang][title]) {
                    element.setAttribute('title', translations[lang][title]);
                }
            }
            
            // Traduzir alt text
            if (element.hasAttribute('alt')) {
                const alt = element.getAttribute('alt');
                if (translations[lang][alt]) {
                    element.setAttribute('alt', translations[lang][alt]);
                }
            }
            
            // Recursivamente traduzir filhos
            Array.from(element.childNodes).forEach(child => {
                translateTextRecursively(child);
            });
        }
    }
    
    // Aplicar traduções recursivamente a todo o documento
    translateTextRecursively(document.body);
    
    // Traduzir título da página
    const pageTitle = document.title;
    if (pageTitle && translations[lang][pageTitle]) {
        document.title = translations[lang][pageTitle];
    }
    
    // Traduzir elementos específicos por seletor
    const specificSelectors = {
        'h1, h2, h3, h4, h5, h6': 'textContent',
        'p, span, div, label, button, a': 'textContent',
        'input[placeholder], textarea[placeholder]': 'placeholder',
        'input[title], button[title], a[title]': 'title',
        'img[alt]': 'alt'
    };
    
    Object.keys(specificSelectors).forEach(selector => {
        const elements = document.querySelectorAll(selector);
        const attribute = specificSelectors[selector];
        
        elements.forEach(element => {
            if (attribute === 'textContent') {
                const text = element.textContent.trim();
                if (text && translations[lang][text]) {
                    element.textContent = translations[lang][text];
                }
            } else if (element.hasAttribute(attribute)) {
                const value = element.getAttribute(attribute);
                if (value && translations[lang][value]) {
                    element.setAttribute(attribute, translations[lang][value]);
                }
            }
        });
    });
    
    // Traduzir elementos com classes específicas
    const classSelectors = {
        '.dashboard-title': 'Dashboard de Recrutamento',
        '.job-management-title': 'Gerenciamento de Vagas',
        '.candidates-title': 'Todos os Candidatos',
        '.processing-monitor-title': 'Monitor de Processamento',
        '.main-title': 'Dashboard de Recrutamento',
        '.section-title': 'Seção Principal'
    };
    
    Object.keys(classSelectors).forEach(selector => {
        const element = document.querySelector(selector);
        if (element && translations[lang][classSelectors[selector]]) {
            element.textContent = translations[lang][classSelectors[selector]];
        }
    });
    
    // Forçar atualização de elementos dinâmicos
    setTimeout(() => {
        // Re-aplicar traduções para elementos que podem ter sido carregados dinamicamente
        translateTextRecursively(document.body);
    }, 100);
    
    // Configurar observer para elementos que podem ser adicionados dinamicamente
    if (!window.translationObserver) {
        window.translationObserver = new MutationObserver((mutations) => {
            mutations.forEach((mutation) => {
                if (mutation.type === 'childList') {
                    mutation.addedNodes.forEach((node) => {
                        if (node.nodeType === Node.ELEMENT_NODE) {
                            translateTextRecursively(node);
                        }
                    });
                }
            });
        });
        
        window.translationObserver.observe(document.body, {
            childList: true,
            subtree: true
        });
    }
    
    console.log('✅ Traduções aplicadas para:', lang);
    
    // Aplicar cores variadas aos scores após a tradução
    // applyScoreColors();
}

// Função para aplicar cores variadas aos scores
function applyScoreColors() {
    console.log('🎨 Função de cores desabilitada para manter CSS limpo');
    return; // DESABILITADA - Deixar CSS funcionar naturalmente
    
    /*
    console.log('🎨 Aplicando cores variadas aos scores...');
    
    // Buscar todos os elementos que contêm scores
    const scoreElements = document.querySelectorAll('.badge, [class*="score"], [class*="badge"], span, div, td');
    
    scoreElements.forEach(element => {
        const text = element.textContent.trim();
        const score = parseFloat(text);
        
        if (!isNaN(score) && score > 0 && score <= 10) {
            console.log(`🎯 Aplicando cor para score: ${score}`);
            
            // Remover classes de cor antigas
            element.classList.remove('badge-score', 'high', 'medium', 'low', 'average');
            
            // Aplicar cores baseadas no score
            if (score >= 8.0) {
                element.classList.add('badge-score', 'high');
                element.style.background = '#28a745'; // Verde
                element.style.color = 'white';
                element.style.borderRadius = '4px';
                element.style.padding = '2px 6px';
                element.style.fontWeight = 'bold';
            } else if (score >= 6.0) {
                element.classList.add('badge-score', 'medium');
                element.style.background = '#ffc107'; // Amarelo
                element.style.color = '#212529';
                element.style.borderRadius = '4px';
                element.style.padding = '2px 6px';
                element.style.fontWeight = 'bold';
            } else if (score >= 4.0) {
                element.classList.add('badge-score', 'average');
                element.style.background = '#17a2b8'; // Azul
                element.style.color = 'white';
                element.style.borderRadius = '4px';
                element.style.padding = '2px 6px';
                element.style.fontWeight = 'bold';
            } else {
                element.classList.add('badge-score', 'low');
                element.style.background = '#dc3545'; // Vermelho
                element.style.color = 'white';
                element.style.borderRadius = '4px';
                element.style.padding = '2px 6px';
                element.style.fontWeight = 'bold';
            }
        }
    });
    
    // Aplicar cores aos status badges
    const statusElements = document.querySelectorAll('[class*="status"], [class*="badge"], span, div, td');
    
    statusElements.forEach(element => {
        const text = element.textContent.trim().toUpperCase();
        
        // Remover classes antigas
        element.classList.remove('badge-pending', 'badge-completed', 'badge-processing', 'badge-failed');
        
        // Aplicar cores baseadas no status
        if (text.includes('PENDENTE') || text.includes('PENDING') || text.includes('PENDIENTE')) {
            element.classList.add('badge-pending');
            element.style.background = '#ffc107'; // Amarelo
            element.style.color = '#212529';
            element.style.borderRadius = '4px';
            element.style.padding = '2px 6px';
            element.style.fontWeight = 'bold';
        } else if (text.includes('CONCLUÍDO') || text.includes('COMPLETED') || text.includes('ANALISADO') || text.includes('ANALYZED') || text.includes('COMPLETADO') || text.includes('CONCLUÍDA')) {
            element.classList.add('badge-completed');
            element.style.background = '#28a745'; // Verde
            element.style.color = 'white';
            element.style.borderRadius = '4px';
            element.style.padding = '2px 6px';
            element.style.fontWeight = 'bold';
        } else if (text.includes('PROCESSANDO') || text.includes('PROCESSING') || text.includes('PROCESANDO')) {
            element.classList.add('badge-processing');
            element.style.background = '#17a2b8'; // Azul
            element.style.color = 'white';
            element.style.borderRadius = '4px';
            element.style.padding = '2px 6px';
            element.style.fontWeight = 'bold';
        } else if (text.includes('FALHOU') || text.includes('FAILED') || text.includes('FALLÓ')) {
            element.classList.add('badge-failed');
            element.style.background = '#dc3545'; // Vermelho
            element.style.color = 'white';
            element.style.borderRadius = '4px';
            element.style.padding = '2px 6px';
            element.style.fontWeight = 'bold';
        }
    });
    
    // Aplicar cores aos números de estatísticas
    const statElements = document.querySelectorAll('span, div, td');
    
    statElements.forEach(element => {
        const text = element.textContent.trim();
        const number = parseInt(text);
        
        if (!isNaN(number) && number > 0 && number <= 100) {
            if (number >= 80) {
                element.style.color = '#28a745';
            } else if (number >= 60) {
                element.style.color = '#ffc107';
            } else if (number >= 40) {
                element.style.color = '#17a2b8';
            } else {
                element.style.color = '#dc3545';
            }
        }
    });
    */
    
    console.log('✅ CSS mantido limpo - cores aplicadas naturalmente');
}

function updateCurrentLanguage(lang) {
    const currentLanguageSpan = document.getElementById('currentLanguage');
    if (currentLanguageSpan) {
        currentLanguageSpan.textContent = lang.toUpperCase();
    }
    
    // Update page title based on language
    const titles = {
        'pt': 'Viana e Moura - Recrutamento Inteligente',
        'en': 'Viana e Moura - Intelligent Recruitment',
        'es': 'Viana e Moura - Reclutamiento Inteligente'
    };
    
    if (titles[lang]) {
        document.title = titles[lang];
    }
}

// Export functions for global use
window.VianaeMoura = {
    showNotification,
    showLoadingState,
    hideLoadingState,
    formatDate,
    formatScore,
    validateForm,
    changeLanguage,
    updateThemeIcon,
    updateNavbarTheme
};
