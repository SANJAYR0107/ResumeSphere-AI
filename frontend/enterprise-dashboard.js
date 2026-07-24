/**
 * RESUMESPHERE AI - ENTERPRISE DASHBOARD JS (Phase D)
 */

document.addEventListener('DOMContentLoaded', () => {
    
    // --- STATE ---
    let jwtToken = localStorage.getItem('rs_ent_token');
    let currentUserRole = localStorage.getItem('rs_ent_role');
    const API_AUTH = '/api/auth';
    const API_ENT = '/api/enterprise';

    // --- UI ELEMENTS ---
    const authView = document.getElementById('auth-view');
    const dashboardView = document.getElementById('dashboard-view');
    const loginBtn = document.getElementById('login-btn');
    const logoutBtn = document.getElementById('logout-btn');
    const toastContainer = document.getElementById('toast-container');
    const navItems = document.querySelectorAll('.nav-item');
    const modules = document.querySelectorAll('.module');
    
    // --- UTILS ---
    function showToast(message, type = 'info') {
        const t = document.createElement('div');
        t.className = `toast toast-${type}`;
        t.innerHTML = `<i class="fa-solid fa-${type==='success'?'check-circle':type==='error'?'exclamation-circle':'info-circle'}"></i> <span>${message}</span>`;
        toastContainer.appendChild(t);
        setTimeout(() => t.classList.add('show'), 10);
        setTimeout(() => { t.classList.remove('show'); setTimeout(()=>t.remove(), 300); }, 3000);
    }

    async function authFetch(url, options = {}) {
        if(!options.headers) options.headers = {};
        if(jwtToken) options.headers['Authorization'] = `Bearer ${jwtToken}`;
        const res = await fetch(url, options);
        if(res.status === 401) {
            logout();
            throw new Error("Unauthorized");
        }
        return res;
    }

    // --- MODULE D9: AUTHENTICATION ---
    function checkAuth() {
        if(jwtToken) {
            authView.style.display = 'none';
            dashboardView.style.display = 'flex';
            document.getElementById('user-info').innerText = `Role: ${currentUserRole}`;
            loadDashboard(); // Load default
        } else {
            authView.style.display = 'flex';
            dashboardView.style.display = 'none';
        }
    }

    function logout() {
        localStorage.removeItem('rs_ent_token');
        localStorage.removeItem('rs_ent_role');
        jwtToken = null;
        currentUserRole = null;
        checkAuth();
    }

    loginBtn.addEventListener('click', async () => {
        const email = document.getElementById('auth-email').value;
        const password = document.getElementById('auth-password').value;
        const btn = document.getElementById('login-btn');
        btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i>';
        
        try {
            const formData = new URLSearchParams();
            formData.append('username', email);
            formData.append('password', password);

            const res = await fetch(`${API_AUTH}/token`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
                body: formData
            });

            if(!res.ok) throw new Error("Invalid credentials");
            const data = await res.json();
            
            jwtToken = data.access_token;
            currentUserRole = data.role;
            localStorage.setItem('rs_ent_token', jwtToken);
            localStorage.setItem('rs_ent_role', currentUserRole);
            
            showToast(`Welcome back, ${data.full_name}`, 'success');
            checkAuth();
        } catch (e) {
            showToast(e.message, 'error');
        } finally {
            btn.innerHTML = 'Sign In';
        }
    });

    logoutBtn.addEventListener('click', logout);
    checkAuth(); // Initial check


    // --- ROUTING ---
    navItems.forEach(item => {
        item.addEventListener('click', (e) => {
            e.preventDefault();
            const targetId = item.getAttribute('data-target');
            navItems.forEach(nav => nav.classList.remove('active'));
            item.classList.add('active');
            
            modules.forEach(m => m.classList.remove('active'));
            document.getElementById(targetId).classList.add('active');
            
            if(targetId === 'module-d1') loadDashboard();
            if(targetId === 'module-d2') loadCandidates();
            if(targetId === 'module-d5') loadActivity();
            if(targetId === 'module-d6') loadInterviewDB();
            if(targetId === 'module-d7') loadAnalytics();
        });
    });

    // --- MODULE D1: DASHBOARD ---
    async function loadDashboard() {
        try {
            const res = await authFetch(`${API_ENT}/dashboard`);
            const data = await res.json();
            document.getElementById('d1-active-jobs').innerText = data.active_jobs;
            document.getElementById('d1-total-cand').innerText = data.total_candidates;
            document.getElementById('d1-shortlisted').innerText = data.shortlisted_candidates;
            loadJobs();
        } catch(e) {}
    }

    async function loadJobs() {
        try {
            const res = await authFetch(`${API_ENT}/jobs`);
            const jobs = await res.json();
            const tbody = document.querySelector('#jobs-table tbody');
            tbody.innerHTML = '';
            
            // Populate D4 dropdown as well
            const select = document.getElementById('d4-job-select');
            select.innerHTML = '';

            jobs.forEach(j => {
                tbody.innerHTML += `
                    <tr>
                        <td><strong>${j.title}</strong></td>
                        <td>${j.location}</td>
                        <td><span class="badge badge-green">${j.status}</span></td>
                        <td><button class="btn btn-secondary" style="padding:4px 8px;">View</button></td>
                    </tr>
                `;
                select.innerHTML += `<option value="${j.id}">${j.title}</option>`;
            });
        } catch(e) {}
    }

    document.getElementById('job-save-btn').addEventListener('click', async () => {
        const title = document.getElementById('job-title').value;
        const loc = document.getElementById('job-location').value;
        const desc = document.getElementById('job-desc').value;
        try {
            await authFetch(`${API_ENT}/jobs`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ title, location: loc, description: desc, requirements: desc })
            });
            showToast('Job created', 'success');
            document.getElementById('job-modal').style.display = 'none';
            loadDashboard();
        } catch (e) {
            showToast('Failed to create job', 'error');
        }
    });

    // --- MODULE D2: CANDIDATE MANAGEMENT ---
    async function loadCandidates(skills = '') {
        try {
            const res = await authFetch(`${API_ENT}/candidates?skills=${skills}`);
            const cands = await res.json();
            const tbody = document.querySelector('#candidates-table tbody');
            tbody.innerHTML = '';
            cands.forEach(c => {
                const bmk = c.is_bookmarked ? 'solid fa-bookmark' : 'regular fa-bookmark';
                tbody.innerHTML += `
                    <tr>
                        <td><strong>${c.name}</strong></td>
                        <td><div style="max-width:200px; white-space:nowrap; overflow:hidden; text-overflow:ellipsis;">${c.skills}</div></td>
                        <td><span class="badge badge-blue">${c.overall_score.toFixed(1)}</span></td>
                        <td>${c.is_shortlisted ? '<span class="badge badge-warning">Shortlisted</span>' : '-'}</td>
                        <td>
                            <button class="btn btn-secondary bmk-btn" data-id="${c.id}" style="padding:4px 8px;"><i class="fa-${bmk}"></i></button>
                        </td>
                    </tr>
                `;
            });
            
            document.querySelectorAll('.bmk-btn').forEach(btn => {
                btn.addEventListener('click', async () => {
                    await authFetch(`${API_ENT}/candidates/${btn.dataset.id}/bookmark`, {method:'POST'});
                    loadCandidates(document.getElementById('d2-search').value);
                });
            });
        } catch(e) {}
    }
    
    document.getElementById('d2-search-btn').addEventListener('click', () => {
        loadCandidates(document.getElementById('d2-search').value);
    });

    // --- MODULE D3: AI RANKING ---
    document.getElementById('d3-rank-btn').addEventListener('click', async () => {
        const jobId = document.getElementById('d4-job-select').value; // Borrowing job select for demo
        if(!jobId) return showToast('Create a job first', 'error');
        
        try {
            showToast('AI is ranking candidates...', 'info');
            await authFetch(`${API_ENT}/jobs/${jobId}/rank`, { method: 'POST' });
            showToast('Ranking complete', 'success');
            loadCandidates();
        } catch (e) {
            showToast('Ranking failed', 'error');
        }
    });

    // --- MODULE D4: BULK PROCESSING ---
    const d4Input = document.getElementById('d4-file-input');
    const d4UploadBtn = document.getElementById('d4-upload-btn');
    
    d4Input.addEventListener('change', () => {
        if(d4Input.files.length > 0) d4UploadBtn.disabled = false;
    });

    d4UploadBtn.addEventListener('click', async () => {
        const jobId = document.getElementById('d4-job-select').value;
        if(!jobId) return showToast('Select a job', 'error');
        
        const formData = new FormData();
        for(let i=0; i<d4Input.files.length; i++){
            formData.append('files', d4Input.files[i]);
        }
        
        document.getElementById('d4-progress').style.display = 'block';
        document.getElementById('d4-progress-text').innerText = `Uploading ${d4Input.files.length} files...`;
        
        try {
            await authFetch(`${API_ENT}/bulk-upload/${jobId}`, {
                method: 'POST',
                headers: { 'Authorization': `Bearer ${jwtToken}` }, // Custom options override
                body: formData
            });
            showToast('Files uploaded. Processing in background.', 'success');
            document.getElementById('d4-progress-text').innerText = 'Done';
            d4Input.value = '';
            d4UploadBtn.disabled = true;
        } catch(e) {
            showToast('Bulk upload failed', 'error');
        }
    });

    // --- MODULE D5: TEAM HUB ---
    async function loadActivity() {
        try {
            const res = await authFetch(`${API_ENT}/activity`);
            const logs = await res.json();
            const feed = document.getElementById('d5-activity-feed');
            feed.innerHTML = '';
            logs.forEach(l => {
                feed.innerHTML += `
                    <div style="padding:15px; border-bottom:1px solid var(--border-color);">
                        <strong><i class="fa-solid fa-user-circle"></i> User ${l.user.substring(0,8)}</strong> 
                        <span style="color:var(--text-secondary); font-size:12px; margin-left:10px;">${new Date(l.time).toLocaleString()}</span>
                        <div style="margin-top:5px; font-weight:500;">${l.action}</div>
                        <div style="color:var(--text-secondary); font-size:13px;">${l.details}</div>
                    </div>
                `;
            });
        } catch(e){}
    }

    // --- MODULE D6: INTERVIEW DB ---
    async function loadInterviewDB() {
        try {
            const res = await authFetch(`${API_ENT}/interview-db`);
            const records = await res.json();
            const container = document.getElementById('d6-container');
            container.innerHTML = '';
            records.forEach(r => {
                container.innerHTML += `
                    <div class="card">
                        <div class="card-title">${r.company || 'Company'} - ${r.role}</div>
                        <div style="margin: 10px 0;">
                            <span class="badge badge-warning">Difficulty: ${r.difficulty}</span>
                        </div>
                        <div style="font-size:13px; color:var(--text-secondary);">
                            <strong>Questions:</strong>
                            <ul style="padding-left:15px; margin-top:5px;">
                                ${r.questions.map(q => `<li>${q}</li>`).join('')}
                            </ul>
                        </div>
                    </div>
                `;
            });
        } catch(e){}
    }

    // --- MODULE D7: ANALYTICS ---
    let charts = {};
    async function loadAnalytics() {
        try {
            const res = await authFetch(`${API_ENT}/analytics`);
            const data = await res.json();
            
            Chart.defaults.color = '#94a3b8';
            
            if(charts.funnel) charts.funnel.destroy();
            charts.funnel = new Chart(document.getElementById('chart-funnel'), {
                type: 'bar',
                data: {
                    labels: ['Sourced', 'Applied', 'Interviewed', 'Offered'],
                    datasets: [{
                        label: 'Candidates',
                        data: [data.hiring_funnel.sourced, data.hiring_funnel.applied, data.hiring_funnel.interviewed, data.hiring_funnel.offered],
                        backgroundColor: ['#64748b', '#3b82f6', '#f59e0b', '#10b981'],
                        borderRadius: 4
                    }]
                }
            });

            if(charts.skills) charts.skills.destroy();
            charts.skills = new Chart(document.getElementById('chart-skills'), {
                type: 'line',
                data: {
                    labels: Object.keys(data.skill_demand),
                    datasets: [{
                        label: 'Demand',
                        data: Object.values(data.skill_demand),
                        borderColor: '#6366f1',
                        tension: 0.4,
                        fill: true,
                        backgroundColor: 'rgba(99, 102, 241, 0.1)'
                    }]
                }
            });
        } catch(e){}
    }

    // --- MODULE D8: NOTIFICATIONS ---
    document.getElementById('notif-btn').addEventListener('click', async () => {
        const dropdown = document.getElementById('notif-dropdown');
        if(dropdown.style.display === 'block') {
            dropdown.style.display = 'none';
            return;
        }
        
        dropdown.style.display = 'block';
        try {
            const res = await authFetch(`${API_ENT}/notifications`);
            const notifs = await res.json();
            const list = document.getElementById('notif-list');
            list.innerHTML = '';
            notifs.forEach(n => {
                list.innerHTML += `
                    <div style="padding:10px 15px; border-bottom:1px solid var(--border-color); ${!n.read?'background:rgba(99,102,241,0.1);':''}">
                        <div style="font-size:13px;">${n.text}</div>
                        <div style="font-size:11px; color:var(--text-secondary); margin-top:3px;">${n.time}</div>
                    </div>
                `;
            });
        } catch(e){}
    });

    // Close dropdown on click outside
    document.addEventListener('click', (e) => {
        if(!e.target.closest('#notif-btn') && !e.target.closest('#notif-dropdown')) {
            document.getElementById('notif-dropdown').style.display = 'none';
        }
    });
});
