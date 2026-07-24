/**
 * saas-dashboard.js
 * Handles Enterprise Admin UI interactions.
 */

document.addEventListener('DOMContentLoaded', () => {
    
    // --- View Routing ---
    const menuItems = document.querySelectorAll('.sidebar-menu li[data-view]');
    const views = document.querySelectorAll('.view-section');
    
    menuItems.forEach(item => {
        item.addEventListener('click', () => {
            // Update active states in menu
            menuItems.forEach(m => m.classList.remove('active'));
            item.classList.add('active');
            
            // Show corresponding view
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

    // --- Tenant Switcher ---
    const tenantSelect = document.getElementById('tenant-select');
    const modalProvision = document.getElementById('modal-provision');
    const btnProvCancel = document.getElementById('btn-prov-cancel');
    const btnProvSubmit = document.getElementById('btn-prov-submit');
    
    tenantSelect.addEventListener('change', (e) => {
        if (e.target.value === 'new') {
            modalProvision.classList.remove('hidden');
            // reset select to previous value visually
            tenantSelect.selectedIndex = 0;
        } else {
            // Mock tenant switch logic
            document.querySelector('.header-action h2').textContent = e.target.options[e.target.selectedIndex].text + " Overview";
            fetchAnalytics(e.target.value);
        }
    });
    
    btnProvCancel.addEventListener('click', () => {
        modalProvision.classList.add('hidden');
    });
    
    btnProvSubmit.addEventListener('click', async () => {
        const name = document.getElementById('prov-name').value;
        const domain = document.getElementById('prov-domain').value;
        if (!name) return alert("Organization name required.");
        
        try {
            const res = await fetch('/api/saas/tenants', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ name, domain })
            });
            if (res.ok) {
                const data = await res.json();
                const option = document.createElement('option');
                option.value = data.id;
                option.text = data.name;
                // Insert before the "New" option
                tenantSelect.add(option, tenantSelect.options[tenantSelect.options.length - 1]);
                tenantSelect.value = data.id;
                modalProvision.classList.add('hidden');
                alert("Workspace Provisioned Successfully.");
            }
        } catch(e) {
            console.error(e);
            alert("Error provisioning workspace. Ensure backend is running.");
            modalProvision.classList.add('hidden');
        }
    });

    // --- Analytics / AI Optimizer ---
    const btnRefresh = document.getElementById('btn-refresh-analytics');
    const aiText = document.getElementById('ai-optimization-text');
    
    const fetchAnalytics = async (tenantId = "tenant_1") => {
        aiText.textContent = "Analyzing usage patterns...";
        try {
            const res = await fetch('/api/saas/analytics', {
                headers: { 'X-Tenant-ID': tenantId }
            });
            if (res.ok) {
                const data = await res.json();
                aiText.innerHTML = `
                    <strong>Predicted Spend:</strong> $${data.predicted_cost_usd} <br>
                    <strong>Recommendation:</strong> ${data.optimization_recommendation}
                `;
            } else {
                throw new Error("Backend error");
            }
        } catch (e) {
            aiText.textContent = "Mock: Consider upgrading to the Enterprise tier; your API Gateway bandwidth is frequently maxing out.";
        }
    };
    
    btnRefresh.addEventListener('click', () => fetchAnalytics(tenantSelect.value));
    
    // Initial fetch
    setTimeout(fetchAnalytics, 1000);

    // --- API Key Generation ---
    const btnCreateKey = document.getElementById('btn-create-key');
    const tbody = document.getElementById('api-key-list');
    
    btnCreateKey.addEventListener('click', async () => {
        const keyName = prompt("Enter a name for the new API Key (e.g. 'Staging Env'):");
        if (!keyName) return;
        
        try {
            const res = await fetch('/api/saas/apikeys', {
                method: 'POST',
                headers: { 
                    'Content-Type': 'application/json',
                    'X-Tenant-ID': tenantSelect.value
                },
                body: JSON.stringify({ name: keyName })
            });
            
            if (res.ok) {
                const data = await res.json();
                
                // Show raw key once
                alert(`IMPORTANT: Copy your key now. It will not be shown again.\n\n${data.api_key}`);
                
                // Add to table mock
                const tr = document.createElement('tr');
                tr.innerHTML = `
                    <td>${keyName}</td>
                    <td>${data.api_key.substring(0, 10)}...</td>
                    <td>${new Date().toISOString().split('T')[0]}</td>
                    <td><span class="badge badge-success">Active</span></td>
                    <td><button class="btn btn-danger btn-sm">Revoke</button></td>
                `;
                tbody.appendChild(tr);
            }
        } catch (e) {
            console.error("API error", e);
            alert("Error connecting to backend.");
        }
    });

});
