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

// Language Selector System
function initializeLanguageSelector() {
    const languageDropdown = document.getElementById('languageDropdown');
    const currentLanguageSpan = document.getElementById('currentLanguage');
    const languageOptions = document.querySelectorAll('.language-option');
    
    if (!languageDropdown) return;
    
    // Load saved language from localStorage
    const savedLanguage = localStorage.getItem('language') || 'pt';
    updateCurrentLanguage(savedLanguage);
    
    languageOptions.forEach(option => {
        option.addEventListener('click', function(e) {
            e.preventDefault();
            const lang = this.getAttribute('data-lang');
            changeLanguage(lang);
        });
    });
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
    
    // Here you would typically reload the page with new language
    // or make AJAX calls to get translated content
    // For now, we'll just update the display
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
    updateThemeIcon
};
