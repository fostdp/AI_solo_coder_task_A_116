class App {
    constructor() {
        this.sceneManager = null;
        this.spinningWheel = null;
        this.chartManager = null;
        this.apiClient = apiClient;
        this.elapsedTime = 0;
        this.updateInterval = 0.1;
        this.lastUpdateTime = 0;
        this.useApi = false;
        this.currentData = null;
        this.alarms = [];
        this.convergenceChart = null;

        this.init();
        this.setupEventListeners();
    }

    init() {
        this.sceneManager = new SceneManager('three-container');
        this.spinningWheel = new SpinningWheel(this.sceneManager.scene);
        this.sceneManager.setSpinningWheel(this.spinningWheel);
        this.chartManager = new ChartManager();

        this.sceneManager.onComponentClick((data) => this.showInfoPanel(data));

        this.sceneManager.setWaterVisible(true);
        this.spinningWheel.setYarnVisible(true);

        this.updateDataDisplay();
    }

    setupEventListeners() {
        const speedControl = document.getElementById('speed-control');
        const speedValue = document.getElementById('speed-value');

        speedControl.addEventListener('input', (e) => {
            const speed = parseInt(e.target.value);
            speedValue.textContent = speed + ' rpm';
            if (!this.useApi) {
                this.sceneManager.setWheelSpeed(speed);
            }
        });

        const showYarn = document.getElementById('show-yarn');
        showYarn.addEventListener('change', (e) => {
            this.spinningWheel.setYarnVisible(e.target.checked);
        });

        const showWater = document.getElementById('show-water');
        showWater.addEventListener('change', (e) => {
            this.sceneManager.setWaterVisible(e.target.checked);
        });

        const useApi = document.getElementById('use-api');
        useApi.addEventListener('change', (e) => {
            this.useApi = e.target.checked;
            if (this.useApi) {
                this.connectToApi();
            } else {
                this.disconnectFromApi();
            }
        });

        const apiUrl = document.getElementById('api-url');
        apiUrl.addEventListener('change', (e) => {
            this.apiClient.setBaseUrl(e.target.value);
        });

        const resetView = document.getElementById('reset-view');
        resetView.addEventListener('click', () => {
            this.sceneManager.resetCamera();
        });

        const toggleRotation = document.getElementById('toggle-rotation');
        toggleRotation.addEventListener('click', () => {
            const isRotating = this.sceneManager.toggleRotation();
            const statusEl = document.getElementById('status');
            if (isRotating) {
                statusEl.textContent = this.useApi ? '运行中' : '模拟模式';
                statusEl.className = 'data-value status-running';
            } else {
                statusEl.textContent = '已暂停';
                statusEl.className = 'data-value status-stopped';
            }
        });

        const closeInfo = document.getElementById('close-info');
        closeInfo.addEventListener('click', () => {
            this.hideInfoPanel();
        });

        const runOptimization = document.getElementById('run-optimization');
        runOptimization.addEventListener('click', () => {
            this.runOptimization();
        });

        this.apiClient.onData((data) => {
            this.currentData = data;
            this.updateFromApiData(data);
        });

        this.apiClient.onConnection((type, connected) => {
            this.updateConnectionStatus(type, connected);
        });

        this.startDataUpdateLoop();
    }

    async connectToApi() {
        const apiUrl = document.getElementById('api-url').value;
        this.apiClient.setBaseUrl(apiUrl);

        try {
            await this.apiClient.checkHealth();
            document.getElementById('status').textContent = '连接中...';

            try {
                await this.apiClient.connectWebSocket();
            } catch (e) {
                console.warn('WebSocket连接失败，使用轮询模式');
            }

            const data = await this.apiClient.getData();
            this.currentData = data;
            this.updateFromApiData(data);

            document.getElementById('status').textContent = '运行中';
        } catch (e) {
            console.error('API连接失败:', e);
            document.getElementById('use-api').checked = false;
            this.useApi = false;
            alert('无法连接到后端API，请确保服务已启动');
        }
    }

    disconnectFromApi() {
        this.apiClient.disconnectWebSocket();
        this.currentData = null;
        document.getElementById('status').textContent = '模拟模式';
    }

    updateConnectionStatus(type, connected) {
        if (type === 'api') {
            const el = document.getElementById('api-status');
            el.textContent = connected ? 'API已连接' : 'API未连接';
            el.className = 'status-indicator ' + (connected ? 'status-connected' : 'status-disconnected');
        } else if (type === 'websocket') {
            const el = document.getElementById('ws-status');
            el.textContent = connected ? 'WebSocket已连接' : 'WebSocket未连接';
            el.className = 'status-indicator ' + (connected ? 'status-connected' : 'status-disconnected');
        }
    }

    updateFromApiData(data) {
        const waterWheel = data.water_wheel || {};
        const spindles = data.spindles || [];

        const wheelRpm = waterWheel.rotational_speed || 0;
        this.sceneManager.setWheelSpeed(Math.min(wheelRpm, 60));

        const activeSpindles = spindles.filter(s => !s.broken);
        const avgSpeed = activeSpindles.length > 0
            ? activeSpindles.reduce((sum, s) => sum + s.speed, 0) / activeSpindles.length
            : 0;
        const avgTension = activeSpindles.length > 0
            ? activeSpindles.reduce((sum, s) => sum + s.tension, 0) / activeSpindles.length
            : 0;
        const avgTwist = activeSpindles.length > 0
            ? activeSpindles.reduce((sum, s) => sum + s.twist, 0) / activeSpindles.length
            : 0;

        document.getElementById('wheel-speed').textContent = wheelRpm.toFixed(1);
        document.getElementById('spindle-speed').textContent = avgSpeed.toFixed(1);
        document.getElementById('tension').textContent = avgTension.toFixed(2);
        document.getElementById('twist').textContent = avgTwist.toFixed(1);
        document.getElementById('power').textContent = (data.energy_efficiency ? avgSpeed * 0.05 : 0.5).toFixed(2);
        document.getElementById('efficiency').textContent = (data.energy_efficiency || 0).toFixed(2);
        document.getElementById('breakage-rate').textContent = (data.breakage_rate || 0).toFixed(1);

        this.chartManager.addDataPoint(wheelRpm, avgTwist, this.elapsedTime);
        this.updateEfficiencyChart(data);
    }

    updateEfficiencyChart(data) {
        const efficiencyData = [
            { label: '水轮效率', value: 85 },
            { label: '传动效率', value: 92 },
            { label: '纺纱效率', value: 78 },
            { label: '综合能效', value: (data.energy_efficiency || 10) * 5 }
        ];
        this.chartManager.updateEfficiencyChart(efficiencyData);
    }

    startDataUpdateLoop() {
        const updateLoop = (timestamp) => {
            const delta = (timestamp - this.lastUpdateTime) / 1000;

            if (delta >= this.updateInterval) {
                this.elapsedTime += delta;
                if (!this.useApi) {
                    this.updateDataDisplay();
                    this.updateCharts();
                }
                this.lastUpdateTime = timestamp;
            }

            requestAnimationFrame(updateLoop);
        };

        requestAnimationFrame(updateLoop);
    }

    updateDataDisplay() {
        const wheelSpeed = this.sceneManager.wheelSpeed;
        const spindleSpeed = this.spinningWheel.getSpindleSpeed(wheelSpeed);
        const tension = this.spinningWheel.getTension(wheelSpeed);
        const twist = this.spinningWheel.getTwist(wheelSpeed);
        const power = this.spinningWheel.getPower(wheelSpeed);
        const efficiency = wheelSpeed > 0 ? (wheelSpeed * 0.3) : 0;
        const breakage = wheelSpeed > 40 ? (wheelSpeed - 40) * 0.2 : 0;

        document.getElementById('wheel-speed').textContent = wheelSpeed.toFixed(1);
        document.getElementById('spindle-speed').textContent = spindleSpeed.toFixed(1);
        document.getElementById('tension').textContent = tension.toFixed(2);
        document.getElementById('twist').textContent = twist.toFixed(1);
        document.getElementById('power').textContent = power.toFixed(3);
        document.getElementById('efficiency').textContent = efficiency.toFixed(2);
        document.getElementById('breakage-rate').textContent = breakage.toFixed(1);
    }

    updateCharts() {
        const wheelSpeed = this.sceneManager.wheelSpeed;
        const twist = this.spinningWheel.getTwist(wheelSpeed);
        this.chartManager.addDataPoint(wheelSpeed, twist, this.elapsedTime);

        const efficiencyData = [
            { label: '水轮效率', value: 85 },
            { label: '传动效率', value: 92 },
            { label: '纺纱效率', value: 78 },
            { label: '综合能效', value: wheelSpeed * 1.2 }
        ];
        this.chartManager.updateEfficiencyChart(efficiencyData);
    }

    async runOptimization() {
        const btn = document.getElementById('run-optimization');
        btn.disabled = true;
        btn.textContent = '优化中...';

        try {
            const params = {
                water_speed: parseFloat(document.getElementById('opt-water-speed').value),
                wheel_radius: 1.5,
                gear_ratio: 8.0,
                mechanical_efficiency: 0.85,
                friction_coefficient: 0.05,
                min_tension: parseFloat(document.getElementById('opt-min-tension').value),
                max_tension: parseFloat(document.getElementById('opt-max-tension').value),
                max_twist_cv: parseFloat(document.getElementById('opt-max-cv').value),
                population_size: parseInt(document.getElementById('opt-population').value),
                generations: parseInt(document.getElementById('opt-generations').value)
            };

            let result;
            if (this.useApi && this.apiClient.isApiConnected()) {
                result = await this.apiClient.runOptimization(params);
            } else {
                result = this.simulateOptimization(params);
            }

            this.displayOptimizationResult(result);
        } catch (e) {
            console.error('优化失败:', e);
            alert('优化计算失败: ' + e.message);
        } finally {
            btn.disabled = false;
            btn.textContent = '运行优化';
        }
    }

    simulateOptimization(params) {
        const history = [];
        let best = 0;
        for (let i = 0; i < params.generations; i++) {
            const val = 5 + Math.random() * 3 + (i / params.generations) * 8;
            if (val > best) best = val;
            history.push(best);
        }

        return {
            optimal_num_spindles: 42,
            optimal_blade_angle: 48.5,
            max_objective_value: best,
            total_production_rate: 35.2,
            energy_efficiency: 12.8,
            twist_uniformity_cv: 3.2,
            breakage_rate: 2.1,
            convergence_history: history
        };
    }

    displayOptimizationResult(result) {
        const resultDiv = document.getElementById('optimization-result');
        resultDiv.classList.remove('hidden');

        document.getElementById('opt-spindles').textContent = result.optimal_num_spindles + ' 个';
        document.getElementById('opt-blade-angle').textContent = result.optimal_blade_angle.toFixed(1) + '°';
        document.getElementById('opt-efficiency').textContent = result.energy_efficiency.toFixed(2) + ' m/min·kW';
        document.getElementById('opt-production').textContent = result.total_production_rate.toFixed(2) + ' m/min';

        this.renderConvergenceChart(result.convergence_history);
    }

    renderConvergenceChart(history) {
        const ctx = document.getElementById('convergence-chart').getContext('2d');

        if (this.convergenceChart) {
            this.convergenceChart.destroy();
        }

        this.convergenceChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: history.map((_, i) => i),
                datasets: [{
                    label: '适应度值',
                    data: history,
                    borderColor: '#e94560',
                    backgroundColor: 'rgba(233, 69, 96, 0.1)',
                    fill: true,
                    tension: 0.4,
                    pointRadius: 0
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false },
                    title: {
                        display: true,
                        text: '收敛曲线',
                        color: '#e0e0e0',
                        font: { size: 12 }
                    }
                },
                scales: {
                    x: {
                        ticks: { color: '#888' },
                        grid: { color: 'rgba(255,255,255,0.1)' }
                    },
                    y: {
                        ticks: { color: '#888' },
                        grid: { color: 'rgba(255,255,255,0.1)' }
                    }
                }
            }
        });
    }

    showInfoPanel(data) {
        const panel = document.getElementById('info-panel');
        const title = document.getElementById('info-title');
        const body = document.getElementById('info-body');

        title.textContent = data.name || '部件信息';

        let html = '';

        if (data.description) {
            html += `<p style="margin-bottom: 10px; color: #e0e0e0; line-height: 1.6;">${data.description}</p>`;
        }

        html += '<div style="border-top: 1px solid rgba(233, 69, 96, 0.3); padding-top: 10px;">';

        const fields = {
            'diameter': '直径',
            'height': '高度',
            'length': '长度',
            'width': '宽度',
            'weight': '重量',
            'material': '材质',
            'bladeCount': '叶片数',
            'transmission': '传动方式',
            'transmissionRatio': '传动比',
            'speed': '转速',
            'index': '编号'
        };

        for (const [key, label] of Object.entries(fields)) {
            if (data[key]) {
                html += `<p><span class="info-label">${label}：</span><span class="info-value">${data[key]}</span></p>`;
            }
        }

        html += '</div>';

        if (data.type === 'spindle') {
            const wheelSpeed = this.sceneManager.wheelSpeed;
            const spindleSpeed = this.spinningWheel.getSpindleSpeed(wheelSpeed) * (data.baseRotationSpeed || 1);
            html += '<div style="border-top: 1px solid rgba(233, 69, 96, 0.3); padding-top: 10px; margin-top: 10px;">';
            html += `<p><span class="info-label">当前转速：</span><span class="info-value">${spindleSpeed.toFixed(1)} rpm</span></p>`;
            html += '</div>';
        }

        body.innerHTML = html;
        panel.classList.remove('hidden');
    }

    hideInfoPanel() {
        const panel = document.getElementById('info-panel');
        panel.classList.add('hidden');
    }

    addAlarm(alarm) {
        this.alarms.unshift(alarm);
        if (this.alarms.length > 50) {
            this.alarms = this.alarms.slice(0, 50);
        }
        this.renderAlarms();
    }

    renderAlarms() {
        const list = document.getElementById('alarm-list');
        if (this.alarms.length === 0) {
            list.innerHTML = '<div class="alarm-empty">暂无告警</div>';
            return;
        }

        list.innerHTML = this.alarms.map(alarm => `
            <div class="alarm-item alarm-${alarm.severity || 'warning'}">
                <div class="alarm-header">
                    <span class="alarm-type">${alarm.alarm_type || '告警'}</span>
                    <span class="alarm-time">${new Date(alarm.timestamp).toLocaleTimeString()}</span>
                </div>
                <div class="alarm-message">${alarm.message || ''}</div>
            </div>
        `).join('');
    }
}

document.addEventListener('DOMContentLoaded', () => {
    window.app = new App();
});
