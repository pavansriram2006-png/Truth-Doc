document.addEventListener('DOMContentLoaded', () => {
    const navLinks = document.querySelectorAll('.nav-link');
    const pages = document.querySelectorAll('.page');

    const backendUrl = ((window.BACKEND_URL ?? 'http://127.0.0.1:8000')).replace(/\/$/, '');
    const historyKey = 'truthdoc-history';

    const fileInput = document.getElementById('fileInput');
    const fileName = document.getElementById('fileName');
    const verifyDocBtn = document.getElementById('verifyDocBtn');
    const verifyAnotherDocBtn = document.getElementById('verifyAnotherDocBtn');
    const docResultCard = document.getElementById('doc-result-card');
    const docMeter = document.getElementById('docMeter');
    const docRiskLabel = document.getElementById('docRiskLabel');
    const docReasons = document.getElementById('docReasons');

    const smsInput = document.getElementById('smsInput');
    const verifySmsBtn = document.getElementById('verifySmsBtn');
    const verifyAnotherSmsBtn = document.getElementById('verifyAnotherSmsBtn');
    const smsResultCard = document.getElementById('sms-result-card');
    const smsReasons = document.getElementById('smsReasons');

    const linkInput = document.getElementById('linkInput');
    const verifyLinkBtn = document.getElementById('verifyLinkBtn');
    const verifyAnotherLinkBtn = document.getElementById('verifyAnotherLinkBtn');
    const linkResultCard = document.getElementById('link-result-card');
    const linkReasons = document.getElementById('linkReasons');

    const historyList = document.getElementById('historyList');
    const clearHistoryBtn = document.getElementById('clearHistoryBtn');

    // Navigation
    navLinks.forEach(link => {
        link.addEventListener('click', (e) => {
            e.preventDefault();
            const targetId = link.getAttribute('data-target');

            navLinks.forEach(l => l.classList.remove('active'));
            link.classList.add('active');

            pages.forEach(page => {
                if (page.id === targetId) {
                    page.classList.add('active');
                } else {
                    page.classList.remove('active');
                }
            });
        });
    });

    renderHistory();

    // Document Verification
    verifyDocBtn.addEventListener('click', () => handleDocumentVerification(fileInput.files[0]));
    verifyAnotherDocBtn.addEventListener('click', resetDocumentView);
    fileInput.addEventListener('change', () => {
        fileName.textContent = fileInput.files.length > 0 ? fileInput.files[0].name : 'No file selected';
    });

    // SMS Verification
    verifySmsBtn.addEventListener('click', () => handleSmsVerification(smsInput.value));
    verifyAnotherSmsBtn.addEventListener('click', resetSmsView);

    // Link Verification
    verifyLinkBtn.addEventListener('click', () => handleLinkVerification(linkInput.value));
    verifyAnotherLinkBtn.addEventListener('click', resetLinkView);

    // History
    clearHistoryBtn.addEventListener('click', () => {
        localStorage.removeItem(historyKey);
        renderHistory();
    });

    async function handleDocumentVerification(file) {
        if (!file) {
            renderError(docResultCard, 'Please select a file first.');
            return;
        }
        setLoading(docResultCard, 'Analyzing Document');
        docReasons.innerHTML = '';
        try {
            const data = await verifyDoc(file);
            if (!data.status) {
                throw new Error(data.detail || 'Invalid backend response');
            }
            renderStatusCard(docResultCard, data.status, data.risk_score, data.reason_for_flag);
            renderReasons(docReasons, data.reason_for_flag);
            updateMeter(data.risk_score);
            addHistory('Document', file.name, data.status, data.risk_score, data.reason_for_flag || []);
        } catch (error) {
            renderError(docResultCard, error.message || 'Failed to verify document.');
        }
    }

    async function handleSmsVerification(text) {
        if (!text || !text.trim()) {
            renderError(smsResultCard, 'Please enter SMS text.');
            return;
        }
        setLoading(smsResultCard, 'Analyzing SMS');
        smsReasons.innerHTML = '';
        try {
            const data = await verifySms(text);
            if (!data.status) {
                throw new Error(data.detail || 'Invalid backend response');
            }
            renderStatusCard(smsResultCard, data.status, data.risk_score, data.reason_for_flag);
            renderReasons(smsReasons, data.reason_for_flag);
            addHistory('SMS', truncate(text, 64), data.status, data.risk_score, data.reason_for_flag || []);
        } catch (error) {
            renderError(smsResultCard, error.message || 'Failed to verify SMS.');
        }
    }

    async function handleLinkVerification(url) {
        if (!url || !url.trim()) {
            renderError(linkResultCard, 'Please enter a link.');
            return;
        }
        setLoading(linkResultCard, 'Analyzing Link');
        linkReasons.innerHTML = '';
        try {
            const data = await verifyLink(url.trim());
            if (!data.status) {
                throw new Error(data.detail || 'Invalid backend response');
            }
            renderStatusCard(linkResultCard, data.status, data.risk_score, data.reason_for_flag);
            renderReasons(linkReasons, data.reason_for_flag);
            addHistory('Link', truncate(url.trim(), 64), data.status, data.risk_score, data.reason_for_flag || []);
        } catch (error) {
            renderError(linkResultCard, error.message || 'Failed to verify link.');
        }
    }

    function resetDocumentView() {
        fileInput.value = '';
        fileName.textContent = 'No file selected';
        docReasons.innerHTML = '';
        updateMeter(0);
        docResultCard.className = 'status-card idle';
        docResultCard.innerHTML = `
            <div class="status-icon"><i class="fas fa-shield"></i></div>
            <div class="status-text">Ready</div>
            <div class="status-chip">Upload a file</div>
        `;
    }

    function resetSmsView() {
        smsInput.value = '';
        smsReasons.innerHTML = '';
        smsResultCard.className = 'status-card idle';
        smsResultCard.innerHTML = `
            <div class="status-icon"><i class="fas fa-shield"></i></div>
            <div class="status-text">Ready</div>
            <div class="status-chip">Enter message</div>
        `;
    }

    function resetLinkView() {
        linkInput.value = '';
        linkReasons.innerHTML = '';
        linkResultCard.className = 'status-card idle';
        linkResultCard.innerHTML = `
            <div class="status-icon"><i class="fas fa-shield"></i></div>
            <div class="status-text">Ready</div>
            <div class="status-chip">Enter URL</div>
        `;
    }

    async function verifyDoc(file) {
        const formData = new FormData();
        formData.append('file', file);
        const response = await fetch(`${backendUrl}/verify-document/`, {
            method: 'POST',
            body: formData,
        });
        return parseResponse(response);
    }

    async function verifySms(text) {
        const response = await fetch(`${backendUrl}/verify-sms/`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ raw_text: text }),
        });
        return parseResponse(response);
    }

    async function verifyLink(url) {
        const response = await fetch(`${backendUrl}/verify-link/`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ url }),
        });
        return parseResponse(response);
    }

    async function parseResponse(response) {
        let data = {};
        try {
            data = await response.json();
        } catch (_err) {
            throw new Error(`HTTP ${response.status}`);
        }
        if (!response.ok) {
            throw new Error(data.detail || `HTTP ${response.status}`);
        }
        return data;
    }

    function setLoading(card, label) {
        card.className = 'status-card idle';
        card.innerHTML = `
            <div class="status-icon"><i class="fas fa-spinner fa-spin"></i></div>
            <div class="status-text">Analyzing</div>
            <div class="status-chip">${label}</div>
        `;
    }

    function renderError(card, message) {
        card.className = 'status-card error';
        card.innerHTML = `
            <div class="status-icon"><i class="fas fa-triangle-exclamation"></i></div>
            <div class="status-text">Error</div>
            <div class="status-chip">${escapeHtml(message)}</div>
        `;
    }

    function renderStatusCard(card, status, risk, reasons) {
        const safeStatus = status && status.toLowerCase() === 'genuine' ? 'genuine' : 'suspicious';
        card.className = `status-card ${safeStatus}`;
        const chip = safeStatus === 'genuine' ? 'Verified' : 'Unknown';
        card.innerHTML = `
            <div class="status-icon"><i class="fas fa-shield"></i></div>
            <div class="status-text">${escapeHtml(status)}</div>
            <div class="status-chip">${chip} | Risk ${Number(risk || 0)}%</div>
        `;
    }

    function renderReasons(root, reasons) {
        root.innerHTML = '';
        if (!reasons || reasons.length === 0) {
            const item = document.createElement('li');
            item.textContent = 'No suspicious indicators found.';
            root.appendChild(item);
            return;
        }
        reasons.forEach((reason) => {
            const item = document.createElement('li');
            item.textContent = reason;
            root.appendChild(item);
        });
    }

    function updateMeter(risk) {
        const value = Math.max(0, Math.min(100, Number(risk) || 0));
        docMeter.style.setProperty('--risk', value);
        docRiskLabel.textContent = `${value}%`;
    }

    function addHistory(type, target, status, risk, reasons) {
        const record = {
            type,
            target,
            status,
            risk,
            reasons,
            ts: new Date().toISOString(),
        };
        const current = getHistory();
        current.unshift(record);
        localStorage.setItem(historyKey, JSON.stringify(current.slice(0, 30)));
        renderHistory();
    }

    function getHistory() {
        try {
            const raw = localStorage.getItem(historyKey);
            return raw ? JSON.parse(raw) : [];
        } catch (_err) {
            return [];
        }
    }

    function renderHistory() {
        const items = getHistory();
        historyList.innerHTML = '';
        if (items.length === 0) {
            historyList.innerHTML = '<div class="history-item">No verification history yet.</div>';
            return;
        } else {
            items.forEach((item) => {
                const el = document.createElement('div');
                el.className = 'history-item';
                const when = new Date(item.ts).toLocaleString();
                const reasons = item.reasons && item.reasons.length > 0 ? item.reasons.length : 0;
                el.innerHTML = `
                    <div class="history-top">
                        <strong>${escapeHtml(item.type)} - ${escapeHtml(item.status)}</strong>
                        <span>Risk ${Number(item.risk || 0)}%</span>
                    </div>
                    <div class="history-meta">${escapeHtml(item.target)} | ${when} | ${reasons} flag(s)</div>
                `;
                historyList.appendChild(el);
            });
        }
    }

    function truncate(text, maxLength) {
        return text.length > maxLength ? `${text.slice(0, maxLength - 3)}...` : text;
    }

    function escapeHtml(value) {
        return String(value)
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#39;');
    }
});
