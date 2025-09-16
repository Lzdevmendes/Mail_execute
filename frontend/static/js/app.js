class EmailClassificationApp {
    constructor() {
        this.apiBaseUrl = window.location.origin;
        this.loadingOverlay = document.getElementById('loadingOverlay');
        this.statusBadge = document.getElementById('statusBadge');
        this.resultsSection = document.getElementById('resultsSection');

        // AI Model control
        this.aiModelToggle = document.getElementById('aiModelToggle');
        this.aiModelLabel = document.getElementById('aiModelLabel');
        this.aiModelDescription = document.getElementById('aiModelDescription');
        this.localModel = document.getElementById('localModel');
        this.cloudModel = document.getElementById('cloudModel');
        this.useOpenAI = false; // Default to local (mais rápido)

        // Form elements
        this.textForm = document.getElementById('textClassificationForm');
        this.fileForm = document.getElementById('fileClassificationForm');
        this.emailContent = document.getElementById('emailContent');
        this.emailFile = document.getElementById('emailFile');
        this.fileDropZone = document.getElementById('fileDropZone');
        this.browseFileBtn = document.getElementById('browseFileBtn');
        this.fileInfo = document.getElementById('fileInfo');
        this.removeFileBtn = document.getElementById('removeFile');

        // Toast elements
        this.successToast = new bootstrap.Toast(document.getElementById('successToast'));
        this.errorToast = new bootstrap.Toast(document.getElementById('errorToast'));
        
        // Initialize the application
        this.init();
    }
    
    init() {
        this.setupEventListeners();
        this.setupFileDropZone();
        this.setupCharacterCounter();
        this.setupAIModelToggle();
        this.checkSystemStatus();
        this.loadMetrics();

        // Setup periodic metrics refresh
        setInterval(() => this.loadMetrics(), 30000); // Every 30 seconds

        console.log('Email Classification System initialized successfully');
    }
    
    setupEventListeners() {
        // Form submissions
        this.textForm.addEventListener('submit', (e) => this.handleTextClassification(e));
        this.fileForm.addEventListener('submit', (e) => this.handleFileClassification(e));
        
        // File handling
        this.browseFileBtn.addEventListener('click', () => this.emailFile.click());
        this.emailFile.addEventListener('change', (e) => this.handleFileSelection(e));
        this.removeFileBtn.addEventListener('click', () => this.clearFileSelection());
        
        // Result actions
        document.getElementById('copyResponseBtn')?.addEventListener('click', () => this.copyResponse());
        document.getElementById('editResponseBtn')?.addEventListener('click', () => this.editResponse());
        document.getElementById('newClassificationBtn')?.addEventListener('click', () => this.resetForm());
        document.getElementById('downloadResultBtn')?.addEventListener('click', () => this.downloadResult());
        
        // Example buttons
        document.querySelectorAll('.use-example').forEach(btn => {
            btn.addEventListener('click', (e) => this.useExample(e));
        });

        // AI Model toggle
        this.aiModelToggle.addEventListener('change', () => this.handleAIModelToggle());

        // Make model options clickable
        this.localModel.addEventListener('click', () => this.selectLocalModel());
        this.cloudModel.addEventListener('click', () => this.selectCloudModel());
        
        // Tab change handling
        document.querySelectorAll('#inputTabs button').forEach(tab => {
            tab.addEventListener('shown.bs.tab', (e) => this.onTabChange(e));
        });
    }
    
    setupFileDropZone() {
        ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
            this.fileDropZone.addEventListener(eventName, this.preventDefaults, false);
        });
        
        ['dragenter', 'dragover'].forEach(eventName => {
            this.fileDropZone.addEventListener(eventName, () => {
                this.fileDropZone.classList.add('dragover');
            });
        });
        
        ['dragleave', 'drop'].forEach(eventName => {
            this.fileDropZone.addEventListener(eventName, () => {
                this.fileDropZone.classList.remove('dragover');
            });
        });
        
        this.fileDropZone.addEventListener('drop', (e) => this.handleFileDrop(e));
        this.fileDropZone.addEventListener('click', () => this.emailFile.click());
    }
    
    setupCharacterCounter() {
        const charCount = document.getElementById('charCount');
        const maxLength = 10000;
        
        this.emailContent.addEventListener('input', () => {
            const length = this.emailContent.value.length;
            charCount.textContent = length;
            
            const counter = charCount.parentElement;
            if (length > maxLength) {
                counter.classList.add('over-limit');
            } else {
                counter.classList.remove('over-limit');
            }
        });
    }
    
    preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }
    
    handleFileDrop(e) {
        const dt = e.dataTransfer;
        const files = dt.files;
        
        if (files.length > 0) {
            this.emailFile.files = files;
            this.updateFileInfo(files[0]);
        }
    }
    
    handleFileSelection(e) {
        const file = e.target.files[0];
        if (file) {
            this.updateFileInfo(file);
        }
    }
    
    updateFileInfo(file) {
        document.getElementById('fileName').textContent = file.name;
        document.getElementById('fileSize').textContent = this.formatFileSize(file.size);
        this.fileInfo.style.display = 'block';
    }
    
    clearFileSelection() {
        this.emailFile.value = '';
        this.fileInfo.style.display = 'none';
    }
    
    formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }
    
    async handleTextClassification(e) {
        e.preventDefault();

        const content = this.emailContent.value.trim();

        if (!this.validateTextInput(content)) {
            return;
        }

        // Disable submit button to prevent double submissions
        const submitBtn = this.textForm.querySelector('button[type="submit"]');
        const originalText = submitBtn.innerHTML;
        submitBtn.disabled = true;
        submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Processando...';

        try {
            this.showLoading();

            // Add timeout for better UX
            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), 30000); // 30 second timeout

            const response = await this.apiCall('/classify', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    content: content,
                    source: 'text_input',
                    metadata: {
                        use_openai: this.useOpenAI,
                        preferred_model: this.useOpenAI ? 'openai' : 'local'
                    }
                }),
                signal: controller.signal
            });

            clearTimeout(timeoutId);
            this.displayResults(response);
            this.showToast('success', 'Email classificado com sucesso!');

        } catch (error) {
            console.error('Text classification error:', error);
            const errorMsg = error.name === 'AbortError' ?
                'Tempo limite excedido. Tente novamente.' :
                'Erro ao classificar email: ' + error.message;
            this.showToast('error', errorMsg);
        } finally {
            this.hideLoading();
            submitBtn.disabled = false;
            submitBtn.innerHTML = originalText;
        }
    }
    
    async handleFileClassification(e) {
        e.preventDefault();

        const file = this.emailFile.files[0];

        if (!this.validateFileInput(file)) {
            return;
        }

        // Disable submit button and show progress
        const submitBtn = this.fileForm.querySelector('button[type="submit"]');
        const originalText = submitBtn.innerHTML;
        submitBtn.disabled = true;
        submitBtn.innerHTML = '<i class="fas fa-upload fa-spin me-2"></i>Processando arquivo...';

        try {
            this.showLoading();

            const formData = new FormData();
            formData.append('file', file);
            formData.append('metadata', JSON.stringify({
                use_openai: this.useOpenAI,
                preferred_model: this.useOpenAI ? 'openai' : 'local'
            }));

            // Add timeout for file processing
            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), 60000); // 60 seconds for files

            const response = await this.apiCall('/classify/file', {
                method: 'POST',
                body: formData,
                signal: controller.signal
            });

            clearTimeout(timeoutId);
            this.displayResults(response);
            this.showToast('success', 'Arquivo processado e classificado com sucesso!');

        } catch (error) {
            console.error('File classification error:', error);
            const errorMsg = error.name === 'AbortError' ?
                'Tempo limite para processamento do arquivo excedido.' :
                'Erro ao processar arquivo: ' + error.message;
            this.showToast('error', errorMsg);
        } finally {
            this.hideLoading();
            submitBtn.disabled = false;
            submitBtn.innerHTML = originalText;
        }
    }
    
    validateTextInput(content) {
        if (!content) {
            this.showToast('error', 'Por favor, insira o conteúdo do email.');
            this.emailContent.focus();
            return false;
        }
        
        if (content.length < 10) {
            this.showToast('error', 'O conteúdo deve ter pelo menos 10 caracteres.');
            this.emailContent.focus();
            return false;
        }
        
        if (content.length > 10000) {
            this.showToast('error', 'O conteúdo não pode exceder 10.000 caracteres.');
            this.emailContent.focus();
            return false;
        }
        
        return true;
    }
    
    validateFileInput(file) {
        if (!file) {
            this.showToast('error', 'Por favor, selecione um arquivo.');
            return false;
        }
        
        const allowedTypes = ['.txt', '.pdf'];
        const fileExtension = '.' + file.name.split('.').pop().toLowerCase();
        
        if (!allowedTypes.includes(fileExtension)) {
            this.showToast('error', 'Tipo de arquivo não suportado. Use .txt ou .pdf');
            return false;
        }
        
        const maxSize = 10 * 1024 * 1024; // 10MB
        if (file.size > maxSize) {
            this.showToast('error', 'Arquivo muito grande. Máximo 10MB.');
            return false;
        }
        
        return true;
    }

    displayResults(data) {
        // Add smooth animation to results
        this.resultsSection.style.opacity = '0';
        this.resultsSection.style.display = 'block';

        // Update category with animation
        const categoryText = document.getElementById('categoryText');
        const categoryIcon = document.getElementById('categoryIcon');

        if (data.category === 'produtivo') {
            categoryText.textContent = 'PRODUTIVO';
            categoryText.className = 'mb-0 fw-bold text-success';
            categoryIcon.className = 'fas fa-check-circle fa-2x text-success';
        } else {
            categoryText.textContent = 'IMPRODUTIVO';
            categoryText.className = 'mb-0 fw-bold text-warning';
            categoryIcon.className = 'fas fa-info-circle fa-2x text-warning';
        }

        // Update confidence with animated progress bar
        const confidence = Math.round(data.confidence * 100);
        document.getElementById('confidenceText').textContent = confidence + '%';

        const confidenceBar = document.getElementById('confidenceBar');

        // Reset progress bar for animation
        confidenceBar.style.width = '0%';
        confidenceBar.setAttribute('aria-valuenow', 0);

        // Set color based on confidence
        if (confidence >= 80) {
            confidenceBar.className = 'progress-bar bg-success';
        } else if (confidence >= 60) {
            confidenceBar.className = 'progress-bar bg-warning';
        } else {
            confidenceBar.className = 'progress-bar bg-danger';
        }

        // Animate progress bar
        setTimeout(() => {
            confidenceBar.style.width = confidence + '%';
            confidenceBar.setAttribute('aria-valuenow', confidence);
        }, 300);

        // Update response
        document.getElementById('suggestedResponseText').textContent = data.suggested_response;

        // Update processing info
        const processingTime = data.processing_time ? (data.processing_time * 1000) : 0;
        document.getElementById('processingTime').textContent =
            Math.round(processingTime) + ' ms';

        document.getElementById('timestamp').textContent =
            new Date(data.timestamp).toLocaleString('pt-BR');

        // Show classification method if available
        if (data.model_used) {
            const methodBadge = document.getElementById('classificationMethod');
            if (methodBadge) {
                const methodName = data.model_used === 'openai' ? 'OpenAI GPT' :
                                 data.model_used === 'ai' ? 'AI Local' : 'Regras';
                methodBadge.textContent = methodName;
                methodBadge.className = `badge ${data.model_used === 'openai' ? 'bg-primary' : 'bg-secondary'}`;
            }
        }

        // Store result for download
        this.lastResult = data;

        // Fade in results with smooth animation
        setTimeout(() => {
            this.resultsSection.style.transition = 'opacity 0.5s ease-in-out';
            this.resultsSection.style.opacity = '1';
            this.resultsSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }, 100);

        // Load updated metrics
        setTimeout(() => this.loadMetrics(), 1000);
    }
    
    async checkSystemStatus() {
        try {
            this.updateStatusBadge('loading', 'Verificando status...', true);
            
            const status = await this.apiCall('/health');
            
            if (status.status === 'healthy') {
                const message = status.ai_model_loaded ? 
                    'Sistema operacional' : 
                    'Sistema operacional (modo básico)';
                this.updateStatusBadge('healthy', message, false);
            } else {
                this.updateStatusBadge('error', 'Sistema indisponível', false);
            }
            
        } catch (error) {
            console.error('Status check error:', error);
            this.updateStatusBadge('error', 'Erro ao verificar status', false);
        }
    }
    
    updateStatusBadge(status, message, spinning = false) {
        this.statusBadge.className = `badge bg-secondary status-${status}`;
        
        const icon = spinning ? 
            '<i class="fas fa-circle-notch fa-spin me-1"></i>' :
            status === 'healthy' ? '<i class="fas fa-check-circle me-1"></i>' :
            status === 'error' ? '<i class="fas fa-exclamation-circle me-1"></i>' :
            '<i class="fas fa-info-circle me-1"></i>';
        
        this.statusBadge.innerHTML = icon + message;
    }
   
    async loadMetrics() {
        try {
            const metrics = await this.apiCall('/metrics');
            
            document.getElementById('totalProcessed').textContent = metrics.total_processed || 0;
            document.getElementById('productiveCount').textContent = metrics.productive_count || 0;
            document.getElementById('unproductiveCount').textContent = metrics.unproductive_count || 0;
            
            const avgTime = metrics.average_processing_time ? 
                (metrics.average_processing_time * 1000).toFixed(0) + ' ms' : '-';
            document.getElementById('averageTime').textContent = avgTime;
            
        } catch (error) {
            console.error('Metrics loading error:', error);
        }
    }
    
    /**
     * Use example email content
     */
    useExample(e) {
        const content = e.target.getAttribute('data-content').replace(/&#10;/g, '\n');
        
        // Switch to text input tab
        const textTab = document.getElementById('text-tab');
        const textTabInstance = new bootstrap.Tab(textTab);
        textTabInstance.show();
        
        // Set content and focus
        this.emailContent.value = content;
        this.emailContent.dispatchEvent(new Event('input')); // Trigger character counter
        this.emailContent.focus();
        
        // Scroll to form
        this.emailContent.scrollIntoView({ behavior: 'smooth', block: 'center' });
        
        this.showToast('success', 'Exemplo carregado com sucesso!');
    }
    
    /**
     * Copy response to clipboard
     */
    async copyResponse() {
        const responseText = document.getElementById('suggestedResponseText').textContent;
        
        try {
            await navigator.clipboard.writeText(responseText);
            this.showToast('success', 'Resposta copiada para a área de transferência!');
        } catch (error) {
            console.error('Copy error:', error);
            this.showToast('error', 'Erro ao copiar resposta.');
        }
    }
  
    editResponse() {
        const responseElement = document.getElementById('suggestedResponseText');
        const currentText = responseElement.textContent;
        
        const newText = prompt('Editar resposta:', currentText);
        
        if (newText !== null && newText.trim()) {
            responseElement.textContent = newText.trim();
            this.showToast('success', 'Resposta editada com sucesso!');
        }
    }
    
    resetForm() {
        this.textForm.reset();
        this.fileForm.reset();
        this.clearFileSelection();
        this.resultsSection.style.display = 'none';
        
        // Switch to text tab
        const textTab = document.getElementById('text-tab');
        const textTabInstance = new bootstrap.Tab(textTab);
        textTabInstance.show();
        
        // Scroll to top
        window.scrollTo({ top: 0, behavior: 'smooth' });
        
        this.emailContent.focus();
    }
    
    downloadResult() {
        if (!this.lastResult) {
            this.showToast('error', 'Nenhum resultado para baixar.');
            return;
        }
        
        const dataStr = JSON.stringify(this.lastResult, null, 2);
        const dataBlob = new Blob([dataStr], { type: 'application/json' });
        const url = URL.createObjectURL(dataBlob);
        
        const link = document.createElement('a');
        link.href = url;
        link.download = `email-classification-${Date.now()}.json`;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        
        URL.revokeObjectURL(url);
        
        this.showToast('success', 'Resultado baixado com sucesso!');
    }
    
    onTabChange(e) {
        if (e.target.id === 'text-tab') {
            this.emailContent.focus();
        }
    }
    
    showLoading() {
        this.loadingOverlay.classList.add('show');
    }
    
    hideLoading() {
        this.loadingOverlay.classList.remove('show');
    }
    
    showToast(type, message) {
        if (type === 'success') {
            document.getElementById('successToastMessage').textContent = message;
            this.successToast.show();
        } else {
            document.getElementById('errorToastMessage').textContent = message;
            this.errorToast.show();
        }
    }

    setupAIModelToggle() {
        // Initialize AI model toggle state
        this.updateAIModelDisplay();
    }

    handleAIModelToggle() {
        this.useOpenAI = this.aiModelToggle.checked;
        this.updateAIModelDisplay();

        // Add visual feedback during toggle
        this.aiModelToggle.disabled = true;
        setTimeout(() => {
            this.aiModelToggle.disabled = false;
        }, 500);

        // Show toast notification
        const modelName = this.useOpenAI ? 'OpenAI GPT' : 'Transformers (Local)';
        this.showToast('success', `Modelo alterado para: ${modelName}`);

        console.log(`AI Model switched to: ${modelName}`);
    }

    selectLocalModel() {
        if (!this.useOpenAI) return; // Already selected

        this.useOpenAI = false;
        this.updateAIModelDisplay();
        this.showToast('success', 'Modelo alterado para: Transformers (Local)');
        console.log('AI Model switched to: Transformers (Local)');
    }

    selectCloudModel() {
        if (this.useOpenAI) return; // Already selected

        this.useOpenAI = true;
        this.updateAIModelDisplay();
        this.showToast('success', 'Modelo alterado para: OpenAI GPT');
        console.log('AI Model switched to: OpenAI GPT');
    }

    updateAIModelDisplay() {
        if (this.useOpenAI) {
            // OpenAI mode (toggle ON)
            this.aiModelLabel.textContent = 'Processamento na nuvem com GPT-3.5/GPT-4 (mais preciso)';
            this.aiModelToggle.checked = true;
            this.localModel.classList.remove('active');
            this.cloudModel.classList.add('active');
        } else {
            // Local mode (toggle OFF)
            this.aiModelLabel.textContent = 'Processamento local com RoBERTa + NLTK (mais rápido)';
            this.aiModelToggle.checked = false;
            this.localModel.classList.add('active');
            this.cloudModel.classList.remove('active');
        }
    }

    async apiCall(endpoint, options = {}) {
        const url = this.apiBaseUrl + endpoint;
        
        try {
            const response = await fetch(url, {
                ...options,
                headers: {
                    ...options.headers,
                }
            });
            
            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                throw new Error(errorData.message || `HTTP ${response.status}: ${response.statusText}`);
            }
            
            return await response.json();
            
        } catch (error) {
            if (error.name === 'TypeError' && error.message.includes('fetch')) {
                throw new Error('Erro de conexão. Verifique sua internet.');
            }
            throw error;
        }
    }
}

// Initialize application when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.emailApp = new EmailClassificationApp();
});

// Handle online/offline status
window.addEventListener('online', () => {
    window.emailApp?.showToast('success', 'Conexão restaurada!');
});

window.addEventListener('offline', () => {
    window.emailApp?.showToast('error', 'Conexão perdida. Verifique sua internet.');
});