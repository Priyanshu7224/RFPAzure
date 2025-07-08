// AI-Powered RFP BOM Generator - Main JavaScript

// Global variables
let stockMasterUploaded = false;
let currentBOMData = [];
let extractedRFPItems = [];
let currentRFPInputMode = 'manual';

// Initialize the application
document.addEventListener('DOMContentLoaded', function() {
    initializeEventListeners();
    checkHealthStatus();
    loadSessionInfo();
});

// Initialize event listeners
function initializeEventListeners() {
    // Stock master file upload
    const fileInput = document.getElementById('stockFileInput');
    const uploadArea = document.getElementById('uploadArea');

    fileInput.addEventListener('change', handleFileUpload);

    // Browse button click handler
    const stockBrowseBtn = document.getElementById('stockBrowseBtn');
    if (stockBrowseBtn) {
        stockBrowseBtn.addEventListener('click', (e) => {
            e.stopPropagation(); // Prevent event bubbling
            fileInput.click();
        });
    }

    // Drag and drop for stock master
    uploadArea.addEventListener('dragover', handleDragOver);
    uploadArea.addEventListener('dragleave', handleDragLeave);
    uploadArea.addEventListener('drop', handleFileDrop);

    // Click handler for upload area (but not for buttons inside)
    uploadArea.addEventListener('click', (e) => {
        // Only trigger if clicking the area itself, not buttons inside
        if (e.target === uploadArea || e.target.closest('.upload-content') && !e.target.closest('button')) {
            fileInput.click();
        }
    });

    // RFP file upload
    const rfpFileInput = document.getElementById('rfpFileInput');
    const rfpUploadArea = document.getElementById('rfpUploadArea');

    rfpFileInput.addEventListener('change', handleRFPFileUpload);

    // RFP Browse button click handler
    const rfpBrowseBtn = document.getElementById('rfpBrowseBtn');
    if (rfpBrowseBtn) {
        rfpBrowseBtn.addEventListener('click', (e) => {
            e.stopPropagation(); // Prevent event bubbling
            rfpFileInput.click();
        });
    }

    // Drag and drop for RFP files
    rfpUploadArea.addEventListener('dragover', handleRFPDragOver);
    rfpUploadArea.addEventListener('dragleave', handleRFPDragLeave);
    rfpUploadArea.addEventListener('drop', handleRFPFileDrop);

    // Click handler for RFP upload area (but not for buttons inside)
    rfpUploadArea.addEventListener('click', (e) => {
        // Only trigger if clicking the area itself, not buttons inside
        if (e.target === rfpUploadArea || e.target.closest('.upload-content') && !e.target.closest('button')) {
            rfpFileInput.click();
        }
    });

    // RFP processing
    document.getElementById('rfpInput').addEventListener('input', validateRFPInput);
}

// Check application health status
async function checkHealthStatus() {
    try {
        const response = await fetch('/health');
        const data = await response.json();
        
        if (data.stock_master_loaded) {
            stockMasterUploaded = true;
            showStep2();
            showToast('Stock master file already loaded', 'success');
        }
    } catch (error) {
        console.error('Health check failed:', error);
    }
}

// File upload handlers
function handleFileUpload(event) {
    const file = event.target.files[0];
    if (file) {
        // Add a small delay to ensure the file is properly selected
        setTimeout(() => {
            uploadStockMaster(file);
        }, 100);
    }
}

function handleDragOver(event) {
    event.preventDefault();
    event.currentTarget.classList.add('dragover');
}

function handleDragLeave(event) {
    event.currentTarget.classList.remove('dragover');
}

function handleFileDrop(event) {
    event.preventDefault();
    event.currentTarget.classList.remove('dragover');
    
    const files = event.dataTransfer.files;
    if (files.length > 0) {
        uploadStockMaster(files[0]);
    }
}

// Upload stock master file
async function uploadStockMaster(file) {
    // Validate file type
    const allowedTypes = ['.xlsx', '.xls', '.csv'];
    const fileExtension = '.' + file.name.split('.').pop().toLowerCase();
    
    if (!allowedTypes.includes(fileExtension)) {
        showToast('Invalid file type. Please upload Excel or CSV file.', 'error');
        return;
    }
    
    // Show loading
    const uploadStatus = document.getElementById('uploadStatus');
    uploadStatus.style.display = 'block';
    uploadStatus.innerHTML = `
        <div class="upload-progress">
            <div class="spinner"></div>
            <p>Uploading and processing ${file.name}...</p>
        </div>
    `;
    
    try {
        const formData = new FormData();
        formData.append('file', file);
        
        const response = await fetch('/upload-stock-master', {
            method: 'POST',
            body: formData
        });
        
        const data = await response.json();
        
        if (data.success) {
            stockMasterUploaded = true;
            uploadStatus.innerHTML = `
                <div class="upload-success">
                    <i class="fas fa-check-circle"></i>
                    <p>Successfully uploaded ${data.total_records} stock records</p>
                    <p class="upload-details">File: ${data.original_rows} rows processed</p>
                    <p class="upload-details">Columns found: ${data.columns_found ? data.columns_found.join(', ') : 'N/A'}</p>
                </div>
            `;
            showToast(`Stock master uploaded: ${data.total_records} records`, 'success');
            showStep2();

            // Re-validate RFP input now that stock is uploaded
            validateRFPInput();

            // Debug log
            console.log('Stock master upload result:', data);
        } else {
            throw new Error(data.error || 'Upload failed');
        }
    } catch (error) {
        uploadStatus.innerHTML = `
            <div class="upload-error">
                <i class="fas fa-exclamation-circle"></i>
                <p>Upload failed: ${error.message}</p>
            </div>
        `;
        showToast(`Upload failed: ${error.message}`, 'error');
    }
}

// Show step 2 (RFP input)
function showStep2() {
    document.getElementById('step2').style.display = 'block';
    document.getElementById('step2').scrollIntoView({ behavior: 'smooth' });
}

// Show step 3 (Results)
function showStep3() {
    document.getElementById('step3').style.display = 'block';
    document.getElementById('step3').scrollIntoView({ behavior: 'smooth' });
}

// Validate RFP input
function validateRFPInput() {
    if (currentRFPInputMode === 'manual') {
        const input = document.getElementById('rfpInput');
        const processBtn = document.getElementById('processBtn');

        const lines = input.value.trim().split('\n').filter(line => line.trim());
        processBtn.disabled = lines.length === 0 || !stockMasterUploaded;

        if (!stockMasterUploaded) {
            processBtn.title = 'Please upload stock master file first';
        } else if (lines.length === 0) {
            processBtn.title = 'Please enter RFP line items';
        } else {
            processBtn.title = `Process ${lines.length} RFP items`;
        }
    } else {
        // File mode - check if we have extracted items
        const processBtn = document.getElementById('processExtractedBtn');
        if (processBtn) {
            processBtn.disabled = extractedRFPItems.length === 0 || !stockMasterUploaded;

            if (!stockMasterUploaded) {
                processBtn.title = 'Please upload stock master file first';
            } else if (extractedRFPItems.length === 0) {
                processBtn.title = 'Please upload and process an RFP file first';
            } else {
                processBtn.title = `Process ${extractedRFPItems.length} extracted RFP items`;
            }
        }
    }
}

// Clear RFP input
function clearRFPInput() {
    document.getElementById('rfpInput').value = '';
    validateRFPInput();
}

// Process RFP items
async function processRFP() {
    const input = document.getElementById('rfpInput');
    const lines = input.value.trim().split('\n').filter(line => line.trim());
    
    if (lines.length === 0) {
        showToast('Please enter RFP line items', 'warning');
        return;
    }
    
    if (!stockMasterUploaded) {
        showToast('Please upload stock master file first', 'warning');
        return;
    }
    
    // Show loading overlay
    showLoading(true);
    
    try {
        const response = await fetch('/process-rfp', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                rfp_items: lines
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            currentBOMData = data.results;
            displayResults(data.results, data.summary);
            showStep3();
            showToast(`Processed ${lines.length} RFP items`, 'success');
        } else {
            throw new Error(data.error || 'Processing failed');
        }
    } catch (error) {
        showToast(`Processing failed: ${error.message}`, 'error');
    } finally {
        showLoading(false);
    }
}

// Display results
function displayResults(results, summary) {
    // Update summary cards
    updateSummaryCards(summary);
    
    // Update results table
    updateResultsTable(results);
}

// Update summary cards
function updateSummaryCards(summary) {
    const summaryCards = document.getElementById('summaryCards');
    summaryCards.innerHTML = `
        <div class="summary-card total">
            <div class="card-number">${summary.total_items}</div>
            <div class="card-label">Total Items</div>
        </div>
        <div class="summary-card matched">
            <div class="card-number">${summary.matched}</div>
            <div class="card-label">Matched</div>
        </div>
        <div class="summary-card unmatched">
            <div class="card-number">${summary.unmatched}</div>
            <div class="card-label">Unmatched</div>
        </div>
        <div class="summary-card unavailable">
            <div class="card-number">${summary.unavailable}</div>
            <div class="card-label">Unavailable</div>
        </div>
    `;
}

// Update results table
function updateResultsTable(results) {
    const tableBody = document.getElementById('resultsTableBody');
    tableBody.innerHTML = '';
    
    results.forEach(result => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>${result.line_number}</td>
            <td class="rfp-item" title="${result.original_rfp_item}">${truncateText(result.original_rfp_item, 50)}</td>
            <td><span class="status-badge status-${result.status}">${result.status}</span></td>
            <td>${result.matched_product_code || '-'}</td>
            <td class="description" title="${result.matched_description}">${truncateText(result.matched_description, 60)}</td>
            <td>${result.match_score}%</td>
            <td>${result.on_hand_quantity || 0}</td>
            <td class="reason" title="${result.match_reason}">${truncateText(result.match_reason, 80)}</td>
        `;
        tableBody.appendChild(row);
    });
}

// Export BOM to Excel
async function exportBOM() {
    if (!currentBOMData || currentBOMData.length === 0) {
        showToast('No BOM data to export', 'warning');
        return;
    }
    
    try {
        const response = await fetch('/export-bom', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                bom_data: currentBOMData
            })
        });
        
        if (response.ok) {
            // Create download link
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = 'generated_bom.xlsx';
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);
            
            showToast('BOM exported successfully', 'success');
        } else {
            const data = await response.json();
            throw new Error(data.error || 'Export failed');
        }
    } catch (error) {
        showToast(`Export failed: ${error.message}`, 'error');
    }
}

// Start over
function startOver() {
    // Reset form
    document.getElementById('rfpInput').value = '';
    document.getElementById('step2').style.display = 'none';
    document.getElementById('step3').style.display = 'none';

    // Reset upload status
    const uploadStatus = document.getElementById('uploadStatus');
    uploadStatus.style.display = 'none';

    // Reset RFP upload status
    const rfpUploadStatus = document.getElementById('rfpUploadStatus');
    if (rfpUploadStatus) {
        rfpUploadStatus.style.display = 'none';
    }

    // Reset RFP preview
    const rfpPreview = document.getElementById('rfpPreview');
    if (rfpPreview) {
        rfpPreview.style.display = 'none';
    }

    // Clear file inputs
    document.getElementById('stockFileInput').value = '';
    const rfpFileInput = document.getElementById('rfpFileInput');
    if (rfpFileInput) {
        rfpFileInput.value = '';
    }

    // Reset variables
    stockMasterUploaded = false;
    currentBOMData = [];
    extractedRFPItems = [];

    // Reset to manual input mode
    switchRFPInputMode('manual');

    // Scroll to top
    window.scrollTo({ top: 0, behavior: 'smooth' });

    showToast('Reset complete. Please upload stock master file to begin.', 'info');
}

// RFP Input Mode Switching
function switchRFPInputMode(mode) {
    currentRFPInputMode = mode;

    // Update tab appearance
    document.getElementById('manualTab').classList.toggle('active', mode === 'manual');
    document.getElementById('fileTab').classList.toggle('active', mode === 'file');

    // Show/hide content
    document.getElementById('manualInput').style.display = mode === 'manual' ? 'block' : 'none';
    document.getElementById('fileInput').style.display = mode === 'file' ? 'block' : 'none';

    // Reset validation
    validateRFPInput();
}

// RFP File Upload Handlers
function handleRFPFileUpload(event) {
    const file = event.target.files[0];
    if (file) {
        // Add a small delay to ensure the file is properly selected
        setTimeout(() => {
            uploadRFPFile(file);
        }, 100);
    }
}

function handleRFPDragOver(event) {
    event.preventDefault();
    event.currentTarget.classList.add('dragover');
}

function handleRFPDragLeave(event) {
    event.currentTarget.classList.remove('dragover');
}

function handleRFPFileDrop(event) {
    event.preventDefault();
    event.currentTarget.classList.remove('dragover');

    const files = event.dataTransfer.files;
    if (files.length > 0) {
        uploadRFPFile(files[0]);
    }
}

// Upload RFP file
async function uploadRFPFile(file) {
    // Validate file type
    const allowedTypes = ['.xlsx', '.xls', '.csv', '.pdf', '.docx', '.txt'];
    const fileExtension = '.' + file.name.split('.').pop().toLowerCase();

    if (!allowedTypes.includes(fileExtension)) {
        showToast('Invalid file type. Please upload Excel, CSV, PDF, Word, or Text file.', 'error');
        return;
    }

    // Show loading
    const uploadStatus = document.getElementById('rfpUploadStatus');
    uploadStatus.style.display = 'block';
    uploadStatus.innerHTML = `
        <div class="upload-progress">
            <div class="spinner"></div>
            <p>Processing ${file.name}...</p>
            <p class="upload-subtext">Extracting RFP items from file</p>
        </div>
    `;

    try {
        const formData = new FormData();
        formData.append('file', file);

        const response = await fetch('/upload-rfp-file', {
            method: 'POST',
            body: formData
        });

        const data = await response.json();

        if (data.success) {
            extractedRFPItems = data.rfp_items;

            uploadStatus.innerHTML = `
                <div class="upload-success">
                    <i class="fas fa-check-circle"></i>
                    <p>Successfully extracted ${data.total_items} RFP items from ${data.original_filename}</p>
                </div>
            `;

            // Show preview
            showRFPPreview(data.rfp_items);
            showToast(`RFP file processed: ${data.total_items} items extracted`, 'success');
        } else {
            throw new Error(data.error || 'Upload failed');
        }
    } catch (error) {
        uploadStatus.innerHTML = `
            <div class="upload-error">
                <i class="fas fa-exclamation-circle"></i>
                <p>Upload failed: ${error.message}</p>
            </div>
        `;
        showToast(`RFP file processing failed: ${error.message}`, 'error');
    }
}

// Show RFP preview
function showRFPPreview(items) {
    const preview = document.getElementById('rfpPreview');
    const previewItems = document.getElementById('previewItems');

    previewItems.innerHTML = '';

    items.forEach((item, index) => {
        const itemDiv = document.createElement('div');
        itemDiv.className = 'preview-item';
        itemDiv.innerHTML = `<strong>${index + 1}.</strong> ${item}`;
        previewItems.appendChild(itemDiv);
    });

    preview.style.display = 'block';

    // Update process button
    const processBtn = document.getElementById('processExtractedBtn');
    processBtn.disabled = !stockMasterUploaded;
    processBtn.title = stockMasterUploaded ?
        `Process ${items.length} extracted RFP items` :
        'Please upload stock master file first';
}

// Edit extracted items
function editExtractedItems() {
    // Switch to manual mode and populate with extracted items
    switchRFPInputMode('manual');
    document.getElementById('rfpInput').value = extractedRFPItems.join('\n');
    validateRFPInput();
    showToast('Items copied to manual editor. You can now edit them before processing.', 'info');
}

// Process extracted RFP items
async function processExtractedRFP() {
    if (!extractedRFPItems || extractedRFPItems.length === 0) {
        showToast('No extracted RFP items to process', 'warning');
        return;
    }

    if (!stockMasterUploaded) {
        showToast('Please upload stock master file first', 'warning');
        return;
    }

    // Show loading overlay
    showLoading(true);

    try {
        const response = await fetch('/process-rfp', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                rfp_items: extractedRFPItems
            })
        });

        const data = await response.json();

        if (data.success) {
            currentBOMData = data.results;
            displayResults(data.results, data.summary);
            showStep3();
            showToast(`Processed ${extractedRFPItems.length} RFP items`, 'success');
        } else {
            throw new Error(data.error || 'Processing failed');
        }
    } catch (error) {
        showToast(`Processing failed: ${error.message}`, 'error');
    } finally {
        showLoading(false);
    }
}

// Utility functions
function truncateText(text, maxLength) {
    if (!text) return '';
    return text.length > maxLength ? text.substring(0, maxLength) + '...' : text;
}

function showLoading(show) {
    const overlay = document.getElementById('loadingOverlay');
    overlay.style.display = show ? 'flex' : 'none';
}

function showToast(message, type = 'info') {
    const container = document.getElementById('toastContainer');
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.innerHTML = `
        <div class="toast-content">
            <strong>${type.charAt(0).toUpperCase() + type.slice(1)}</strong>
            <p>${message}</p>
        </div>
    `;

    container.appendChild(toast);

    // Auto remove after 5 seconds
    setTimeout(() => {
        if (toast.parentNode) {
            toast.parentNode.removeChild(toast);
        }
    }, 5000);
}

// Chat functionality
function toggleChat() {
    const chatInterface = document.getElementById('chatInterface');
    const isVisible = chatInterface.style.display !== 'none';
    chatInterface.style.display = isVisible ? 'none' : 'block';

    // If opening chat, scroll to bottom and focus input
    if (!isVisible) {
        setTimeout(() => {
            const messagesContainer = document.getElementById('chatMessages');
            const chatInput = document.getElementById('chatInput');

            // Scroll to bottom
            messagesContainer.scrollTo({
                top: messagesContainer.scrollHeight,
                behavior: 'smooth'
            });

            // Focus input on desktop (not mobile to avoid keyboard issues)
            if (window.innerWidth > 768) {
                chatInput.focus();
            }
        }, 100);
    }
}

function handleChatKeyPress(event) {
    if (event.key === 'Enter') {
        sendChatMessage();
    }
}

function sendChatMessage() {
    const input = document.getElementById('chatInput');
    const message = input.value.trim();

    if (!message) return;

    // Add user message
    addChatMessage(message, 'user');
    input.value = '';

    // Show typing indicator
    showTypingIndicator();

    // Simulate AI response with more realistic delay
    setTimeout(() => {
        hideTypingIndicator();
        const response = generateChatResponse(message);
        addChatMessage(response, 'bot');
    }, 1500);
}

function showTypingIndicator() {
    const messagesContainer = document.getElementById('chatMessages');
    const typingDiv = document.createElement('div');
    typingDiv.className = 'chat-message bot-message typing-indicator';
    typingDiv.id = 'typingIndicator';
    typingDiv.innerHTML = `
        <div class="message-content">
            <div class="typing-dots">
                <span></span>
                <span></span>
                <span></span>
            </div>
        </div>
    `;

    messagesContainer.appendChild(typingDiv);

    // Scroll to bottom
    setTimeout(() => {
        messagesContainer.scrollTo({
            top: messagesContainer.scrollHeight,
            behavior: 'smooth'
        });
    }, 100);
}

function hideTypingIndicator() {
    const typingIndicator = document.getElementById('typingIndicator');
    if (typingIndicator) {
        typingIndicator.remove();
    }
}

function addChatMessage(message, sender) {
    const messagesContainer = document.getElementById('chatMessages');
    const messageDiv = document.createElement('div');
    messageDiv.className = `chat-message ${sender}-message`;
    messageDiv.innerHTML = `<div class="message-content">${message}</div>`;

    messagesContainer.appendChild(messageDiv);

    // Ensure smooth scrolling to bottom
    setTimeout(() => {
        messagesContainer.scrollTo({
            top: messagesContainer.scrollHeight,
            behavior: 'smooth'
        });
    }, 100);
}

function generateChatResponse(userMessage) {
    const responses = {
        'help': 'I can help you with RFP processing. Upload your stock master file, enter RFP items, and I\'ll generate a BOM for you.',
        'upload': 'To upload a stock master file, drag and drop it in the upload area or click to browse. Supported formats: Excel (.xlsx, .xls) and CSV.',
        'process': 'Enter your RFP line items in the text area, one per line. I\'ll use AI to match them against your stock master.',
        'export': 'Once processing is complete, you can export the BOM to Excel format using the Export button.',
        'default': 'I\'m here to help with RFP processing. You can ask about uploading files, processing items, or exporting results.'
    };

    const lowerMessage = userMessage.toLowerCase();

    if (lowerMessage.includes('help')) return responses.help;
    if (lowerMessage.includes('upload')) return responses.upload;
    if (lowerMessage.includes('process')) return responses.process;
    if (lowerMessage.includes('export')) return responses.export;

    return responses.default;
}

// Session Management Functions
async function loadSessionInfo() {
    try {
        const response = await fetch('/session-info');
        const data = await response.json();

        const sessionDetails = document.getElementById('sessionDetails');
        if (sessionDetails) {
            const storageType = data.storage.storage_type;
            const sessionId = data.session.session_id ? data.session.session_id.substring(0, 8) + '...' : 'N/A';
            sessionDetails.textContent = `Session: ${sessionId} | Storage: ${storageType}`;
        }

        // Show session info in development
        if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
            const sessionInfo = document.getElementById('sessionInfo');
            if (sessionInfo) {
                sessionInfo.style.display = 'block';
            }
        }

        console.log('Session Info:', data);
    } catch (error) {
        console.error('Failed to load session info:', error);
    }
}

function toggleSessionInfo() {
    fetch('/session-info')
        .then(response => response.json())
        .then(data => {
            const details = JSON.stringify(data, null, 2);
            alert(`Session Information:\n\n${details}`);
        })
        .catch(error => {
            console.error('Failed to get session info:', error);
        });
}

async function clearSession() {
    if (confirm('Are you sure you want to clear your session? This will remove all uploaded data.')) {
        try {
            const response = await fetch('/clear-session', { method: 'POST' });
            const data = await response.json();

            if (data.success) {
                showToast('Session cleared successfully. Page will reload.', 'success');
                setTimeout(() => {
                    window.location.reload();
                }, 2000);
            } else {
                showToast('Failed to clear session', 'error');
            }
        } catch (error) {
            showToast('Error clearing session', 'error');
        }
    }
}
