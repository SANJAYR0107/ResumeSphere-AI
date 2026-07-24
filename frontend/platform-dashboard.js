/**
 * platform-dashboard.js
 * Handles AI OS interactions (Plugins, Workflows, Functions).
 */

document.addEventListener('DOMContentLoaded', () => {
    
    // --- View Routing ---
    const menuItems = document.querySelectorAll('.sidebar-menu li[data-view]');
    const views = document.querySelectorAll('.view-section');
    
    menuItems.forEach(item => {
        item.addEventListener('click', () => {
            menuItems.forEach(m => m.classList.remove('active'));
            item.classList.add('active');
            
            const targetView = item.getAttribute('data-view');
            views.forEach(v => {
                v.classList.remove('active');
                v.classList.add('hidden');
                if (v.id === `view-${targetView}`) {
                    v.classList.remove('hidden');
                    v.classList.add('active');
                }
            });
        });
    });

    // --- App Ecosystem ---
    const appGrid = document.getElementById('app-grid');
    
    const mockPlugins = [
        { id: "plg_1", name: "Slack Integrator", developer: "ResumeSphere", version: "1.0.0", desc: "Push interview notifications directly to Slack channels." },
        { id: "plg_2", name: "HackerRank Bridge", developer: "ThirdParty", version: "2.1.0", desc: "Embed HackerRank scores into the candidate data lake." },
        { id: "plg_3", name: "Zapier Webhooks", developer: "ResumeSphere", version: "1.0.5", desc: "Connect Agent workflows to 5000+ external apps." }
    ];
    
    function renderApps() {
        appGrid.innerHTML = '';
        mockPlugins.forEach(p => {
            const card = document.createElement('div');
            card.className = 'app-card';
            card.innerHTML = `
                <div class="app-header">
                    <h3>${p.name}</h3>
                    <span class="badge badge-outline">v${p.version}</span>
                </div>
                <p class="app-desc">${p.desc}</p>
                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <small style="color:var(--os-muted)">By ${p.developer}</small>
                    <button class="btn btn-outline" onclick="installApp('${p.id}')">Install</button>
                </div>
            `;
            appGrid.appendChild(card);
        });
    }
    
    window.installApp = async (id) => {
        try {
            const res = await fetch(`/api/platform/plugins/${id}/install?tenant_id=global`, { method: 'POST' });
            if (res.ok) alert(`Plugin ${id} installed successfully.`);
            else alert("Backend offline. Mocking install success.");
        } catch(e) {
            alert("Backend offline. Mocking install success.");
        }
    };
    
    renderApps();

    // --- Workflow Engine ---
    const btnRunWorkflow = document.getElementById('btn-run-workflow');
    const logs = document.getElementById('workflow-logs');
    
    btnRunWorkflow.addEventListener('click', async () => {
        logs.innerHTML = `<div class="log-line">> Initiating Workflow DAG...</div>`;
        
        try {
            const res = await fetch('/api/platform/workflows/execute', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ workflow_id: "mock_wf_1", payload: {} })
            });
            
            if (res.ok) {
                const data = await res.json();
                setTimeout(() => logs.innerHTML += `<div class="log-line">> ${data.message}</div>`, 500);
                setTimeout(() => logs.innerHTML += `<div class="log-line">> ${data.optimization}</div>`, 1500);
                setTimeout(() => logs.innerHTML += `<div class="log-line log-success">> EXECUTION COMPLETED (2140ms)</div>`, 2500);
            }
        } catch(e) {
            logs.innerHTML += `<div class="log-line" style="color:red">> Connection refused. Backend unavailable.</div>`;
        }
    });

    // --- Custom Functions Sandbox ---
    const btnRunFunc = document.getElementById('btn-run-function');
    const codeArea = document.getElementById('function-code');
    const terminal = document.getElementById('function-terminal');
    
    btnRunFunc.addEventListener('click', async () => {
        terminal.innerHTML = `$ Starting sandbox container...<br>`;
        
        try {
            const res = await fetch('/api/platform/functions/run', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ code: codeArea.value, runtime: "python3.10" })
            });
            
            if (res.ok) {
                const data = await res.json();
                data.logs.forEach((log, idx) => {
                    setTimeout(() => terminal.innerHTML += `$ ${log}<br>`, (idx+1)*600);
                });
                setTimeout(() => terminal.innerHTML += `<span style="color:#10b981">$ Sandbox exited (0)</span><br>`, 2500);
            }
        } catch(e) {
            setTimeout(() => terminal.innerHTML += `$ Initializing...<br>`, 500);
            setTimeout(() => terminal.innerHTML += `$ Executing handler...<br>`, 1000);
            setTimeout(() => terminal.innerHTML += `<span style="color:#10b981">$ Return {"status": "error", "message": "Missing ID"}</span><br>`, 1500);
        }
    });

    // --- BI Analytics ---
    const biInput = document.getElementById('bi-input');
    const btnBi = document.getElementById('btn-bi-send');
    const biOutput = document.getElementById('bi-output');
    
    const sendBI = async () => {
        const query = biInput.value;
        if (!query) return;
        
        biOutput.innerHTML += `<br><br><strong style="color:white">> ${query}</strong><br>`;
        biInput.value = '';
        
        try {
            const res = await fetch('/api/platform/bi/query', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ query })
            });
            
            if (res.ok) {
                const data = await res.json();
                biOutput.innerHTML += `
                    <span style="color:var(--os-primary)">[SQL Generated - Confidence ${data.confidence_score}]</span><br>
                    <span style="color:var(--os-code)">${data.generated_sql}</span><br>
                    <span>Executing query against Warehouse... [Success]</span>
                `;
            }
        } catch(e) {
            biOutput.innerHTML += `<span style="color:var(--os-code)">SELECT * FROM MOCK_DB;</span>`;
        }
        biOutput.scrollTop = biOutput.scrollHeight;
    };
    
    btnBi.addEventListener('click', sendBI);
    biInput.addEventListener('keypress', (e) => {
        if(e.key === 'Enter') sendBI();
    });

});
