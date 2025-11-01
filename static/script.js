class SEOTrafficBoosterUI {
    constructor() {
        this.socket = io();
        this.isRunning = false;
        this.initializeEventListeners();
        this.initializeSocketListeners();
    }

    initializeEventListeners() {
        const startBtn = document.getElementById('startBtn');
        const stopBtn = document.getElementById('stopBtn');

        startBtn.addEventListener('click', () => this.startCycles());
        stopBtn.addEventListener('click', () => this.stopCycles());
    }

    initializeSocketListeners() {
        this.socket.on('connect', () => {
            this.addStatusLog('Connected to SEO Traffic Booster server');
        });

        this.socket.on('status_update', (data) => {
            this.updateCycleInfo(data.cycle, data.total_cycles);
            this.addStatusLog(data.message);
        });

        this.socket.on('start_success', (data) => {
            this.isRunning = true;
            this.updateButtonStates();
            this.addStatusLog(data.message);
        });

        this.socket.on('stop_success', (data) => {
            this.isRunning = false;
            this.updateButtonStates();
            this.addStatusLog(data.message);
        });

        this.socket.on('error', (data) => {
            this.addStatusLog(`ERROR: ${data.message}`);
            alert(data.message);
        });
    }

    startCycles() {
        const keywords = document.getElementById('keywords').value;
        const website = document.getElementById('website').value;
        const cycles = document.getElementById('cycles').value;
        const delay = document.getElementById('delay').value;

        if (!keywords.trim() || !website.trim()) {
            alert('Please fill in both keywords and target website!');
            return;
        }

        this.socket.emit('start_cycles', {
            keywords: keywords,
            website: website,
            cycles: parseInt(cycles),
            delay: parseInt(delay)
        });
    }

    stopCycles() {
        this.socket.emit('stop_cycles');
    }

    updateCycleInfo(current, total) {
        document.getElementById('currentCycle').textContent = current;
        document.getElementById('totalCycles').textContent = total;
    }

    addStatusLog(message) {
        const statusLog = document.getElementById('statusLog');
        const statusItem = document.createElement('div');
        statusItem.className = 'status-item';
        statusItem.textContent = message;
        
        statusLog.appendChild(statusItem);
        statusLog.scrollTop = statusLog.scrollHeight;

        // Keep only last 100 messages
        const items = statusLog.getElementsByClassName('status-item');
        if (items.length > 100) {
            items[0].remove();
        }
    }

    updateButtonStates() {
        const startBtn = document.getElementById('startBtn');
        const stopBtn = document.getElementById('stopBtn');

        if (this.isRunning) {
            startBtn.disabled = true;
            stopBtn.disabled = false;
            startBtn.textContent = 'Running...';
        } else {
            startBtn.disabled = false;
            stopBtn.disabled = true;
            startBtn.textContent = 'Start SEO Booster';
        }
    }
}

// Initialize the application when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new SEOTrafficBoosterUI();
});
