/**
 * RESUMESPHERE AI - TALENT INTELLIGENCE DASHBOARD JS (Phase G)
 */

document.addEventListener('DOMContentLoaded', () => {
    
    // --- STATE & AUTH ---
    let jwtToken = localStorage.getItem('rs_cloud_token'); // Shared token for admin
    const API = '/api/talent';

    if(!jwtToken) {
        alert("Access Denied: Enterprise Admin token required. Redirecting to Cloud Auth.");
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
        if(res.status === 401) {
            window.location.href = "cloud-dashboard.html";
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
            document.getElementById('page-title').innerText = item.innerText;
            
            // Lazy loaders
            if(targetId === 'module-g8') loadDashboard();
            if(targetId === 'module-g1') loadGraph();
            if(targetId === 'module-g3') loadPredictive();
            if(targetId === 'module-g5') loadSkills();
            if(targetId === 'module-g6') loadHeatmap();
        });
    });

    // --- G8: DASHBOARD ---
    async function loadDashboard() {
        try {
            const res = await apiFetch('/dashboard');
            const data = await res.json();
            
            document.getElementById('dash-active').innerText = data.active_candidates;
            document.getElementById('dash-reqs').innerText = data.open_requisitions;
            document.getElementById('dash-match').innerText = data.ai_match_efficiency + '%';
            document.getElementById('dash-cph').innerText = data.cost_per_hire;

            renderVelocityChart();
            renderDiversityChart(data.diversity_index);
        } catch(e){}
    }

    function renderVelocityChart() {
        const ctx = document.getElementById('chart-velocity');
        if(window.velChart) window.velChart.destroy();
        Chart.defaults.color = '#888';
        window.velChart = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: ['Q1', 'Q2', 'Q3', 'Q4'],
                datasets: [{
                    label: 'Hires',
                    data: [12, 19, 15, 25],
                    backgroundColor: 'rgba(251, 191, 36, 0.8)',
                    borderRadius: 4
                }]
            },
            options: { plugins:{legend:{display:false}} }
        });
    }

    function renderDiversityChart(val) {
        const ctx = document.getElementById('chart-diversity');
        if(window.divChart) window.divChart.destroy();
        window.divChart = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: ['Index', 'Gap'],
                datasets: [{
                    data: [val, 100-val],
                    backgroundColor: ['#10b981', '#333'],
                    borderWidth:0
                }]
            },
            options: { cutout:'80%', plugins:{legend:{display:false}} }
        });
    }

    // --- G1: GRAPH ---
    document.getElementById('g1-refresh').addEventListener('click', loadGraph);
    async function loadGraph() {
        try {
            const res = await apiFetch('/graph');
            const data = await res.json();
            const container = document.getElementById('network-container');
            
            const nodes = new vis.DataSet(data.nodes.map(n => ({
                id: n.id, label: n.label, 
                color: n.group==='skill'?'#fbbf24':n.group==='candidate'?'#3b82f6':'#f43f5e',
                font: {color: '#fff'}
            })));
            const edges = new vis.DataSet(data.edges.map(e => ({
                from: e.from, to: e.to, label: e.label,
                font: {color: '#888', size:10}, color: '#333'
            })));
            
            new vis.Network(container, {nodes, edges}, {physics: {stabilization: false}});
            showToast('Graph synchronized.');
        } catch(e){}
    }

    // --- G2: RANKING ---
    document.getElementById('g2-rank-btn').addEventListener('click', async () => {
        const role = document.getElementById('g2-role').value || 'Developer';
        document.getElementById('g2-results-container').innerHTML = '<div style="text-align:center; padding:20px; color:#fbbf24;"><i class="fa-solid fa-circle-notch fa-spin"></i> Running ML Model...</div>';
        
        try {
            const res = await apiFetch('/ranking', {
                method:'POST', headers:{'Content-Type':'application/json'},
                body: JSON.stringify({job_role: role})
            });
            const ranks = await res.json();
            let html = '';
            ranks.forEach((r, idx) => {
                html += `
                    <div class="ranking-row">
                        <div style="display:flex; align-items:center; gap:15px;">
                            <div style="font-size:1.5rem; color:var(--text-secondary); width:30px;">#${idx+1}</div>
                            <div>
                                <div style="font-weight:600; font-size:1.1rem;">${r.name}</div>
                                <div style="font-size:12px; color:var(--text-secondary);">Confidence: ${r.confidence}%</div>
                            </div>
                        </div>
                        <div class="score-badge">${r.match_score}% Match</div>
                    </div>
                `;
            });
            document.getElementById('g2-results-container').innerHTML = html;
        } catch(e){}
    });

    // --- G3: PREDICTIVE ---
    async function loadPredictive() {
        try {
            const res = await apiFetch('/predict');
            const data = await res.json();
            document.getElementById('g3-ttf').innerText = data.time_to_fill_days + ' Days';
            document.getElementById('g3-offer').innerText = data.offer_acceptance_probability + '%';
            document.getElementById('g3-risk').innerText = data.flight_risk_candidates;
            document.getElementById('g3-rec').innerHTML = `<i class="fa-solid fa-lightbulb" style="color:var(--accent-emerald);"></i> ${data.recommended_action}`;
        } catch(e){}
    }

    // --- G4: SALARY ---
    document.getElementById('g4-btn').addEventListener('click', async () => {
        const role = document.getElementById('g4-role').value;
        const loc = document.getElementById('g4-loc').value;
        try {
            const res = await apiFetch(`/salary?role=${encodeURIComponent(role)}&location=${encodeURIComponent(loc)}`);
            const data = await res.json();
            document.getElementById('g4-result').style.display = 'block';
            
            document.getElementById('g4-min').innerText = '$' + (data.min_salary/1000).toFixed(0) + 'k';
            document.getElementById('g4-avg').innerText = '$' + (data.average_salary/1000).toFixed(0) + 'k';
            document.getElementById('g4-max').innerText = '$' + (data.max_salary/1000).toFixed(0) + 'k';
        } catch(e){}
    });

    // --- G5: SKILLS ---
    async function loadSkills() {
        try {
            const res = await apiFetch('/skills');
            const data = await res.json();
            document.getElementById('g5-up').innerHTML = data.trending_up.map(s=>`<li>${s}</li>`).join('');
            document.getElementById('g5-down').innerHTML = data.trending_down.map(s=>`<li>${s}</li>`).join('');
            document.getElementById('g5-gaps').innerHTML = data.critical_gaps_in_org.map(s=>`<li>${s}</li>`).join('');
        } catch(e){}
    }

    // --- G6: HEATMAP ---
    async function loadHeatmap() {
        try {
            const res = await apiFetch('/heatmap');
            const data = await res.json();
            const grid = document.getElementById('g6-heat');
            grid.innerHTML = '';
            data.forEach(d => {
                // Calculate color intensity
                const alpha = d.talent_density / 100;
                grid.innerHTML += `
                    <div class="heatmap-cell" style="background:rgba(251, 191, 36, ${alpha}); border:1px solid rgba(251, 191, 36, ${alpha+0.2})">
                        <div style="font-size:1.5rem; margin-bottom:5px;">${d.talent_density}</div>
                        <div style="font-size:12px; font-weight:400;">${d.region}</div>
                    </div>
                `;
            });
        } catch(e){}
    }

    // --- G7: WORKFORCE ---
    document.getElementById('g7-btn').addEventListener('click', async () => {
        const payload = {
            department: document.getElementById('g7-dept').value,
            forecasted_hires: parseInt(document.getElementById('g7-hires').value),
            target_quarter: document.getElementById('g7-q').value,
            budget: parseInt(document.getElementById('g7-budget').value)
        };
        try {
            await apiFetch('/workforce', {
                method:'POST', headers:{'Content-Type':'application/json'},
                body: JSON.stringify(payload)
            });
            showToast('Workforce Plan successfully submitted.');
        } catch(e){}
    });

    // Initial Load
    loadDashboard();
});
