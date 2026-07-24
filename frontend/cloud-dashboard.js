/**
 * RESUMESPHERE AI - GLOBAL CLOUD DASHBOARD JS (Phase F)
 */

document.addEventListener('DOMContentLoaded', () => {
    
    // --- STATE & ROUTING ---
    let jwtToken = localStorage.getItem('rs_cloud_token');
    const API = '/api/cloud';

    const authView = document.getElementById('auth-view');
    const cloudView = document.getElementById('cloud-view');
    const toastContainer = document.getElementById('toast-container');
    const navItems = document.querySelectorAll('.nav-item');
    const modules = document.querySelectorAll('.module');

    function showToast(message, type = 'info') {
        const t = document.createElement('div');
        t.className = `toast toast-${type}`;
        t.innerHTML = `<i class="fa-solid fa-${type==='success'?'check-circle':type==='error'?'exclamation-circle':'info-circle'}"></i> <span>${message}</span>`;
        toastContainer.appendChild(t);
        setTimeout(() => t.classList.add('show'), 10);
        setTimeout(() => { t.classList.remove('show'); setTimeout(()=>t.remove(), 300); }, 3000);
    }

    async function apiFetch(endpoint, options = {}) {
        if(!options.headers) options.headers = {};
        options.headers['Authorization'] = `Bearer ${jwtToken}`;
        const res = await fetch(`${API}${endpoint}`, options);
        if(res.status === 401) {
            logout();
        }
        return res;
    }

    function checkAuth() {
        if(jwtToken) {
            authView.style.display = 'none';
            cloudView.style.display = 'flex';
            document.getElementById('user-name').innerText = localStorage.getItem('rs_cloud_user') || 'Cloud User';
        } else {
            authView.style.display = 'flex';
            cloudView.style.display = 'none';
        }
    }

    window.logout = function() {
        localStorage.removeItem('rs_cloud_token');
        localStorage.removeItem('rs_cloud_user');
        jwtToken = null;
        checkAuth();
    }

    // --- MODULE F1: MULTI-CLOUD AUTH ---
    window.mockOAuth = async function(provider, code) {
        try {
            const res = await fetch(`${API}/auth/oauth`, {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({provider, code})
            });
            const data = await res.json();
            if(data.access_token) {
                jwtToken = data.access_token;
                localStorage.setItem('rs_cloud_token', jwtToken);
                localStorage.setItem('rs_cloud_user', data.full_name);
                showToast(`Authenticated via ${provider}`, 'success');
                checkAuth();
            }
        } catch(e) {
            showToast('OAuth Failed', 'error');
        }
    }

    checkAuth();

    // --- ROUTING ---
    navItems.forEach(item => {
        item.addEventListener('click', (e) => {
            e.preventDefault();
            const targetId = item.getAttribute('data-target');
            navItems.forEach(nav => nav.classList.remove('active'));
            item.classList.add('active');
            
            modules.forEach(m => m.classList.remove('active'));
            document.getElementById(targetId).classList.add('active');
            
            // Lazy loaders
            if(targetId === 'module-f2') loadFiles();
            if(targetId === 'module-f4') loadJobs();
            if(targetId === 'module-f5') loadEvents();
            if(targetId === 'module-f8') loadLogs();
            if(targetId === 'module-f9') initMetrics();
        });
    });

    // --- MODULE F2: CLOUD STORAGE ---
    const fileInput = document.getElementById('f2-file');
    fileInput.addEventListener('change', async () => {
        if(!fileInput.files.length) return;
        const formData = new FormData();
        formData.append('file', fileInput.files[0]);
        
        try {
            showToast('Uploading to S3...', 'info');
            await apiFetch('/storage/upload', { method: 'POST', body: formData });
            showToast('File secured in cloud', 'success');
            loadFiles();
        } catch(e) { showToast('Upload failed', 'error'); }
    });

    async function loadFiles() {
        try {
            const res = await apiFetch('/storage/files');
            const files = await res.json();
            const container = document.getElementById('f2-files');
            container.innerHTML = '';
            files.forEach(f => {
                container.innerHTML += `
                    <div class="card" style="padding:15px; text-align:center;">
                        <i class="fa-solid fa-file-pdf" style="font-size:2rem; color:var(--accent-rose); margin-bottom:10px;"></i>
                        <div style="font-weight:600; font-size:13px; margin-bottom:5px; white-space:nowrap; overflow:hidden; text-overflow:ellipsis;">${f.filename}</div>
                        <div style="font-size:11px; color:var(--text-secondary); margin-bottom:10px;">${f.provider} • v${f.version}</div>
                        <a href="${f.url}" target="_blank" class="btn btn-outline" style="padding:4px 10px; font-size:11px;">Download</a>
                    </div>
                `;
            });
        } catch(e){}
    }

    // --- MODULE F3: GITHUB LIVE ---
    document.getElementById('f3-sync-btn').addEventListener('click', async () => {
        const username = document.getElementById('f3-user').value || 'octocat';
        try {
            const res = await apiFetch('/github/sync', {
                method:'POST', headers:{'Content-Type':'application/json'},
                body: JSON.stringify({username})
            });
            const data = await res.json();
            document.getElementById('f3-commits').innerText = data.stats.commits;
            document.getElementById('f3-score').innerText = data.stats.score.toFixed(1);
            showToast('GitHub data synchronized', 'success');
        } catch(e) {}
    });

    // --- MODULE F4: JOB CONNECTORS ---
    document.getElementById('f4-sync-btn').addEventListener('click', loadJobs);
    
    async function loadJobs() {
        try {
            const res = await apiFetch('/jobs/sync');
            const jobs = await res.json();
            const tbody = document.getElementById('f4-jobs');
            tbody.innerHTML = '';
            jobs.forEach(j => {
                let badge = j.source==='LinkedIn' ? 'badge-blue' : 'badge-emerald';
                tbody.innerHTML += `
                    <tr style="border-bottom:1px solid var(--border-color);">
                        <td style="padding:10px; font-weight:500;">${j.title}</td>
                        <td style="padding:10px;">${j.company}</td>
                        <td style="padding:10px;"><span class="badge ${badge}">${j.source}</span></td>
                        <td style="padding:10px;"><button class="btn btn-primary" onclick="applyJob('${j.title}','${j.company}','${j.source}')" style="padding:4px 8px;">Apply</button></td>
                    </tr>
                `;
            });
        } catch(e){}
    }
    
    window.applyJob = async function(title, company, source) {
        try {
            await apiFetch('/jobs/apply', {
                method:'POST', headers:{'Content-Type':'application/json'},
                body: JSON.stringify({job_title:title, company_name:company, source})
            });
            showToast(`Applied to ${company} via ${source} Connector`, 'success');
        } catch(e){}
    }

    // --- MODULE F5: CALENDAR ---
    document.getElementById('f5-add-btn').addEventListener('click', async () => {
        try {
            const res = await apiFetch('/calendar/schedule', {
                method:'POST', headers:{'Content-Type':'application/json'},
                body: JSON.stringify({title:'Mock Interview', date: new Date().toISOString()})
            });
            const data = await res.json();
            showToast('Event synced to Calendar', 'success');
            loadEvents();
        } catch(e){}
    });
    
    async function loadEvents() {
        try {
            const res = await apiFetch('/calendar/events');
            const evts = await res.json();
            const div = document.getElementById('f5-events');
            div.innerHTML = '';
            evts.forEach(e => {
                div.innerHTML += `
                    <div style="background:rgba(255,255,255,0.03); padding:12px; border-radius:6px; border-left:3px solid var(--accent-purple);">
                        <div style="font-weight:600;">${e.title}</div>
                        <div style="font-size:12px; color:var(--text-secondary); margin-top:4px;">${new Date(e.start_time).toLocaleString()}</div>
                        <div style="font-size:12px; margin-top:4px;"><a href="${e.meeting_link}" target="_blank" style="color:var(--accent-blue);">Join Meeting</a></div>
                    </div>
                `;
            });
        } catch(e){}
    }

    // --- MODULE F7: PUBLIC API ---
    document.getElementById('f7-key-btn').addEventListener('click', async () => {
        try {
            const res = await apiFetch('/developer/keys', {method:'POST'});
            const data = await res.json();
            document.getElementById('f7-key-val').value = data.api_key;
            showToast('New API Key Generated', 'success');
        } catch(e){}
    });
    
    document.getElementById('f7-hook-btn').addEventListener('click', async () => {
        const url = document.getElementById('f7-hook-url').value;
        if(!url) return;
        try {
            await apiFetch('/developer/webhooks', {
                method:'POST', headers:{'Content-Type':'application/json'},
                body: JSON.stringify({url, event_type:'ALL'})
            });
            showToast('Webhook registered', 'success');
        } catch(e){}
    });

    // --- MODULE F8: AUTOMATIONS & F6: EMAILS ---
    window.triggerAuto = async function(task) {
        try {
            await apiFetch('/automation/execute', {
                method:'POST', headers:{'Content-Type':'application/json'},
                body: JSON.stringify({task_name:task})
            });
            showToast('Workflow triggered', 'success');
            setTimeout(loadLogs, 2500); // Wait for background task to simulate
        } catch(e){}
    }
    
    async function loadLogs() {
        try {
            const res = await apiFetch('/email/logs');
            const logs = await res.json();
            const div = document.getElementById('f6-logs');
            div.innerHTML = '';
            logs.forEach(l => {
                div.innerHTML += `
                    <div style="padding:8px 0; border-bottom:1px solid var(--border-color);">
                        <span class="badge badge-blue">${l.status}</span> 
                        <span style="margin-left:10px;">${l.subject}</span>
                    </div>
                `;
            });
        } catch(e){}
    }

    // --- MODULE F9: OBSERVABILITY ---
    let metricsChart;
    let metricsInterval;
    
    function initMetrics() {
        const ctx = document.getElementById('metrics-chart');
        if(metricsChart) metricsChart.destroy();
        if(metricsInterval) clearInterval(metricsInterval);
        
        Chart.defaults.color = '#a1a1aa';
        metricsChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: Array(10).fill(''),
                datasets: [{
                    label: 'API Latency (ms)',
                    data: Array(10).fill(50),
                    borderColor: '#10b981',
                    tension: 0.4,
                    pointRadius: 0
                }]
            },
            options: { animation: false, scales: { y: { beginAtZero: true, max: 200 } }, plugins: { legend: {display:false} } }
        });
        
        fetchMetrics();
        metricsInterval = setInterval(fetchMetrics, 3000);
    }
    
    async function fetchMetrics() {
        try {
            const res = await apiFetch('/system/metrics');
            const data = await res.json();
            
            document.getElementById('f9-metrics-text').innerHTML = `
                <div><div style="font-size:1.5rem;color:var(--text-primary);">${data.api_latency_ms.toFixed(1)}ms</div><div style="font-size:11px;">Latency</div></div>
                <div><div style="font-size:1.5rem;color:var(--text-primary);">${data.memory_usage_mb.toFixed(0)}MB</div><div style="font-size:11px;">RAM</div></div>
                <div><div style="font-size:1.5rem;color:var(--text-primary);">${data.active_connections}</div><div style="font-size:11px;">Connections</div></div>
                <div><div style="font-size:1.5rem;color:var(--text-primary);">${(data.error_rate_percent).toFixed(2)}%</div><div style="font-size:11px;">Error Rate</div></div>
            `;
            
            const chartData = metricsChart.data.datasets[0].data;
            chartData.push(data.api_latency_ms);
            chartData.shift();
            metricsChart.update();
        } catch(e){}
    }
});
