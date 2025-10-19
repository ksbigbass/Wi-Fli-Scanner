let autoRefreshInterval = null;
let isAutoRefreshEnabled = true;
let isLoading = false;

async function fetchWifiData() {
    if (isLoading) return;

    isLoading = true;
    const refreshBtn = document.getElementById('refreshBtn');
    refreshBtn.disabled = true;
    refreshBtn.textContent = '⏳ Scanning...';

    try {
        const response = await fetch('/api/wifi-data');
        const data = await response.json();

        if (!data.success) {
            showError(data.error || 'Unknown error occurred');
            updateStatus('error', 'Scan failed');
            return;
        }

        displayNetworks(data.wifi_networks);
        updateStatus('success', `Found ${data.count} networks`);

        const now = new Date();
        document.getElementById('lastUpdate').textContent =
            `Last updated: ${now.toLocaleTimeString()}`;

    } catch (error) {
        console.error('Error fetching Wi-Fi data:', error);
        showError('Failed to connect to server. Please check if the server is running.');
        updateStatus('error', 'Connection failed');
    } finally {
        isLoading = false;
        refreshBtn.disabled = false;
        refreshBtn.textContent = '🔄 Refresh Now';
    }
}

function displayNetworks(networks) {
    const resultDiv = document.getElementById('result');

    if (!networks || networks.length === 0) {
        resultDiv.innerHTML = '<div class="loading">No networks found</div>';
        return;
    }

    const html = networks.map(network => `
        <div class="network-card">
            <div class="network-header">
                <div class="network-ssid">
                    ${network.security !== 'Open' ? '🔒' : '🔓'} 
                    ${escapeHtml(network.ssid)}
                </div>
                <div class="signal-badge signal-${network.quality.toLowerCase()}">
                    ${network.signal}% ${network.quality}
                </div>
            </div>
            <div class="signal-bar">
                <div class="signal-fill signal-${network.quality.toLowerCase()}" 
                     style="width: ${network.signal}%; background: ${getSignalColor(network.signal)}">
                </div>
            </div>
            <div class="network-details">
                <div class="detail-item">
                    <span class="detail-label">Security</span>
                    <span>${escapeHtml(network.security)}</span>
                </div>
                ${network.channel ? `
                <div class="detail-item">
                    <span class="detail-label">Channel</span>
                    <span>${escapeHtml(network.channel)}</span>
                </div>` : ''}
                ${network.frequency ? `
                <div class="detail-item">
                    <span class="detail-label">Frequency</span>
                    <span>${escapeHtml(network.frequency)}</span>
                </div>` : ''}
                <button onclick="runWifite('${escapeHtml(network.bssid || network.ssid)}')" 
                        style="margin-top:10px; background:#dc3545;">
                    🚀 Run Wifite
                </button>
            </div>
        </div>
    `).join('');

    resultDiv.innerHTML = html;
}

async function runWifite(target) {
    if (!confirm(`Start Wifite on ${target}?`)) return;
    try {
        const response = await fetch('/api/run-wifite', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ bssid: target })
        });
        const data = await response.json();
        alert(data.success ? data.message : `Error: ${data.error}`);
    } catch (error) {
        alert('Failed to contact backend: ' + error.message);
    }
}

function showError(message) {
    const resultDiv = document.getElementById('result');
    resultDiv.innerHTML = `
        <div class="error-message">
            <strong>⚠️ Error:</strong> ${escapeHtml(message)}
        </div>
    `;
}

function updateStatus(type, message) {
    const statusDot = document.getElementById('statusDot');
    const statusText = document.getElementById('statusText');

    statusDot.className = 'status-dot' + (type === 'error' ? ' error' : '');
    statusText.textContent = message;
}

function toggleAutoRefresh() {
    isAutoRefreshEnabled = !isAutoRefreshEnabled;
    const btn = document.getElementById('toggleAutoBtn');

    if (isAutoRefreshEnabled) {
        btn.textContent = '⏸️ Pause Auto-Refresh';
        startAutoRefresh();
    } else {
        btn.textContent = '▶️ Resume Auto-Refresh';
        stopAutoRefresh();
    }
}

function startAutoRefresh() {
    if (autoRefreshInterval) clearInterval(autoRefreshInterval);
    autoRefreshInterval = setInterval(fetchWifiData, 10000);
}

function stopAutoRefresh() {
    if (autoRefreshInterval) {
        clearInterval(autoRefreshInterval);
        autoRefreshInterval = null;
    }
}

function getSignalColor(signal) {
    if (signal >= 70) return '#28a745';
    if (signal >= 50) return '#17a2b8';
    if (signal >= 30) return '#ffc107';
    return '#dc3545';
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Initialize
updateStatus('success', 'Ready');
fetchWifiData();
startAutoRefresh();
document.getElementById('refreshBtn').addEventListener('click', fetchWifiData);
document.getElementById('toggleAutoBtn').addEventListener('click', toggleAutoRefresh);