/**
 * RESUMESPHERE AI - LEARNING PLATFORM JS (Phase H)
 */

document.addEventListener('DOMContentLoaded', () => {
    
    // --- STATE & AUTH ---
    let jwtToken = localStorage.getItem('rs_cloud_token'); // Shared token
    const API = '/api/learning';

    if(!jwtToken) {
        alert("Access Denied: Please authenticate via Global Cloud first.");
        window.location.href = "cloud-dashboard.html";
        return;
    }

    const toastContainer = document.getElementById('toast-container');
    const navItems = document.querySelectorAll('.nav-item');
    const modules = document.querySelectorAll('.module');

    function showToast(message, type = 'info') {
        const t = document.createElement('div');
        t.className = `toast`;
        t.innerHTML = `<i class="fa-solid fa-info-circle"></i> <span>${message}</span>`;
        toastContainer.appendChild(t);
        setTimeout(() => t.classList.add('show'), 10);
        setTimeout(() => { t.classList.remove('show'); setTimeout(()=>t.remove(), 300); }, 3000);
    }

    async function apiFetch(endpoint, options = {}) {
        if(!options.headers) options.headers = {};
        options.headers['Authorization'] = `Bearer ${jwtToken}`;
        const res = await fetch(`${API}${endpoint}`, options);
        if(res.status === 401) window.location.href = "cloud-dashboard.html";
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
            document.getElementById('page-title').innerText = item.innerText;
            
            // Lazy Loaders
            if(targetId === 'module-h9') loadLeaderboard();
            if(targetId === 'module-h2') loadCourses();
            if(targetId === 'module-h6') loadAnalytics();
            if(targetId === 'module-h7') loadGroups();
        });
    });

    // --- H9: Gamification & Leaderboard ---
    async function loadLeaderboard() {
        try {
            const res = await apiFetch('/leaderboard');
            const data = await res.json();
            
            document.getElementById('h9-xp').innerText = data.my_stats.xp;
            document.getElementById('h9-lvl').innerText = data.my_stats.level;
            document.getElementById('h9-streak').innerText = data.my_stats.streak;
            document.getElementById('top-streak').innerText = data.my_stats.streak;
            
            const tbody = document.getElementById('h9-lb');
            tbody.innerHTML = '';
            data.top_users.forEach((u, i) => {
                const isMe = u.name === localStorage.getItem('rs_cloud_user');
                tbody.innerHTML += `
                    <tr style="${isMe ? 'background:rgba(139, 92, 246, 0.1);' : ''} border-bottom:1px solid var(--border-color);">
                        <td style="padding:10px;">#${i+1}</td>
                        <td style="padding:10px; font-weight:${isMe?'bold':'normal'};">${u.name} ${isMe?'(You)':''}</td>
                        <td style="padding:10px;">Lvl ${u.level}</td>
                        <td style="padding:10px; color:var(--accent-primary); font-weight:600;">${u.xp} XP</td>
                    </tr>
                `;
            });
        } catch(e){}
    }

    // --- H1: AI Course Generator ---
    document.getElementById('h1-btn').addEventListener('click', async () => {
        const role = document.getElementById('h1-role').value;
        const skills = document.getElementById('h1-skills').value;
        const stat = document.getElementById('h1-status');
        stat.innerHTML = '<i class="fa-solid fa-spinner fa-spin" style="font-size:3rem; margin-bottom:15px; color:var(--accent-warning);"></i><p>Compiling curriculum...</p>';
        
        try {
            await apiFetch('/generate-path', {
                method:'POST', headers:{'Content-Type':'application/json'},
                body: JSON.stringify({target_role:role, current_skills:skills})
            });
            stat.innerHTML = '<i class="fa-solid fa-check-circle" style="font-size:3rem; margin-bottom:15px; color:var(--accent-success);"></i><p>Enrolled Successfully!</p>';
            showToast('Course generated & enrolled', 'success');
        } catch(e){}
    });

    // --- H2: Course Management ---
    async function loadCourses() {
        try {
            const res = await apiFetch('/courses');
            const data = await res.json();
            const grid = document.getElementById('h2-grid');
            grid.innerHTML = '';
            data.forEach(c => {
                grid.innerHTML += `
                    <div class="course-card">
                        <div class="course-img"><i class="fa-solid fa-book-open"></i></div>
                        <div class="course-body">
                            <h4 style="margin-bottom:5px;">${c.title}</h4>
                            <div style="font-size:12px; color:var(--text-secondary); margin-bottom:10px;">${c.category} • ${c.difficulty}</div>
                            <div class="progress-bg"><div class="progress-fill" style="width: ${Math.floor(Math.random()*80)}%;"></div></div>
                            <button class="btn btn-primary" style="width:100%; justify-content:center; margin-top:10px;">Continue</button>
                        </div>
                    </div>
                `;
            });
        } catch(e){}
    }

    // --- H3: Interactive Coding Lab ---
    document.getElementById('h3-run').addEventListener('click', async () => {
        const code = document.getElementById('h3-code').value;
        const term = document.getElementById('h3-term');
        term.innerText = "$ Executing in secure sandbox...\n";
        term.classList.remove('error');
        
        try {
            const res = await apiFetch('/execute-code', {
                method:'POST', headers:{'Content-Type':'application/json'},
                body: JSON.stringify({language:'python', code, lesson_id:'mock'})
            });
            const data = await res.json();
            if(data.status === 'success') {
                term.innerText += `> ${data.output}\n\nExecution Time: ${data.execution_time_ms}ms\nAI Review: ${data.ai_review}`;
                showToast('+50 XP Earned', 'success');
            } else {
                term.classList.add('error');
                term.innerText += `> ${data.output}\n\nAI Review: ${data.ai_review}`;
            }
        } catch(e){}
    });

    // --- H4: Quiz Engine ---
    window.selectOpt = function(el) {
        document.querySelectorAll('.quiz-option').forEach(o => o.classList.remove('selected'));
        el.classList.add('selected');
    }
    document.getElementById('h4-submit').addEventListener('click', async () => {
        const sel = document.querySelector('.quiz-option.selected');
        if(!sel) return;
        
        try {
            const res = await apiFetch('/quiz/evaluate', {
                method:'POST', headers:{'Content-Type':'application/json'},
                body: JSON.stringify({quiz_id:'q1', answers:{'q1': sel.innerText}})
            });
            const data = await res.json();
            const fb = document.getElementById('h4-feedback');
            fb.style.display = 'block';
            fb.style.background = data.passed ? 'rgba(16, 185, 129, 0.1)' : 'rgba(239, 68, 68, 0.1)';
            fb.style.borderColor = data.passed ? 'rgba(16, 185, 129, 0.3)' : 'rgba(239, 68, 68, 0.3)';
            fb.innerHTML = `<h4 style="color:${data.passed?'#34d399':'#f87171'}; margin-bottom:5px;">Score: ${data.score}%</h4><p>${data.feedback}</p>`;
        } catch(e){}
    });

    // --- H5: Certification ---
    window.verifyCert = async function(cid) {
        try {
            const res = await apiFetch(`/certificate/${cid}`);
            const data = await res.json();
            const resDiv = document.getElementById('h5-result');
            resDiv.style.display = 'block';
            resDiv.innerHTML = `
                <h4 style="color:var(--accent-success); margin-bottom:10px;"><i class="fa-solid fa-check-circle"></i> Digital Credential Verified</h4>
                <div style="font-size:13px; line-height:1.6; color:var(--text-secondary);">
                    <div><strong>ID:</strong> ${data.verification_id}</div>
                    <div><strong>Student:</strong> ${data.student}</div>
                    <div><strong>Issued:</strong> ${new Date(data.issue_date).toLocaleDateString()}</div>
                </div>
            `;
        } catch(e){}
    }

    // --- H6: Analytics ---
    async function loadAnalytics() {
        try {
            const res = await apiFetch('/analytics');
            const data = await res.json();
            
            document.getElementById('h6-text').innerHTML = `
                <div style="margin-bottom:20px;">
                    <h4 style="color:var(--accent-primary);">Study Hours</h4>
                    <div style="font-size:2rem; font-weight:700;">${data.total_study_hours}h</div>
                </div>
                <div>
                    <h4 style="color:var(--accent-success);">Completion Rate</h4>
                    <div style="font-size:2rem; font-weight:700;">${data.completion_rate}%</div>
                </div>
            `;
            
            const ctx = document.getElementById('chart-analytics');
            if(window.anChart) window.anChart.destroy();
            Chart.defaults.color = '#94a3b8';
            window.anChart = new Chart(ctx, {
                type: 'line',
                data: {
                    labels: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
                    datasets: [{
                        label: 'Study Hours',
                        data: [2, 3, 1, 4, 2, 5, 3],
                        borderColor: '#8b5cf6',
                        tension: 0.4,
                        fill: true,
                        backgroundColor: 'rgba(139, 92, 246, 0.1)'
                    }]
                },
                options: { plugins:{legend:{display:false}} }
            });
        } catch(e){}
    }

    // --- H7: Study Groups ---
    async function loadGroups() {
        try {
            const res = await apiFetch('/groups');
            const groups = await res.json();
            const grid = document.getElementById('h7-grid');
            grid.innerHTML = '';
            groups.forEach(g => {
                grid.innerHTML += `
                    <div class="card" style="padding:20px;">
                        <h4 style="margin-bottom:5px;">${g.name}</h4>
                        <p style="color:var(--text-secondary); font-size:12px; margin-bottom:15px;">${g.description}</p>
                        <button class="btn btn-outline" style="width:100%; justify-content:center;">Join Discussion</button>
                    </div>
                `;
            });
        } catch(e){}
    }

    // --- H8: Copilot ---
    document.getElementById('h8-btn').addEventListener('click', async () => {
        const inp = document.getElementById('h8-input');
        const q = inp.value;
        if(!q) return;
        
        const chat = document.getElementById('h8-chat');
        chat.innerHTML += `<div style="background:rgba(255,255,255,0.05); padding:15px; border-radius:8px; align-self:flex-end; max-width:80%; border:1px solid var(--border-color);">${q}</div>`;
        inp.value = '';
        
        try {
            const res = await apiFetch('/ask-copilot', {
                method:'POST', headers:{'Content-Type':'application/json'},
                body: JSON.stringify({question:q, context:'General Study'})
            });
            const data = await res.json();
            chat.innerHTML += `<div style="background:rgba(139, 92, 246, 0.1); padding:15px; border-radius:8px; border:1px solid rgba(139, 92, 246, 0.3); max-width:80%;">${data.answer}</div>`;
            chat.scrollTop = chat.scrollHeight;
        } catch(e){}
    });

    // Init
    loadLeaderboard();
});
