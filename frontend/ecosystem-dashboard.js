/**
 * RESUMESPHERE AI - CAREER ECOSYSTEM JS (Phase E)
 */

document.addEventListener('DOMContentLoaded', () => {
    
    // --- STATE & AUTH ---
    let jwtToken = localStorage.getItem('rs_ent_token'); // Share auth with Enterprise for demo
    const API = '/api/ecosystem';

    if(!jwtToken) {
        alert("Please login via the Enterprise portal first to access the Ecosystem.");
        window.location.href = "enterprise-dashboard.html";
        return;
    }

    // --- UI ELEMENTS ---
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

    async function apiFetch(endpoint, options = {}) {
        if(!options.headers) options.headers = {};
        options.headers['Authorization'] = `Bearer ${jwtToken}`;
        const res = await fetch(`${API}${endpoint}`, options);
        if(res.status === 401) {
            localStorage.removeItem('rs_ent_token');
            window.location.href = "index.html";
        }
        return res;
    }

    // --- ROUTING ---
    navItems.forEach(item => {
        item.addEventListener('click', (e) => {
            e.preventDefault();
            const targetId = item.getAttribute('data-target');
            navItems.forEach(nav => nav.classList.remove('active'));
            item.classList.add('active');
            
            modules.forEach(m => m.classList.remove('active'));
            document.getElementById(targetId).classList.add('active');
            
            // Lazy Load Module Data
            if(targetId === 'module-e9') loadDashboard();
            if(targetId === 'module-e4') loadJobs();
            if(targetId === 'module-e5') loadMentors();
            if(targetId === 'module-e6') loadCommunity();
            if(targetId === 'module-e8') loadInsights();
        });
    });

    // --- E9: DASHBOARD ---
    async function loadDashboard() {
        try {
            const res = await apiFetch('/dashboard');
            const data = await res.json();
            document.getElementById('user-name').innerText = data.user;
            document.getElementById('dash-gh').innerText = data.github_score || '-';
            document.getElementById('dash-li').innerText = data.linkedin_score || '-';
            document.getElementById('dash-learn').innerText = data.learning_progress + '%';
            document.getElementById('dash-apps').innerText = data.active_applications;

            // Render Chart
            renderCompletionChart(data.learning_progress);
        } catch(e) {}
    }

    function renderCompletionChart(progress) {
        const ctx = document.getElementById('chart-completion');
        if(window.compChart) window.compChart.destroy();
        Chart.defaults.color = '#94a3b8';
        window.compChart = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: ['Completed', 'Remaining'],
                datasets: [{
                    data: [progress, 100 - progress],
                    backgroundColor: ['#10b981', '#334155'],
                    borderWidth: 0,
                    cutout: '80%'
                }]
            },
            options: { plugins: { legend: { display: false } } }
        });
    }

    // --- E1: PORTFOLIO ---
    document.getElementById('btn-save-port').addEventListener('click', async () => {
        const theme = document.getElementById('port-theme').value;
        const skills = document.getElementById('port-skills').value.split(',').map(s=>s.trim());
        try {
            await apiFetch('/portfolio', {
                method: 'POST',
                headers: {'Content-Type':'application/json'},
                body: JSON.stringify({theme, skills, projects:[]})
            });
            showToast('Portfolio configuration saved', 'success');
        } catch(e) { showToast('Error saving', 'error'); }
    });

    document.getElementById('btn-export-port').addEventListener('click', async () => {
        try {
            const res = await apiFetch('/portfolio/export');
            const data = await res.json();
            const blob = new Blob([data.html], {type: 'text/html'});
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = 'portfolio.html';
            a.click();
            showToast('Portfolio exported', 'success');
        } catch(e) { showToast('Error exporting', 'error'); }
    });

    // --- E2: GITHUB ANALYZER ---
    document.getElementById('btn-analyze-gh').addEventListener('click', async () => {
        const username = document.getElementById('gh-username').value;
        if(!username) return;
        const btn = document.getElementById('btn-analyze-gh');
        btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i>';
        
        try {
            const res = await apiFetch('/analyze/github', {
                method: 'POST',
                headers: {'Content-Type':'application/json'},
                body: JSON.stringify({username})
            });
            const data = await res.json();
            
            document.getElementById('gh-results').style.display = 'grid';
            document.getElementById('gh-score').innerText = Math.round(data.repository_score);
            document.getElementById('gh-recs').innerHTML = data.recommendations.map(r=>`<li><i class="fa-solid fa-lightbulb text-warning" style="margin-right:8px; color:var(--accent-warning);"></i>${r}</li>`).join('');
            showToast('Analysis complete', 'success');
        } catch(e) { showToast('Analysis failed', 'error'); }
        btn.innerHTML = 'Analyze Profile';
    });

    // --- E3: LINKEDIN OPTIMIZER ---
    document.getElementById('btn-analyze-li').addEventListener('click', async () => {
        const url = document.getElementById('li-url').value;
        if(!url) return;
        const btn = document.getElementById('btn-analyze-li');
        btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i>';
        
        try {
            const res = await apiFetch('/analyze/linkedin', {
                method: 'POST',
                headers: {'Content-Type':'application/json'},
                body: JSON.stringify({profile_url: url})
            });
            const data = await res.json();
            
            document.getElementById('li-results').style.display = 'grid';
            document.getElementById('li-score').innerText = Math.round(data.strength_score);
            document.getElementById('li-recs').innerHTML = data.suggestions.map(r=>`<li><i class="fa-solid fa-arrow-trend-up" style="margin-right:8px; color:var(--accent-blue);"></i>${r}</li>`).join('');
            showToast('Optimization complete', 'success');
        } catch(e) { showToast('Analysis failed', 'error'); }
        btn.innerHTML = 'Optimize Profile';
    });

    // --- E4: JOB DISCOVERY ---
    async function loadJobs() {
        try {
            const res = await apiFetch('/jobs/recommended');
            const jobs = await res.json();
            const feed = document.getElementById('job-feed');
            feed.innerHTML = '';
            jobs.forEach(j => {
                feed.innerHTML += `
                    <div class="job-card">
                        <div style="display:flex; justify-content:space-between;">
                            <h3 style="color:var(--text-primary); margin-bottom:5px;">${j.title}</h3>
                            <span class="badge badge-green">${j.match_score}% Match</span>
                        </div>
                        <div style="color:var(--text-secondary); font-size:14px;"><i class="fa-solid fa-building"></i> ${j.company}</div>
                        <div style="color:var(--text-secondary); font-size:14px;"><i class="fa-solid fa-money-bill"></i> ${j.salary}</div>
                        <button class="btn btn-primary" style="margin-top:10px; width:100%; justify-content:center;">Apply via ATS</button>
                    </div>
                `;
            });
        } catch(e){}
    }

    // --- E5: MENTOR CONNECT ---
    async function loadMentors() {
        try {
            const res = await apiFetch('/mentors');
            const mentors = await res.json();
            const feed = document.getElementById('mentor-feed');
            feed.innerHTML = '';
            mentors.forEach(m => {
                feed.innerHTML += `
                    <div class="mentor-card">
                        <div class="mentor-avatar"><i class="fa-solid fa-user-tie" style="color:white;"></i></div>
                        <h3 style="margin-bottom:5px;">Mentor #${m.id.substring(0,4)}</h3>
                        <p style="color:var(--accent-cyan); font-size:13px; margin-bottom:10px;">${m.expertise}</p>
                        <p style="color:var(--text-secondary); font-size:12px; margin-bottom:15px;">${m.bio}</p>
                        <button class="btn btn-outline" style="width:100%; justify-content:center;" onclick="bookMentor('${m.id}')">Book Session</button>
                    </div>
                `;
            });
        } catch(e){}
    }
    
    window.bookMentor = async function(id) {
        try {
            await apiFetch(`/mentors/${id}/book`, {method:'POST'});
            showToast('Session Booked! Check notifications.', 'success');
        } catch(e){ showToast('Booking failed', 'error'); }
    }

    // --- E6: COMMUNITY HUB ---
    async function loadCommunity() {
        try {
            const res = await apiFetch('/community/posts');
            const posts = await res.json();
            const feed = document.getElementById('comm-feed');
            feed.innerHTML = '';
            posts.forEach(p => {
                feed.innerHTML += `
                    <div style="padding:15px; background:rgba(0,0,0,0.2); border-radius:var(--radius-sm); border:1px solid var(--border-color);">
                        <h4 style="margin-bottom:5px; color:var(--text-primary);">${p.title}</h4>
                        <div style="font-size:12px; color:var(--text-secondary); display:flex; gap:15px;">
                            <span><i class="fa-solid fa-user"></i> ${p.author || 'User'}</span>
                            <span><i class="fa-solid fa-heart" style="color:var(--accent-pink);"></i> ${p.likes}</span>
                        </div>
                    </div>
                `;
            });
        } catch(e){}
    }

    document.getElementById('btn-post').addEventListener('click', async () => {
        const title = document.getElementById('comm-title').value;
        const content = document.getElementById('comm-content').value;
        try {
            await apiFetch('/community/posts', {
                method:'POST',
                headers:{'Content-Type':'application/json'},
                body: JSON.stringify({title, content, category:'Discussion'})
            });
            showToast('Post published', 'success');
            document.getElementById('comm-title').value = '';
            document.getElementById('comm-content').value = '';
            loadCommunity();
        } catch(e) {}
    });

    // --- E8: AI INSIGHTS ---
    async function loadInsights() {
        try {
            const res = await apiFetch('/insights');
            const data = await res.json();
            
            document.getElementById('insight-advice').innerText = data.advice;
            document.getElementById('insight-skills').innerHTML = data.emerging_skills.map(s=>`<span class="badge badge-purple">${s}</span>`).join('');

            const ctx = document.getElementById('chart-radar');
            if(window.radarChart) window.radarChart.destroy();
            window.radarChart = new Chart(ctx, {
                type: 'radar',
                data: {
                    labels: ['Market Demand', 'Readiness', 'Skill Trend', 'Leadership', 'Risk Mitigation'],
                    datasets: [{
                        label: 'Career Score',
                        data: [data.market_demand_score, data.promotion_readiness, 85, 60, 100 - data.career_risk],
                        backgroundColor: 'rgba(139, 92, 246, 0.2)',
                        borderColor: '#8b5cf6',
                        pointBackgroundColor: '#8b5cf6'
                    }]
                },
                options: { scales: { r: { angleLines: {color: 'rgba(255,255,255,0.1)'}, grid: {color: 'rgba(255,255,255,0.1)'}, pointLabels: {color: '#94a3b8'} } }, plugins: { legend: {display:false} } }
            });
        } catch(e){}
    }

    // --- E7: NOTIFICATIONS ---
    document.getElementById('notif-btn').addEventListener('click', async () => {
        const panel = document.getElementById('notif-panel');
        if(panel.style.display === 'block') { panel.style.display = 'none'; return; }
        
        panel.style.display = 'block';
        try {
            const res = await apiFetch('/notifications');
            const notifs = await res.json();
            const list = document.getElementById('notif-list');
            list.innerHTML = '';
            notifs.forEach(n => {
                let icon = 'fa-bell';
                let col = 'var(--accent-blue)';
                if(n.type === 'job_match') { icon='fa-briefcase'; col='var(--accent-green)'; }
                if(n.type === 'mentor_alert') { icon='fa-user-tie'; col='var(--accent-purple)'; }
                
                list.innerHTML += `
                    <div style="display:flex; gap:15px; align-items:flex-start; padding:10px; background:rgba(0,0,0,0.2); border-radius:var(--radius-sm);">
                        <i class="fa-solid ${icon}" style="color:${col}; margin-top:3px;"></i>
                        <div style="font-size:13px; line-height:1.4;">${n.message}</div>
                    </div>
                `;
            });
        } catch(e){}
    });

    // Initial Load
    loadDashboard();
});
