// ===== 설정 =====
const API_BASE_URL = 'http://localhost:8000';

// ===== 전역 변수 =====
let charts = {};
let refreshInterval = null;
let systemTrendData = {
    labels: [],
    cpu: [],
    memory: [],
    disk: []
};

// ===== 초기화 =====
document.addEventListener('DOMContentLoaded', () => {
    initializeApp();
});

async function initializeApp() {
    setupNavigation();
    setupEventListeners();
    await checkAPIConnection();
    loadDashboardData();
    initCharts();
    startAutoRefresh();
}

// ===== 네비게이션 =====
function setupNavigation() {
    const navItems = document.querySelectorAll('.nav-item');
    const pages = document.querySelectorAll('.page-content');
    
    navItems.forEach(item => {
        item.addEventListener('click', (e) => {
            e.preventDefault();
            const targetPage = item.dataset.page;
            
            // 네비게이션 활성화 상태 변경
            navItems.forEach(nav => nav.classList.remove('active'));
            item.classList.add('active');
            
            // 페이지 전환
            pages.forEach(page => page.classList.remove('active'));
            document.getElementById(`${targetPage}-page`).classList.add('active');
            
            // 페이지 타이틀 변경
            const titles = {
                'dashboard': '대시보드',
                'jobs': '작업 관리',
                'monitoring': '시스템 모니터링',
                'executions': '실행 이력',
                'notifications': '알림'
            };
            document.getElementById('page-title').textContent = titles[targetPage];
            
            // 페이지별 데이터 로드
            loadPageData(targetPage);
        });
    });
}

function setupEventListeners() {
    // 메뉴 토글
    document.getElementById('menuToggle').addEventListener('click', () => {
        document.querySelector('.sidebar').classList.toggle('collapsed');
        document.querySelector('.main-content').classList.toggle('expanded');
    });
    
    // 새로고침
    document.getElementById('refreshBtn').addEventListener('click', async () => {
        const btn = document.getElementById('refreshBtn');
        btn.classList.add('spinning');
        await loadDashboardData();
        setTimeout(() => btn.classList.remove('spinning'), 600);
    });
    
    // 작업 생성 버튼
    document.getElementById('createJobBtn')?.addEventListener('click', () => {
        openJobModal();
    });
    
    // 모달 닫기
    document.getElementById('closeModal')?.addEventListener('click', closeJobModal);
    document.getElementById('cancelModal')?.addEventListener('click', closeJobModal);
    
    // 모달 배경 클릭
    document.getElementById('jobModal')?.addEventListener('click', (e) => {
        if (e.target.id === 'jobModal') closeJobModal();
    });
    
    // 작업 폼 제출
    document.getElementById('jobForm')?.addEventListener('submit', async (e) => {
        e.preventDefault();
        await saveJob();
    });
    
    // 필터 이벤트
    document.getElementById('jobTypeFilter')?.addEventListener('change', loadJobs);
    document.getElementById('jobStatusFilter')?.addEventListener('change', loadJobs);
    document.getElementById('jobSearch')?.addEventListener('input', debounce(loadJobs, 500));
    document.getElementById('executionStatusFilter')?.addEventListener('change', loadExecutions);
    document.getElementById('notificationLevelFilter')?.addEventListener('change', loadNotifications);
}

// ===== API 연결 확인 =====
async function checkAPIConnection() {
    try {
        const response = await fetch(`${API_BASE_URL}/health`);
        const data = await response.json();
        
        if (data.status === 'healthy') {
            updateAPIStatus(true);
        } else {
            updateAPIStatus(false);
        }
    } catch (error) {
        console.error('API 연결 실패:', error);
        updateAPIStatus(false);
    }
}

function updateAPIStatus(connected) {
    const icon = document.getElementById('api-status-icon');
    const text = document.getElementById('api-status-text');
    
    if (connected) {
        icon.className = 'fas fa-circle connected';
        text.textContent = 'API 연결됨';
    } else {
        icon.className = 'fas fa-circle disconnected';
        text.textContent = 'API 연결 끊김';
    }
}

// ===== 대시보드 데이터 로드 =====
async function loadDashboardData() {
    try {
        // 통계 로드
        const stats = await fetchAPI('/monitoring/stats');
        updateStats(stats);
        
        // 최근 실행 이력
        const executions = await fetchAPI('/monitoring/recent?type=executions&limit=5');
        updateRecentExecutions(executions);
        
        // 시스템 메트릭
        const metrics = await fetchAPI('/monitoring/metrics/current');
        updateResourceChart(metrics);
        
    } catch (error) {
        console.error('대시보드 데이터 로드 실패:', error);
    }
}

function updateStats(stats) {
    document.getElementById('total-jobs').textContent = stats.total_jobs || 0;
    document.getElementById('enabled-jobs').textContent = stats.enabled_jobs || 0;
    document.getElementById('total-executions').textContent = stats.total_executions || 0;
    document.getElementById('success-rate').textContent = `${stats.success_rate || 0}%`;
}

function updateRecentExecutions(executions) {
    const container = document.getElementById('recent-executions');
    
    if (!executions || executions.length === 0) {
        container.innerHTML = '<div class="loading">최근 실행 이력이 없습니다.</div>';
        return;
    }
    
    container.innerHTML = executions.map(exec => `
        <div class="activity-item ${exec.status}">
            <div class="activity-info">
                <h4>${exec.job_name || 'Unknown Job'}</h4>
                <p>${formatDateTime(exec.started_at)}</p>
            </div>
            <div class="activity-status ${exec.status}">
                ${exec.status.toUpperCase()}
            </div>
        </div>
    `).join('');
}

// ===== 차트 초기화 =====
function initCharts() {
    // 실행 통계 차트
    const executionCtx = document.getElementById('executionChart');
    if (executionCtx) {
        charts.execution = new Chart(executionCtx, {
            type: 'doughnut',
            data: {
                labels: ['성공', '실패', '진행 중'],
                datasets: [{
                    data: [0, 0, 0],
                    backgroundColor: ['#10b981', '#ef4444', '#f59e0b'],
                    borderWidth: 0
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: { color: '#94a3b8' }
                    }
                }
            }
        });
    }
    
    // 리소스 차트
    const resourceCtx = document.getElementById('resourceChart');
    if (resourceCtx) {
        charts.resource = new Chart(resourceCtx, {
            type: 'bar',
            data: {
                labels: ['CPU', '메모리', '디스크'],
                datasets: [{
                    label: '사용률 (%)',
                    data: [0, 0, 0],
                    backgroundColor: ['#3b82f6', '#8b5cf6', '#f59e0b'],
                    borderWidth: 0
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                scales: {
                    y: {
                        beginAtZero: true,
                        max: 100,
                        ticks: { color: '#94a3b8' },
                        grid: { color: '#334155' }
                    },
                    x: {
                        ticks: { color: '#94a3b8' },
                        grid: { display: false }
                    }
                },
                plugins: {
                    legend: { display: false }
                }
            }
        });
    }
    
    // 시스템 추이 차트
    const trendCtx = document.getElementById('systemTrendChart');
    if (trendCtx) {
        charts.trend = new Chart(trendCtx, {
            type: 'line',
            data: {
                labels: [],
                datasets: [
                    {
                        label: 'CPU %',
                        data: [],
                        borderColor: '#3b82f6',
                        backgroundColor: 'rgba(59, 130, 246, 0.1)',
                        tension: 0.4
                    },
                    {
                        label: '메모리 %',
                        data: [],
                        borderColor: '#8b5cf6',
                        backgroundColor: 'rgba(139, 92, 246, 0.1)',
                        tension: 0.4
                    },
                    {
                        label: '디스크 %',
                        data: [],
                        borderColor: '#f59e0b',
                        backgroundColor: 'rgba(245, 158, 11, 0.1)',
                        tension: 0.4
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                scales: {
                    y: {
                        beginAtZero: true,
                        max: 100,
                        ticks: { color: '#94a3b8' },
                        grid: { color: '#334155' }
                    },
                    x: {
                        ticks: { color: '#94a3b8' },
                        grid: { color: '#334155' }
                    }
                },
                plugins: {
                    legend: {
                        labels: { color: '#94a3b8' }
                    }
                }
            }
        });
    }
}

function updateResourceChart(metrics) {
    if (!metrics) return;
    
    // 실행 차트 업데이트 (통계에서)
    fetchAPI('/monitoring/stats').then(stats => {
        if (charts.execution) {
            charts.execution.data.datasets[0].data = [
                stats.success_executions || 0,
                stats.failed_executions || 0,
                0
            ];
            charts.execution.update();
        }
    });
    
    // 리소스 차트 업데이트
    if (charts.resource && metrics.cpu && metrics.memory && metrics.disk) {
        charts.resource.data.datasets[0].data = [
            metrics.cpu.percent || 0,
            metrics.memory.percent || 0,
            metrics.disk.percent || 0
        ];
        charts.resource.update();
    }
    
    // 추이 차트 업데이트
    if (charts.trend && metrics.cpu && metrics.memory && metrics.disk) {
        const now = new Date().toLocaleTimeString('ko-KR', { 
            hour: '2-digit', 
            minute: '2-digit' 
        });
        
        systemTrendData.labels.push(now);
        systemTrendData.cpu.push(metrics.cpu.percent || 0);
        systemTrendData.memory.push(metrics.memory.percent || 0);
        systemTrendData.disk.push(metrics.disk.percent || 0);
        
        // 최대 20개 데이터 포인트 유지
        if (systemTrendData.labels.length > 20) {
            systemTrendData.labels.shift();
            systemTrendData.cpu.shift();
            systemTrendData.memory.shift();
            systemTrendData.disk.shift();
        }
        
        charts.trend.data.labels = systemTrendData.labels;
        charts.trend.data.datasets[0].data = systemTrendData.cpu;
        charts.trend.data.datasets[1].data = systemTrendData.memory;
        charts.trend.data.datasets[2].data = systemTrendData.disk;
        charts.trend.update();
    }
}

// ===== 페이지별 데이터 로드 =====
async function loadPageData(page) {
    switch(page) {
        case 'dashboard':
            await loadDashboardData();
            break;
        case 'jobs':
            await loadJobs();
            break;
        case 'monitoring':
            await loadMonitoring();
            break;
        case 'executions':
            await loadExecutions();
            break;
        case 'notifications':
            await loadNotifications();
            break;
    }
}

// ===== 작업 관리 =====
async function loadJobs() {
    try {
        const typeFilter = document.getElementById('jobTypeFilter')?.value || '';
        const statusFilter = document.getElementById('jobStatusFilter')?.value || '';
        const search = document.getElementById('jobSearch')?.value || '';
        
        let url = '/jobs?';
        if (typeFilter) url += `job_type=${typeFilter}&`;
        if (statusFilter) url += `enabled=${statusFilter}&`;
        
        const data = await fetchAPI(url);
        
        const tbody = document.getElementById('jobs-tbody');
        if (!data.items || data.items.length === 0) {
            tbody.innerHTML = '<tr><td colspan="7" class="loading">작업이 없습니다.</td></tr>';
            return;
        }
        
        // 검색 필터 적용
        let jobs = data.items;
        if (search) {
            jobs = jobs.filter(job => 
                job.name.toLowerCase().includes(search.toLowerCase()) ||
                (job.description && job.description.toLowerCase().includes(search.toLowerCase()))
            );
        }
        
        tbody.innerHTML = jobs.map(job => `
            <tr>
                <td>${job.id}</td>
                <td><strong>${job.name}</strong></td>
                <td>${job.job_type}</td>
                <td><code>${job.cron_expression}</code></td>
                <td>
                    <span class="status-badge ${job.enabled ? 'enabled' : 'disabled'}">
                        ${job.enabled ? '활성' : '비활성'}
                    </span>
                </td>
                <td>${job.last_execution_at ? formatDateTime(job.last_execution_at) : '-'}</td>
                <td>
                    <div class="action-buttons">
                        <button class="btn btn-sm btn-primary" onclick="executeJob(${job.id})">
                            <i class="fas fa-play"></i>
                        </button>
                        <button class="btn btn-sm btn-secondary" onclick="toggleJob(${job.id}, ${!job.enabled})">
                            <i class="fas fa-${job.enabled ? 'pause' : 'play'}"></i>
                        </button>
                        <button class="btn btn-sm btn-danger" onclick="deleteJob(${job.id})">
                            <i class="fas fa-trash"></i>
                        </button>
                    </div>
                </td>
            </tr>
        `).join('');
        
    } catch (error) {
        console.error('작업 로드 실패:', error);
        document.getElementById('jobs-tbody').innerHTML = 
            '<tr><td colspan="7" class="loading">데이터 로드 실패</td></tr>';
    }
}

async function executeJob(jobId) {
    if (!confirm('이 작업을 즉시 실행하시겠습니까?')) return;
    
    try {
        await fetchAPI(`/jobs/${jobId}/execute`, 'POST');
        alert('작업이 실행되었습니다.');
        await loadJobs();
    } catch (error) {
        alert('작업 실행 실패: ' + error.message);
    }
}

async function toggleJob(jobId, enable) {
    try {
        await fetchAPI(`/jobs/${jobId}/${enable ? 'enable' : 'disable'}`, 'POST');
        await loadJobs();
    } catch (error) {
        alert('작업 상태 변경 실패: ' + error.message);
    }
}

async function deleteJob(jobId) {
    if (!confirm('정말로 이 작업을 삭제하시겠습니까?')) return;
    
    try {
        await fetchAPI(`/jobs/${jobId}`, 'DELETE');
        alert('작업이 삭제되었습니다.');
        await loadJobs();
    } catch (error) {
        alert('작업 삭제 실패: ' + error.message);
    }
}

// ===== 작업 모달 =====
function openJobModal(job = null) {
    const modal = document.getElementById('jobModal');
    const title = document.getElementById('modal-title');
    
    if (job) {
        title.textContent = '작업 수정';
        document.getElementById('job-name').value = job.name;
        document.getElementById('job-description').value = job.description || '';
        document.getElementById('job-type').value = job.job_type;
        document.getElementById('job-script-path').value = job.script_path;
        document.getElementById('job-cron').value = job.cron_expression;
        document.getElementById('job-timeout').value = job.timeout_seconds;
        document.getElementById('job-enabled').checked = job.enabled;
    } else {
        title.textContent = '새 작업 생성';
        document.getElementById('jobForm').reset();
    }
    
    modal.classList.add('active');
}

function closeJobModal() {
    document.getElementById('jobModal').classList.remove('active');
}

async function saveJob() {
    const jobData = {
        name: document.getElementById('job-name').value,
        description: document.getElementById('job-description').value,
        job_type: document.getElementById('job-type').value,
        script_path: document.getElementById('job-script-path').value,
        cron_expression: document.getElementById('job-cron').value,
        timeout_seconds: parseInt(document.getElementById('job-timeout').value),
        enabled: document.getElementById('job-enabled').checked
    };
    
    try {
        await fetchAPI('/jobs', 'POST', jobData);
        alert('작업이 저장되었습니다.');
        closeJobModal();
        await loadJobs();
    } catch (error) {
        alert('작업 저장 실패: ' + error.message);
    }
}

// ===== 시스템 모니터링 =====
async function loadMonitoring() {
    try {
        const metrics = await fetchAPI('/monitoring/metrics/current');
        updateMonitoringDisplay(metrics);
    } catch (error) {
        console.error('모니터링 데이터 로드 실패:', error);
    }
}

function updateMonitoringDisplay(metrics) {
    if (!metrics) return;
    
    // CPU
    if (metrics.cpu) {
        document.getElementById('cpu-percent').textContent = `${metrics.cpu.percent}%`;
        document.getElementById('cpu-progress').style.width = `${metrics.cpu.percent}%`;
        document.getElementById('cpu-count').textContent = metrics.cpu.count;
    }
    
    // 메모리
    if (metrics.memory) {
        document.getElementById('memory-percent').textContent = `${metrics.memory.percent}%`;
        document.getElementById('memory-progress').style.width = `${metrics.memory.percent}%`;
        document.getElementById('memory-used').textContent = metrics.memory.used_gb.toFixed(2);
        document.getElementById('memory-total').textContent = metrics.memory.total_gb.toFixed(2);
    }
    
    // 디스크
    if (metrics.disk) {
        document.getElementById('disk-percent').textContent = `${metrics.disk.percent}%`;
        document.getElementById('disk-progress').style.width = `${metrics.disk.percent}%`;
        document.getElementById('disk-used').textContent = metrics.disk.used_gb.toFixed(2);
        document.getElementById('disk-total').textContent = metrics.disk.total_gb.toFixed(2);
    }
    
    // 네트워크
    if (metrics.network) {
        document.getElementById('network-sent').textContent = metrics.network.sent_mb.toFixed(2);
        document.getElementById('network-recv').textContent = metrics.network.recv_mb.toFixed(2);
    }
    
    // 호스트명
    document.getElementById('hostname').textContent = metrics.hostname || '-';
}

// ===== 실행 이력 =====
async function loadExecutions() {
    try {
        const statusFilter = document.getElementById('executionStatusFilter')?.value || '';
        
        let url = '/jobs/executions?limit=50';
        if (statusFilter) url += `&status_filter=${statusFilter}`;
        
        const data = await fetchAPI(url);
        
        const tbody = document.getElementById('executions-tbody');
        if (!data.items || data.items.length === 0) {
            tbody.innerHTML = '<tr><td colspan="7" class="loading">실행 이력이 없습니다.</td></tr>';
            return;
        }
        
        tbody.innerHTML = data.items.map(exec => `
            <tr>
                <td>${exec.id}</td>
                <td>${exec.job_name || 'Unknown'}</td>
                <td>
                    <span class="status-badge ${exec.status}">
                        ${exec.status.toUpperCase()}
                    </span>
                </td>
                <td>${formatDateTime(exec.started_at)}</td>
                <td>${exec.completed_at ? formatDateTime(exec.completed_at) : '-'}</td>
                <td>${exec.duration_seconds ? exec.duration_seconds.toFixed(2) + 's' : '-'}</td>
                <td>
                    <button class="btn btn-sm btn-secondary" onclick="viewExecutionDetail(${exec.id})">
                        <i class="fas fa-eye"></i>
                    </button>
                </td>
            </tr>
        `).join('');
        
    } catch (error) {
        console.error('실행 이력 로드 실패:', error);
        document.getElementById('executions-tbody').innerHTML = 
            '<tr><td colspan="7" class="loading">데이터 로드 실패</td></tr>';
    }
}

function viewExecutionDetail(execId) {
    // TODO: 실행 상세 모달 구현
    alert(`실행 ID ${execId}의 상세 정보 (구현 예정)`);
}

// ===== 알림 =====
async function loadNotifications() {
    try {
        const levelFilter = document.getElementById('notificationLevelFilter')?.value || '';
        
        let url = '/monitoring/notifications?limit=50';
        if (levelFilter) url += `&level=${levelFilter}`;
        
        const data = await fetchAPI(url);
        
        const container = document.getElementById('notifications-list');
        if (!data.items || data.items.length === 0) {
            container.innerHTML = '<div class="loading">알림이 없습니다.</div>';
            return;
        }
        
        container.innerHTML = data.items.map(notif => `
            <div class="notification-item ${notif.level}">
                <div class="notification-header">
                    <h4>${notif.title}</h4>
                    <span class="notification-level ${notif.level}">
                        ${notif.level}
                    </span>
                </div>
                <div class="notification-message">${notif.message}</div>
                <div class="notification-time">
                    ${formatDateTime(notif.sent_at)}
                </div>
            </div>
        `).join('');
        
    } catch (error) {
        console.error('알림 로드 실패:', error);
        document.getElementById('notifications-list').innerHTML = 
            '<div class="loading">데이터 로드 실패</div>';
    }
}

// ===== 자동 새로고침 =====
function startAutoRefresh() {
    // 30초마다 자동 새로고침
    refreshInterval = setInterval(async () => {
        const activePage = document.querySelector('.page-content.active');
        if (activePage) {
            const pageId = activePage.id.replace('-page', '');
            await loadPageData(pageId);
        }
    }, 30000);
}

// ===== 유틸리티 함수 =====
async function fetchAPI(endpoint, method = 'GET', body = null) {
    const options = {
        method,
        headers: {
            'Content-Type': 'application/json'
        }
    };
    
    if (body) {
        options.body = JSON.stringify(body);
    }
    
    const response = await fetch(`${API_BASE_URL}${endpoint}`, options);
    
    if (!response.ok) {
        throw new Error(`API 오류: ${response.statusText}`);
    }
    
    return await response.json();
}

function formatDateTime(dateString) {
    if (!dateString) return '-';
    const date = new Date(dateString);
    return date.toLocaleString('ko-KR', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit'
    });
}

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