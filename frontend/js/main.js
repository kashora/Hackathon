let reportData = null; // Placeholder for report data
const chatContainer = document.getElementById('chat-container');
const chatInput = document.getElementById('chat-input');
const sendBtn = document.getElementById('send-btn');
const reportBtn = document.getElementById('report-btn');
let canGenerateReport = false;
let welcomeShown = true;
let chat = []; // Store chat history for the API

// Adjust textarea height based on content
chatInput.addEventListener('input', function() {
    this.style.height = 'auto';
    this.style.height = (this.scrollHeight) + 'px';
    if (this.value.trim() === '') {
        sendBtn.disabled = true;
    } else {
        sendBtn.disabled = false;
    }
});

// Handle sending a message
async function sendMessage() {
    const prompt = chatInput.value.trim();
    if (!prompt) return;

    chatInput.value = '';
    chatInput.style.height = 'auto';
    sendBtn.disabled = true;

    // Clear welcome message if shown
    if (welcomeShown) {
        chatContainer.innerHTML = '';
        welcomeShown = false;
        chatContainer.style.justifyContent = 'flex-start';
        chatContainer.style.alignItems = 'stretch';
    }

    // Add user message
    const userMsg = document.createElement('div');
    userMsg.className = 'message user visible';
    userMsg.innerHTML = `<div class="message-content">${prompt}</div>`;
    chatContainer.appendChild(userMsg);
    chatContainer.scrollTop = chatContainer.scrollHeight;

    // Add to chat history
    chat.push(['user', prompt]);

    // Add thinking indicator
    const thinkingEl = document.createElement('div');
    thinkingEl.className = 'multi-agent visible';
    thinkingEl.innerHTML = `
        <div class="avatar-container technical">MA</div>
        <div class="multi-agent-content">
            <div class="title">Multi-Agent Thinking</div>
            <div class="agent"><i class="fas fa-cog fa-spin"></i>Agent 1 analyzing relevant procedures...</div>
            <div class="agent"><i class="fas fa-cog fa-spin"></i>Agent 2 summarizing outcomes...</div>
            <div class="agent"><i class="fas fa-cog fa-spin"></i>Agent 3 drafting the final report...</div>
        </div>
    `;
    chatContainer.appendChild(thinkingEl);
    chatContainer.scrollTop = chatContainer.scrollHeight;

    try {
        // Call the backend API
        const response = await fetch('http://127.0.0.1:5000/neurocorp', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                messages: chat
            })
        });
        
        const data = await response.json();
        console.log(data);
        reportData = data.final_report;
        console.log(reportData);
        
        // Remove thinking indicator
        chatContainer.removeChild(thinkingEl);
        
        // Technical analysis response
        if (data.technical_analysis) {
            const technicalMsg = document.createElement('div');
            technicalMsg.className = 'message assistant visible';
            technicalMsg.innerHTML = `
                <div class="avatar-container technical">TA</div>
                <div class="message-content">
                    <strong>Technical Analysis:</strong><br>
                    ${formatMarkdown(data.technical_analysis)}
                </div>
            `;
            chatContainer.appendChild(technicalMsg);
            chat.push(['technical_analyst', data.technical_analysis]);
        }
        
        // Business analysis response
        if (data.business_analysis) {
            const businessMsg = document.createElement('div');
            businessMsg.className = 'message assistant visible';
            businessMsg.innerHTML = `
                <div class="avatar-container business">BA</div>
                <div class="message-content">
                    <strong>Business Analysis:</strong><br>
                    ${formatMarkdown(data.business_analysis)}
                </div>
            `;
            chatContainer.appendChild(businessMsg);
            chat.push(['business_analyst', data.business_analysis]);
        }
        
        // Enable report generation if available
        canGenerateReport = true;
        reportBtn.disabled = false;
        
    } catch (err) {
        console.error(err);
        
        // Remove thinking indicator and show error
        chatContainer.removeChild(thinkingEl);
        
        const errorMsg = document.createElement('div');
        errorMsg.className = 'message assistant visible';
        errorMsg.innerHTML = `
            <div class="avatar-container">PA</div>
            <div class="message-content">❌ Error communicating with backend. Please try again.</div>
        `;
        chatContainer.appendChild(errorMsg);
        chat.push(['system', '[Error communicating with backend]']);
    }

    sendBtn.disabled = false;
    chatContainer.scrollTop = chatContainer.scrollHeight;
}

// Function to handle report generation
async function generateReport() {
    if (!canGenerateReport || !reportData) return;
    
    reportBtn.disabled = true;
    
    try {
        // Use the reportData to generate PDF
        createPDF(reportData);
        
        const reportMsg = document.createElement('div');
        reportMsg.className = 'message assistant visible';
        reportMsg.innerHTML = `
            <div class="avatar-container technical">FR</div>
            
            <div class="message-content">
                <strong>Final Report:</strong><br>
                
            </div>
            <div class="message-content">📄 PDF report has been generated and downloaded</div>
        `;
        chatContainer.appendChild(reportMsg);
        chat.push(['system', 'Report generated: procedure_report.pdf']);
    } catch (err) {
        console.error(err);
        const errorMsg = document.createElement('div');
        errorMsg.className = 'message assistant visible';
        errorMsg.innerHTML = `
            <div class="avatar-container technical">PA</div>
            <div class="message-content">❌ Error generating report. Please try again.</div>
        `;
        chatContainer.appendChild(errorMsg);
        chat.push(['system', '[Error generating report]']);
    }
    
    setTimeout(() => {
        reportBtn.disabled = !canGenerateReport;
    }, 2000);
    
    chatContainer.scrollTop = chatContainer.scrollHeight;
}

// Function to format markdown-style text
function formatMarkdown(text) {
    // Convert **text** to <strong>text</strong>
    return text.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
}

// Function to create PDF from report data
function createPDF(reportData) {
    // Make sure jsPDF is loaded
    if (typeof window.jspdf === 'undefined') {
        console.error('jsPDF library not loaded');
        return;
    }
    
    const { jsPDF } = window.jspdf;
    
    // Create a new PDF document
    const doc = new jsPDF({
        orientation: 'portrait',
        unit: 'pt',
        format: 'a4'
    });
    
    // Convert markdown to HTML - ensure reportData is treated as string
    const converter = new showdown.Converter({
        tables: true,
        tasklists: true,
        strikethrough: true
    });
    
    // Ensure reportData is a string
    const reportContent = typeof reportData === 'string' 
        ? reportData 
        : JSON.stringify(reportData, null, 2);
    
    // Convert markdown to HTML
    const htmlContent = converter.makeHtml(reportContent);
    
    // Set up the PDF content preview area
    const pdfPreview = document.getElementById('pdf-preview');
    const pdfContent = document.getElementById('pdf-content');
    
    // Add header to the content
    pdfContent.innerHTML = `
        <div style="margin-bottom: 20px; border-bottom: 2px solid #1a73e8; padding-bottom: 10px;">
            <h1 style="color: #1a73e8; font-size: 24px; margin: 0;">Procedure Report</h1>
            <p style="color: #5f6368; margin: 5px 0 0 0;">${new Date().toLocaleDateString()}</p>
        </div>
        ${htmlContent}
    `;
    
    // Split content into pages
    const pageWidth = doc.internal.pageSize.getWidth();
    const pageHeight = doc.internal.pageSize.getHeight();
    const margin = 40; // margin in pts
    
    // Calculate text width and height
    const textWidth = pageWidth - (margin * 2);
    
    // Apply styles directly to the document 
    // Title
    doc.setFontSize(24);
    doc.setTextColor(26, 115, 232); // #1a73e8
    doc.text('Procedure Report', margin, margin + 10);
    
    // Date
    doc.setFontSize(12);
    doc.setTextColor(95, 99, 104); // #5f6368
    doc.text(new Date().toLocaleDateString(), margin, margin + 30);
    
    // Line under header
    doc.setDrawColor(26, 115, 232); // #1a73e8
    doc.setLineWidth(1);
    doc.line(margin, margin + 40, pageWidth - margin, margin + 40);
    
    // Convert report content to lines
    doc.setFontSize(12);
    doc.setTextColor(32, 33, 36); // #202124
    
    // Use splitTextToSize to handle line breaks
    const lines = doc.splitTextToSize(
        // Strip HTML tags from markdown converted content
        htmlContent.replace(/<[^>]*>?/gm, ''),
        textWidth
    );
    
    let y = margin + 60; // Starting y position after header
    
    // Add lines to document with pagination
    for (let i = 0; i < lines.length; i++) {
        // If we've reached the bottom of the page, add a new page
        if (y > pageHeight - margin) {
            doc.addPage();
            y = margin; // Reset Y position
        }
        
        // Add the line to the document
        doc.text(lines[i], margin, y);
        y += 14; // Line height
    }
    
    // Save the PDF
    doc.save('procedure_report.pdf');
}

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    // Event listeners
    sendBtn.addEventListener('click', sendMessage);
    
    chatInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            if (!sendBtn.disabled && chatInput.value.trim()) {
                sendMessage();
            }
        }
    });

    reportBtn.addEventListener('click', generateReport);
});