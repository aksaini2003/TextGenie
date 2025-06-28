// Main JavaScript for InsightGenie Application
class InsightGenie {
    constructor() {
        this.uploadedFiles = [];
        this.languages = [];
        this.init();
    }

    init() {
        this.initializeEventListeners();
        this.loadLanguages();
        this.initializeDropZone();
        this.initializeWordCounter();
        this.enableSmoothScrolling();
    }

    // Initialize all event listeners
    initializeEventListeners() {
        // File upload
        document.getElementById('uploadArea').addEventListener('click', () => {
            document.getElementById('fileInput').click();
        });

        document.getElementById('fileInput').addEventListener('change', (e) => {
            this.handleFileUpload(e.target.files);
        });

        // Q&A functionality
        document.getElementById('askBtn').addEventListener('click', () => {
            this.askQuestion();
        });

        document.getElementById('questionInput').addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.askQuestion();
            }
        });

        // Document summarization
        document.getElementById('summarizeDocsBtn').addEventListener('click', () => {
            this.summarizeDocuments();
        });

        // Text summarization
        document.getElementById('summarizeTextBtn').addEventListener('click', () => {
            this.summarizeText();
        });

        // Translation
        document.getElementById('translateBtn').addEventListener('click', () => {
            this.translateText();
        });

        document.getElementById('swapLanguagesBtn').addEventListener('click', () => {
            this.swapLanguages();
        });

        // Clear history
        document.getElementById('clearHistoryBtn').addEventListener('click', () => {
            this.clearHistory();
        });

        // Text input monitoring
        document.getElementById('summarizeTextInput').addEventListener('input', () => {
            this.updateWordCount();
        });
    }

    // Initialize drag and drop functionality
    initializeDropZone() {
        const uploadArea = document.getElementById('uploadArea');

        uploadArea.addEventListener('dragover', (e) => {
            e.preventDefault();
            uploadArea.classList.add('dragover');
        });

        uploadArea.addEventListener('dragleave', (e) => {
            e.preventDefault();
            uploadArea.classList.remove('dragover');
        });

        uploadArea.addEventListener('drop', (e) => {
            e.preventDefault();
            uploadArea.classList.remove('dragover');
            this.handleFileUpload(e.dataTransfer.files);
        });
    }

    // Handle file upload with enhanced error handling
    async handleFileUpload(files) {
        if (!files || files.length === 0) {
            this.showToast('No files selected', 'error');
            return;
        }

        const formData = new FormData();
        const allowedTypes = ['text/plain', 'application/pdf', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'];
        const maxSize = 200 * 1024 * 1024; // 200MB

        // Validate files before upload
        for (let file of files) {
            if (!allowedTypes.includes(file.type) && !file.name.match(/\.(txt|pdf|docx)$/i)) {
                this.showToast(`File "${file.name}" has unsupported format. Only TXT, PDF, and DOCX files are allowed.`, 'error');
                continue;
            }

            if (file.size > maxSize) {
                this.showToast(`File "${file.name}" is too large. Maximum size is 200MB.`, 'error');
                continue;
            }

            if (file.size === 0) {
                this.showToast(`File "${file.name}" is empty.`, 'error');
                continue;
            }

            formData.append('files', file);
        }

        if (!formData.has('files')) {
            this.showToast('No valid files to upload', 'error');
            return;
        }

        this.showUploadProgress();

        try {
            const response = await fetch('/upload', {
                method: 'POST',
                body: formData
            });

            const result = await response.json();

            if (response.ok) {
                this.displayUploadResults(result);
                this.enableChatInterface(result.success_count > 0);
                this.showToast(result.message, result.success_count > 0 ? 'success' : 'warning');
            } else {
                throw new Error(result.error || 'Upload failed');
            }
        } catch (error) {
            console.error('Upload error:', error);
            this.showToast(`Upload failed: ${error.message}`, 'error');
        } finally {
            this.hideUploadProgress();
        }
    }

    // Display upload progress
    showUploadProgress() {
        const progressContainer = document.getElementById('uploadProgress');
        const progressBar = progressContainer.querySelector('.progress-bar');
        
        progressContainer.style.display = 'block';
        progressBar.style.width = '0%';
        
        // Simulate progress
        let progress = 0;
        const interval = setInterval(() => {
            progress += Math.random() * 15;
            if (progress > 90) progress = 90;
            progressBar.style.width = progress + '%';
        }, 200);

        // Store interval for cleanup
        this.uploadInterval = interval;
    }

    // Hide upload progress
    hideUploadProgress() {
        if (this.uploadInterval) {
            clearInterval(this.uploadInterval);
        }
        
        const progressContainer = document.getElementById('uploadProgress');
        const progressBar = progressContainer.querySelector('.progress-bar');
        
        progressBar.style.width = '100%';
        
        setTimeout(() => {
            progressContainer.style.display = 'none';
            progressBar.style.width = '0%';
        }, 500);
    }

    // Display upload results with detailed feedback (append new files, don't clear existing ones)
    displayUploadResults(result) {
        const resultsContainer = document.getElementById('uploadResults');
        
        // Don't clear existing results, just add new ones
        if (result.files && result.files.length > 0) {
            result.files.forEach(file => {
                // Check if file already exists to avoid duplicates
                const existingFiles = Array.from(resultsContainer.querySelectorAll('.filename'));
                const fileExists = existingFiles.some(el => el.textContent === file.filename);
                
                if (!fileExists) {
                    const resultItem = document.createElement('div');
                    resultItem.className = `upload-result-item ${file.status === 'error' ? 'error' : ''}`;
                    
                    // Format file size if available
                    const sizeText = file.size ? this.formatFileSize(file.size) : '';
                    const statusText = file.status === 'processed' ? 'Processed' : 'Failed';
                    
                    resultItem.innerHTML = `
                        <div class="file-info">
                            <div class="filename" title="${file.filename}">${file.filename}</div>
                            <div class="file-details">
                                ${sizeText ? `Size: ${sizeText} • ` : ''}Status: ${statusText}
                                ${file.message ? `<br>${file.message}` : ''}
                            </div>
                        </div>
                        <div class="status">
                            <div class="status-icon ${file.status === 'processed' ? 'success' : 'error'}" 
                                 title="${file.status === 'processed' ? 'Successfully processed' : 'Processing failed'}">
                                <i class="fas ${file.status === 'processed' ? 'fa-check' : 'fa-times'}"></i>
                            </div>
                        </div>
                    `;
                    
                    resultsContainer.appendChild(resultItem);
                }
            });
        }
    }

    // Format file size for display
    formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }

    // Enable or disable chat interface based on uploaded files
    enableChatInterface(hasFiles) {
        const questionInput = document.getElementById('questionInput');
        const askBtn = document.getElementById('askBtn');
        const summarizeBtn = document.getElementById('summarizeDocsBtn');

        questionInput.disabled = !hasFiles;
        askBtn.disabled = !hasFiles;
        summarizeBtn.disabled = !hasFiles;

        if (hasFiles) {
            questionInput.placeholder = 'Ask a question about your documents...';
        } else {
            questionInput.placeholder = 'Upload documents first to ask questions...';
        }
    }

    // Ask question functionality with improved error handling
    async askQuestion() {
        const questionInput = document.getElementById('questionInput');
        const question = questionInput.value.trim();

        if (!question) {
            this.showToast('Please enter a question', 'warning');
            return;
        }

        this.showLoading();
        this.addMessageToChat(question, 'question');
        questionInput.value = '';

        try {
            const response = await fetch('/ask', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ question: question })
            });

            const result = await response.json();

            if (response.ok) {
                this.addMessageToChat(result.answer, 'answer');
            } else {
                throw new Error(result.error || 'Failed to get answer');
            }
        } catch (error) {
            console.error('Question error:', error);
            this.addMessageToChat(`Error: ${error.message}`, 'answer');
            this.showToast(`Error: ${error.message}`, 'error');
        } finally {
            this.hideLoading();
        }
    }

    // Add message to chat with animation
    addMessageToChat(message, type) {
        const chatHistory = document.getElementById('chatHistory');
        const messageDiv = document.createElement('div');
        messageDiv.className = `chat-message ${type}`;

        messageDiv.innerHTML = `
            <div class="message-bubble ${type}">
                ${this.formatMessage(message)}
            </div>
        `;

        chatHistory.appendChild(messageDiv);
        chatHistory.scrollTop = chatHistory.scrollHeight;
    }

    // Format message content with proper styling and structure
    formatMessage(message) {
        if (!message) return '';
        
        // Clean up the message
        let formatted = message.trim();
        
        // First, handle headers with special formatting (before bullet points)
        formatted = formatted.replace(/^([A-Z][A-Za-z\s]+):$/gm, '<div class="message-header">$1</div>');
        
        // Format bold text (surrounded by **text**)
        formatted = formatted.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');
        
        // Format italic text (surrounded by *text*)
        formatted = formatted.replace(/(?<!\*)\*([^*]+)\*(?!\*)/g, '<em>$1</em>');
        
        // Format code snippets (surrounded by `code`)
        formatted = formatted.replace(/`([^`]+)`/g, '<code class="inline-code">$1</code>');
        
        // Split into lines and process each line
        const lines = formatted.split('\n');
        const processedLines = [];
        
        for (let i = 0; i < lines.length; i++) {
            const line = lines[i].trim();
            
            if (!line) {
                processedLines.push('<br>');
                continue;
            }
            
            // Check if line is a bullet point
            if (/^[\*\-\•]\s+/.test(line)) {
                const content = line.replace(/^[\*\-\•]\s+/, '');
                processedLines.push(`<div class="list-item">${content}</div>`);
            }
            // Check if line is a numbered list
            else if (/^\d+\.\s+/.test(line)) {
                const content = line.replace(/^\d+\.\s+/, '');
                const number = line.match(/^(\d+\.)/)[1];
                processedLines.push(`<div class="numbered-item">${number} ${content}</div>`);
            }
            // Check if line is already a formatted header
            else if (line.includes('<div class="message-header">')) {
                processedLines.push(line);
            }
            // Regular paragraph content
            else {
                processedLines.push(`<p class="message-paragraph">${line}</p>`);
            }
        }
        
        return processedLines.join('');
    }

    // Summarize uploaded documents
    async summarizeDocuments() {
        this.showLoading();

        try {
            const response = await fetch('/summarize', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                }
            });

            const result = await response.json();

            if (response.ok) {
                this.addMessageToChat(`📄 Summary of ${result.document_count} document(s):\n\n${result.summary}`, 'answer');
                this.showToast('Documents summarized successfully', 'success');
            } else {
                throw new Error(result.error || 'Failed to summarize documents');
            }
        } catch (error) {
            console.error('Summarization error:', error);
            this.showToast(`Error: ${error.message}`, 'error');
        } finally {
            this.hideLoading();
        }
    }

    // Summarize text input
    async summarizeText() {
        const textInput = document.getElementById('summarizeTextInput');
        const summarySize = document.getElementById('summarySize').value;
        const text = textInput.value.trim();

        if (!text) {
            this.showToast('Please enter text to summarize', 'warning');
            return;
        }

        const wordCount = text.split(/\s+/).length;
        if (wordCount > 8000) {
            this.showToast('Text exceeds 8,000 word limit', 'error');
            return;
        }

        this.showLoading();

        try {
            const response = await fetch('/summarize_text', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    text: text,
                    summary_size: summarySize
                })
            });

            const result = await response.json();

            if (response.ok) {
                this.displaySummaryResult(result.summary);
                this.showToast('Text summarized successfully', 'success');
            } else {
                throw new Error(result.error || 'Failed to summarize text');
            }
        } catch (error) {
            console.error('Text summarization error:', error);
            this.showToast(`Error: ${error.message}`, 'error');
        } finally {
            this.hideLoading();
        }
    }

    // Display summary result
    displaySummaryResult(summary) {
        const summaryResult = document.getElementById('summaryResult');
        const summaryContent = summaryResult.querySelector('.summary-content');
        
        summaryContent.innerHTML = this.formatMessage(summary);
        summaryResult.style.display = 'block';
        
        // Scroll to result
        summaryResult.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }

    // Translate text functionality
    async translateText() {
        const translateInput = document.getElementById('translateInput');
        const sourceLanguage = document.getElementById('sourceLanguage').value;
        const targetLanguage = document.getElementById('targetLanguage').value;
        const text = translateInput.value.trim();

        if (!text) {
            this.showToast('Please enter text to translate', 'warning');
            return;
        }

        if (sourceLanguage === targetLanguage) {
            this.showToast('Source and target languages cannot be the same', 'warning');
            return;
        }

        this.showLoading();

        try {
            const response = await fetch('/translate', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    text: text,
                    source_language: sourceLanguage,
                    target_language: targetLanguage
                })
            });

            const result = await response.json();

            if (response.ok) {
                document.getElementById('translationOutput').value = result.translated_text;
                this.showToast('Text translated successfully', 'success');
            } else {
                throw new Error(result.error || 'Failed to translate text');
            }
        } catch (error) {
            console.error('Translation error:', error);
            this.showToast(`Error: ${error.message}`, 'error');
        } finally {
            this.hideLoading();
        }
    }

    // Swap source and target languages
    swapLanguages() {
        const sourceSelect = document.getElementById('sourceLanguage');
        const targetSelect = document.getElementById('targetLanguage');
        const translateInput = document.getElementById('translateInput');
        const translationOutput = document.getElementById('translationOutput');

        // Swap language selections
        const tempLanguage = sourceSelect.value;
        sourceSelect.value = targetSelect.value;
        targetSelect.value = tempLanguage;

        // Swap text content
        const tempText = translateInput.value;
        translateInput.value = translationOutput.value;
        translationOutput.value = tempText;

        this.showToast('Languages swapped', 'info');
    }

    // Load supported languages
    async loadLanguages() {
        try {
            const response = await fetch('/get_languages');
            const result = await response.json();

            if (response.ok) {
                this.languages = result.languages;
                this.populateLanguageSelects();
            } else {
                console.error('Failed to load languages');
            }
        } catch (error) {
            console.error('Error loading languages:', error);
        }
    }

    // Populate language select elements
    populateLanguageSelects() {
        const sourceSelect = document.getElementById('sourceLanguage');
        const targetSelect = document.getElementById('targetLanguage');

        // Clear existing options
        sourceSelect.innerHTML = '';
        targetSelect.innerHTML = '';

        // Add language options
        this.languages.forEach(language => {
            const sourceOption = new Option(language, language);
            const targetOption = new Option(language, language);
            
            sourceSelect.add(sourceOption);
            targetSelect.add(targetOption);
        });

        // Set default selections
        sourceSelect.value = 'English';
        targetSelect.value = 'Spanish';
    }

    // Initialize word counter
    initializeWordCounter() {
        this.updateWordCount();
    }

    // Update word count display
    updateWordCount() {
        const textInput = document.getElementById('summarizeTextInput');
        const wordCountDisplay = document.getElementById('wordCount');
        const text = textInput.value.trim();
        const wordCount = text ? text.split(/\s+/).length : 0;

        wordCountDisplay.textContent = `${wordCount.toLocaleString()} words`;

        // Update styling based on word count
        wordCountDisplay.className = '';
        if (wordCount > 7000) {
            wordCountDisplay.classList.add('danger');
        } else if (wordCount > 5000) {
            wordCountDisplay.classList.add('warning');
        }
    }

    // Clear history functionality
    async clearHistory() {
        if (!confirm('Are you sure you want to clear all history and uploaded documents?')) {
            return;
        }

        this.showLoading();

        try {
            const response = await fetch('/clear_history', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                }
            });

            const result = await response.json();

            if (response.ok) {
                // Clear UI
                document.getElementById('chatHistory').innerHTML = '';
                document.getElementById('uploadResults').innerHTML = '';
                document.getElementById('summaryResult').style.display = 'none';
                document.getElementById('questionInput').value = '';
                document.getElementById('summarizeTextInput').value = '';
                document.getElementById('translateInput').value = '';
                document.getElementById('translationOutput').value = '';
                
                this.enableChatInterface(false);
                this.updateWordCount();
                this.showToast('History cleared successfully', 'success');
            } else {
                throw new Error(result.error || 'Failed to clear history');
            }
        } catch (error) {
            console.error('Clear history error:', error);
            this.showToast(`Error: ${error.message}`, 'error');
        } finally {
            this.hideLoading();
        }
    }

    // Clear uploaded files only
    async clearFiles() {
        if (!confirm('Are you sure you want to clear all uploaded files?')) {
            return;
        }

        try {
            const response = await fetch('/clear_history', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                }
            });

            const result = await response.json();

            if (response.ok) {
                // Clear upload results display
                document.getElementById('uploadResults').innerHTML = '';
                this.enableChatInterface(false);
                this.showToast('Files cleared successfully', 'success');
            } else {
                throw new Error(result.error || 'Failed to clear files');
            }
        } catch (error) {
            console.error('Clear files error:', error);
            this.showToast(`Error: ${error.message}`, 'error');
        }
    }

    // Show loading overlay (only in working area)
    showLoading() {
        const loadingOverlay = document.getElementById('loadingOverlay');
        const activeTab = document.querySelector('.tab-pane.active');
        
        if (activeTab) {
            // Position loading overlay relative to active tab
            loadingOverlay.style.position = 'absolute';
            loadingOverlay.style.top = '0';
            loadingOverlay.style.left = '0';
            loadingOverlay.style.width = '100%';
            loadingOverlay.style.height = '100%';
            loadingOverlay.style.zIndex = '9999';
            
            // Make the active tab container relative
            activeTab.style.position = 'relative';
            activeTab.appendChild(loadingOverlay);
        }
        
        loadingOverlay.style.display = 'flex';
    }

    // Hide loading overlay
    hideLoading() {
        const loadingOverlay = document.getElementById('loadingOverlay');
        loadingOverlay.style.display = 'none';
        
        // Move loading overlay back to body
        document.body.appendChild(loadingOverlay);
    }

    // Show toast notification
    showToast(message, type = 'info') {
        const toast = document.getElementById('toast');
        const toastBody = toast.querySelector('.toast-body');
        
        toastBody.textContent = message;
        
        // Update toast styling based on type
        toast.className = `toast ${type}`;
        
        const bsToast = new bootstrap.Toast(toast);
        bsToast.show();
    }

    // Enable smooth scrolling for navigation
    enableSmoothScrolling() {
        document.querySelectorAll('a[href^="#"]').forEach(anchor => {
            anchor.addEventListener('click', function (e) {
                e.preventDefault();
                const target = document.querySelector(this.getAttribute('href'));
                if (target) {
                    target.scrollIntoView({
                        behavior: 'smooth',
                        block: 'start'
                    });
                }
            });
        });
    }
}

// Initialize the application when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new InsightGenie();
});

// Handle online/offline status
window.addEventListener('online', () => {
    const app = new InsightGenie();
    app.showToast('Connection restored', 'success');
});

window.addEventListener('offline', () => {
    const app = new InsightGenie();
    app.showToast('Connection lost. Some features may not work.', 'warning');
});
