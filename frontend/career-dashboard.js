/**
 * RESUMESPHERE AI - CAREER ASSISTANT DASHBOARD JS (Phase C)
 */

document.addEventListener('DOMContentLoaded', () => {
    // --- State & Config ---
    const API_BASE = '/api/career';

    // --- Core UI & Routing ---
    const navItems = document.querySelectorAll('.nav-item');
    const moduleSections = document.querySelectorAll('.module-section');
    const pageTitleDisplay = document.getElementById('page-title-display');
    const themeToggleBtn = document.getElementById('theme-toggle-btn');
    const toastContainer = document.getElementById('toast-container');

    // Routing Logic
    navItems.forEach(item => {
        item.addEventListener('click', (e) => {
            e.preventDefault();
            const targetId = item.getAttribute('data-target');
            if (!targetId) return;

            // Update active state in nav
            navItems.forEach(nav => nav.classList.remove('active'));
            item.classList.add('active');

            // Update title
            pageTitleDisplay.innerText = item.innerText;

            // Switch section
            moduleSections.forEach(sec => sec.classList.remove('active'));
            document.getElementById(targetId).classList.add('active');

            // Load data for specific modules when opened
            if (targetId === 'module-c9') loadC9Analytics();
            if (targetId === 'module-c8') loadC8Jobs();
        });
    });

    // Theme Toggle
    themeToggleBtn.addEventListener('click', () => {
        const currentTheme = document.documentElement.getAttribute('data-theme');
        const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
        document.documentElement.setAttribute('data-theme', newTheme);
        themeToggleBtn.innerHTML = newTheme === 'dark' ? '<i class="fa-solid fa-moon"></i>' : '<i class="fa-solid fa-sun"></i>';
        
        // Re-render charts for new theme
        if(document.getElementById('module-c9').classList.contains('active')) {
            loadC9Analytics();
        }
    });

    // Toast Utility
    window.showToast = function(message, type = 'info') {
        const toast = document.createElement('div');
        toast.className = `toast toast-${type}`;
        
        let icon = 'fa-info-circle';
        if(type === 'success') icon = 'fa-check-circle';
        if(type === 'error') icon = 'fa-exclamation-circle';
        
        toast.innerHTML = `<i class="fa-solid ${icon}"></i> <span>${message}</span>`;
        toastContainer.appendChild(toast);
        
        // Trigger reflow for animation
        setTimeout(() => toast.classList.add('show'), 10);
        
        setTimeout(() => {
            toast.classList.remove('show');
            setTimeout(() => toast.remove(), 300);
        }, 3000);
    };

    // Helper: Show loader in a container
    function showSkeleton(containerId) {
        document.getElementById(containerId).innerHTML = '<div style="height: 100px; width:100%" class="skeleton"></div>'.repeat(3);
        document.getElementById(containerId).style.display = 'block';
    }


    /* =================================================================
       MODULE C1: AI Career Coach
       ================================================================= */
    document.getElementById('c1-generate-btn').addEventListener('click', async () => {
        const targetRole = document.getElementById('c1-target-role').value;
        const resumeSkills = document.getElementById('c1-resume-skills').value.split(',').map(s => s.trim());
        
        if (!targetRole) return showToast('Please enter a target role', 'error');

        const btn = document.getElementById('c1-generate-btn');
        btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Generating...';
        btn.disabled = true;

        try {
            const res = await fetch(`${API_BASE}/coach`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ target_role: targetRole, resume_skills: resumeSkills })
            });
            const data = await res.json();
            
            const timelineContainer = document.getElementById('c1-timeline');
            timelineContainer.innerHTML = '';
            
            if(data.roadmap && data.roadmap.phases) {
                data.roadmap.phases.forEach((phase, index) => {
                    timelineContainer.innerHTML += `
                        <div class="glass-card" style="position:relative;">
                            <span class="badge badge-purple" style="position:absolute; top:-10px; left:20px;">Month ${phase.month || (index+1)}</span>
                            <h3 style="margin-top:10px;">${phase.focus_area || 'Phase Focus'}</h3>
                            <ul style="margin-top:10px; color:var(--text-secondary); padding-left:15px;">
                                ${phase.goals ? phase.goals.map(g => `<li>${g}</li>`).join('') : '<li>No goals specified</li>'}
                            </ul>
                        </div>
                    `;
                });
            } else {
                timelineContainer.innerHTML = '<p>Generated successfully, but could not parse roadmap phases.</p>';
            }
            document.getElementById('c1-results').style.display = 'block';
            showToast('Roadmap generated successfully', 'success');
        } catch (e) {
            showToast('Failed to generate roadmap', 'error');
            console.error(e);
        } finally {
            btn.innerHTML = '<i class="fa-solid fa-magic"></i> Generate Roadmap';
            btn.disabled = false;
        }
    });

    /* =================================================================
       MODULE C2: Chat Assistant
       ================================================================= */
    const chatInput = document.getElementById('chat-input');
    const chatHistory = document.getElementById('chat-history');
    
    function appendChatMessage(text, sender) {
        const msgDiv = document.createElement('div');
        msgDiv.style.maxWidth = '80%';
        msgDiv.style.padding = '12px 18px';
        msgDiv.style.borderRadius = 'var(--radius-md)';
        msgDiv.style.marginBottom = '10px';
        
        if (sender === 'user') {
            msgDiv.style.alignSelf = 'flex-end';
            msgDiv.style.background = 'var(--accent-blue)';
            msgDiv.style.color = '#fff';
            msgDiv.innerText = text;
        } else {
            msgDiv.style.alignSelf = 'flex-start';
            msgDiv.style.background = 'rgba(255,255,255,0.05)';
            msgDiv.style.border = '1px solid var(--border-color)';
            msgDiv.innerHTML = marked.parse(text); // Use marked to parse markdown
        }
        
        chatHistory.appendChild(msgDiv);
        chatHistory.scrollTop = chatHistory.scrollHeight;
    }

    document.getElementById('chat-send-btn').addEventListener('click', async () => {
        const query = chatInput.value.trim();
        if (!query) return;
        
        appendChatMessage(query, 'user');
        chatInput.value = '';
        
        const loaderId = 'chat-loader-' + Date.now();
        const loaderHTML = `<div id="${loaderId}" style="align-self: flex-start; color: var(--text-secondary);"><i class="fa-solid fa-ellipsis fa-fade"></i> AI is typing...</div>`;
        chatHistory.insertAdjacentHTML('beforeend', loaderHTML);
        chatHistory.scrollTop = chatHistory.scrollHeight;

        try {
            const res = await fetch(`${API_BASE}/chat`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ 
                    query: query,
                    resume_skills: ["Python", "JavaScript", "React"],
                    ats_score: 85,
                    missing_skills: ["AWS", "Docker"],
                    target_role: "Full Stack Developer"
                })
            });
            const data = await res.json();
            document.getElementById(loaderId).remove();
            appendChatMessage(data.response || 'Sorry, I could not generate a response.', 'ai');
        } catch (e) {
            document.getElementById(loaderId).remove();
            appendChatMessage('An error occurred connecting to the assistant.', 'ai');
        }
    });

    chatInput.addEventListener('keypress', (e) => {
        if(e.key === 'Enter') document.getElementById('chat-send-btn').click();
    });


    /* =================================================================
       MODULE C3: Cover Letter
       ================================================================= */
    document.getElementById('c3-generate-btn').addEventListener('click', async () => {
        const company = document.getElementById('c3-company').value || "Tech Corp";
        const role = document.getElementById('c3-role').value || "Software Engineer";
        const jd = document.getElementById('c3-jd').value;
        
        const btn = document.getElementById('c3-generate-btn');
        btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Generating...';
        btn.disabled = true;

        try {
            const res = await fetch(`${API_BASE}/cover-letter/generate`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    candidate_name: "John Doe",
                    target_role: role,
                    company_name: company,
                    experience_type: "Experienced",
                    resume_skills: ["Python", "FastAPI", "JavaScript", "React"],
                    jd_text: jd
                })
            });
            const data = await res.json();
            document.getElementById('c3-result-editor').value = data.cover_letter || "Generation failed.";
            showToast('Cover letter generated', 'success');
        } catch (e) {
            showToast('Failed to generate cover letter', 'error');
        } finally {
            btn.innerHTML = '<i class="fa-solid fa-magic"></i> Generate';
            btn.disabled = false;
        }
    });

    document.getElementById('c3-copy-btn').addEventListener('click', () => {
        const text = document.getElementById('c3-result-editor').value;
        if (!text) return;
        navigator.clipboard.writeText(text);
        showToast('Copied to clipboard', 'success');
    });

    document.getElementById('c3-clear-btn').addEventListener('click', () => {
        document.getElementById('c3-company').value = '';
        document.getElementById('c3-role').value = '';
        document.getElementById('c3-jd').value = '';
        document.getElementById('c3-result-editor').value = '';
    });
    
    // PDF Download for C3 using html2pdf since generating from backend might need proper auth/setup
    // But backend provides an endpoint, let's use the backend endpoint if possible.
    document.getElementById('c3-pdf-btn').addEventListener('click', async () => {
        const text = document.getElementById('c3-result-editor').value;
        if (!text) return showToast('No content to download', 'error');
        
        showToast('Downloading PDF...', 'info');
        try {
            const res = await fetch(`${API_BASE}/cover-letter/download-pdf`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ cover_letter: text })
            });
            
            if(!res.ok) throw new Error("Network response was not ok");
            const blob = await res.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = 'Cover_Letter.pdf';
            document.body.appendChild(a);
            a.click();
            a.remove();
            showToast('Downloaded successfully', 'success');
        } catch(e) {
            console.error(e);
            showToast('Failed to download from server, generating client-side PDF', 'info');
            // Fallback to client-side PDF generation
            const element = document.createElement('div');
            element.innerHTML = `<div style="padding:40px; font-family:serif; line-height:1.6;">${text.replace(/\n/g, '<br>')}</div>`;
            html2pdf().from(element).save('Cover_Letter.pdf');
        }
    });


    /* =================================================================
       MODULE C4: Learning Roadmap
       ================================================================= */
    document.getElementById('c4-generate-btn').addEventListener('click', async () => {
        const skill = document.getElementById('c4-skill').value;
        if (!skill) return showToast('Enter a skill', 'error');

        const btn = document.getElementById('c4-generate-btn');
        btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i>';
        btn.disabled = true;

        showSkeleton('c4-tasks-container');
        document.getElementById('c4-results').style.display = 'block';

        try {
            const res = await fetch(`${API_BASE}/learning-roadmap`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ target_skill: skill })
            });
            const data = await res.json();
            
            const tasksContainer = document.getElementById('c4-tasks-container');
            tasksContainer.innerHTML = '';
            
            if(data.roadmap) {
                // Assuming roadmap has daily, weekly, monthly
                ['daily', 'weekly', 'monthly'].forEach(period => {
                    const items = data.roadmap[`${period}_tasks`] || [];
                    tasksContainer.innerHTML += `
                        <div class="glass-card">
                            <h3 style="text-transform:capitalize; border-bottom:1px solid var(--border-color); padding-bottom:5px; margin-bottom:10px;">${period} Tasks</h3>
                            <ul style="padding-left:15px; color:var(--text-secondary);">
                                ${items.map(i => `<li>${i}</li>`).join('')}
                            </ul>
                        </div>
                    `;
                });
            }
            
            const resContainer = document.getElementById('c4-resources-container');
            resContainer.innerHTML = '';
            if(data.roadmap && data.roadmap.resources) {
                data.roadmap.resources.forEach(r => {
                    resContainer.innerHTML += `
                        <div class="glass-card" style="padding:15px;">
                            <strong>${r.title || r}</strong>
                            <p style="font-size:0.8rem; color:var(--text-secondary); margin-top:5px;">${r.type || 'Resource'}</p>
                            ${r.url ? `<a href="${r.url}" target="_blank" style="color:var(--accent-blue); font-size:0.8rem;">View Link</a>` : ''}
                        </div>
                    `;
                });
            }
            
        } catch (e) {
            showToast('Failed to load roadmap', 'error');
        } finally {
            btn.innerHTML = 'Generate';
            btn.disabled = false;
        }
    });

    /* =================================================================
       MODULE C5: Certifications
       ================================================================= */
    document.getElementById('c5-fetch-btn').addEventListener('click', async () => {
        const btn = document.getElementById('c5-fetch-btn');
        btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Finding...';
        btn.disabled = true;

        showSkeleton('c5-certs-container');

        try {
            const res = await fetch(`${API_BASE}/certifications`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ 
                    resume_skills: ["Python", "AWS"], 
                    target_role: "Cloud Engineer" 
                })
            });
            const certs = await res.json();
            
            const container = document.getElementById('c5-certs-container');
            container.innerHTML = '';
            
            certs.forEach(cert => {
                container.innerHTML += `
                    <div class="glass-card">
                        <h3 style="margin-bottom:10px; font-size:1.1rem;">${cert.name}</h3>
                        <div style="display:flex; gap:5px; margin-bottom:15px; flex-wrap:wrap;">
                            <span class="badge badge-orange">Difficulty: ${cert.difficulty}</span>
                            <span class="badge badge-purple">Duration: ${cert.duration}</span>
                        </div>
                        <p style="font-size:0.9rem; color:var(--text-secondary);">${cert.career_value || 'Great for boosting resume visibility.'}</p>
                    </div>
                `;
            });
            showToast('Certifications loaded', 'success');
        } catch (e) {
            showToast('Failed to fetch certifications', 'error');
        } finally {
            btn.innerHTML = '<i class="fa-solid fa-sync"></i> Find Best Certifications';
            btn.disabled = false;
        }
    });

    /* =================================================================
       MODULE C6: Portfolio Analyzer
       ================================================================= */
    document.getElementById('c6-analyze-btn').addEventListener('click', async () => {
        const text = document.getElementById('c6-project-text').value;
        if (!text) return showToast('Please enter project details', 'error');

        const btn = document.getElementById('c6-analyze-btn');
        btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Analyzing...';
        btn.disabled = true;

        showSkeleton('c6-scores-container');

        try {
            const res = await fetch(`${API_BASE}/portfolio-analysis`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ resume_skills: [], project_text: text })
            });
            const data = await res.json();
            
            const container = document.getElementById('c6-scores-container');
            container.innerHTML = `
                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <span style="font-weight:600;">Overall Score</span>
                    <span style="font-size:1.5rem; color:var(--accent-green); font-family:var(--font-heading);">${data.portfolio_score || 85}/100</span>
                </div>
                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <span style="font-weight:600;">Code Quality</span>
                    <span style="font-size:1.5rem; color:var(--accent-blue); font-family:var(--font-heading);">${data.code_quality_score || 80}/100</span>
                </div>
                <div style="margin-top:15px; border-top:1px solid var(--border-color); padding-top:15px;">
                    <h4 style="margin-bottom:10px;">Suggestions</h4>
                    <ul style="color:var(--text-secondary); padding-left:15px; font-size:0.9rem;">
                        ${data.suggestions ? data.suggestions.map(s => `<li>${s}</li>`).join('') : '<li>Add more documentation.</li>'}
                    </ul>
                </div>
            `;
            showToast('Analysis complete', 'success');
        } catch (e) {
            showToast('Failed to analyze portfolio', 'error');
        } finally {
            btn.innerHTML = '<i class="fa-solid fa-magnifying-glass-chart"></i> Analyze';
            btn.disabled = false;
        }
    });

    /* =================================================================
       MODULE C7: Job Readiness
       ================================================================= */
    document.getElementById('c7-calculate-btn').addEventListener('click', async () => {
        const btn = document.getElementById('c7-calculate-btn');
        btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Calculating...';
        btn.disabled = true;

        showSkeleton('c7-scores-container');

        try {
            const res = await fetch(`${API_BASE}/job-readiness`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ 
                    ats_score: 75, 
                    interview_avg_score: 8.0, 
                    skill_match_percentage: 80, 
                    portfolio_score: 8.5 
                })
            });
            const data = await res.json();
            
            const container = document.getElementById('c7-scores-container');
            container.innerHTML = '';
            
            const metrics = [
                { label: 'Overall Readiness', value: data.overall_score || 82, color: 'var(--accent-green)' },
                { label: 'Resume ATS', value: data.components?.ats_score || 75, color: 'var(--accent-blue)' },
                { label: 'Interview', value: (data.components?.interview_score || 8)*10, color: 'var(--accent-purple)' },
                { label: 'Skills Match', value: data.components?.skill_match || 80, color: 'var(--accent-orange)' }
            ];
            
            metrics.forEach(m => {
                container.innerHTML += `
                    <div class="glass-card" style="display:flex; flex-direction:column; align-items:center; justify-content:center;">
                        <div style="position:relative; width:120px; height:120px; border-radius:50%; background:conic-gradient(${m.color} ${m.value}%, rgba(255,255,255,0.1) 0); display:flex; align-items:center; justify-content:center; margin-bottom:15px;">
                            <div style="width:100px; height:100px; background:var(--bg-card); border-radius:50%; display:flex; align-items:center; justify-content:center; font-size:1.5rem; font-family:var(--font-heading); font-weight:700;">
                                ${m.value}%
                            </div>
                        </div>
                        <h3 style="font-size:1rem;">${m.label}</h3>
                    </div>
                `;
            });
            
            const list = document.getElementById('c7-suggestions-list');
            list.innerHTML = '';
            if(data.suggestions) {
                data.suggestions.forEach(s => {
                    list.innerHTML += `<li>${s}</li>`;
                });
            } else {
                list.innerHTML = '<li>You are well prepared. Keep applying!</li>';
            }
            
            showToast('Scores calculated', 'success');
        } catch (e) {
            showToast('Failed to calculate readiness', 'error');
        } finally {
            btn.innerHTML = 'Calculate Score';
            btn.disabled = false;
        }
    });

    /* =================================================================
       MODULE C8: Job Tracker (Kanban)
       ================================================================= */
    async function loadC8Jobs() {
        try {
            const res = await fetch(`${API_BASE}/tracker/jobs`);
            const jobs = await res.json();
            
            // Clear dropzones
            document.querySelectorAll('.kanban-dropzone').forEach(el => el.innerHTML = '');
            
            jobs.forEach(job => {
                const status = job.status.toLowerCase();
                const dropzoneId = `kb-${status}`;
                const dropzone = document.getElementById(dropzoneId);
                if (dropzone) {
                    const card = document.createElement('div');
                    card.className = 'glass-card';
                    card.style.padding = '15px';
                    card.style.cursor = 'grab';
                    card.draggable = true;
                    card.dataset.id = job.id;
                    card.innerHTML = `
                        <div style="display:flex; justify-content:space-between; margin-bottom:5px;">
                            <strong>${job.company_name}</strong>
                            <button class="icon-btn delete-job-btn" style="width:24px; height:24px; font-size:0.8rem; color:var(--accent-red); border:none;" data-id="${job.id}"><i class="fa-solid fa-trash"></i></button>
                        </div>
                        <div style="font-size:0.9rem; color:var(--text-secondary);">${job.role_title}</div>
                        <div style="font-size:0.8rem; margin-top:5px; color:var(--accent-blue);">${job.location || 'Remote'}</div>
                    `;
                    
                    // Simple drag implementation (can be enhanced)
                    card.addEventListener('dragstart', (e) => {
                        e.dataTransfer.setData('text/plain', job.id);
                    });
                    
                    dropzone.appendChild(card);
                }
            });
            
            // Bind delete buttons
            document.querySelectorAll('.delete-job-btn').forEach(btn => {
                btn.addEventListener('click', async (e) => {
                    e.stopPropagation();
                    const id = btn.dataset.id;
                    if(confirm("Delete this job application?")) {
                        await fetch(`${API_BASE}/tracker/job/${id}`, { method: 'DELETE' });
                        showToast('Job deleted', 'success');
                        loadC8Jobs();
                    }
                });
            });
            
        } catch (e) {
            console.error("Failed to load jobs", e);
        }
    }

    document.getElementById('c8-add-btn').addEventListener('click', () => {
        document.getElementById('c8-modal').style.display = 'flex';
    });

    document.getElementById('c8-save-btn').addEventListener('click', async () => {
        const company = document.getElementById('c8-form-company').value;
        const role = document.getElementById('c8-form-role').value;
        const status = document.getElementById('c8-form-status').value;
        
        if(!company || !role) return showToast('Company and Role required', 'error');
        
        try {
            await fetch(`${API_BASE}/tracker/job`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ company_name: company, role_title: role, status: status })
            });
            document.getElementById('c8-modal').style.display = 'none';
            showToast('Job added', 'success');
            loadC8Jobs();
        } catch(e) {
            showToast('Failed to add job', 'error');
        }
    });

    /* =================================================================
       MODULE C9: Analytics Dashboard (Chart.js)
       ================================================================= */
    let charts = {};
    Chart.defaults.color = '#94a3b8'; // text-secondary
    Chart.defaults.font.family = 'Inter, sans-serif';

    function getChartThemeColors() {
        const isLight = document.documentElement.getAttribute('data-theme') === 'light';
        return {
            grid: isLight ? 'rgba(0,0,0,0.1)' : 'rgba(255,255,255,0.1)',
            text: isLight ? '#475569' : '#94a3b8'
        };
    }

    async function loadC9Analytics() {
        try {
            // First load the API data
            const res = await fetch(`${API_BASE}/dashboard?ats_score=80`);
            const data = await res.json();
            
            const theme = getChartThemeColors();
            Chart.defaults.color = theme.text;
            
            const commonOptions = {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    x: { grid: { color: theme.grid } },
                    y: { grid: { color: theme.grid } }
                },
                plugins: { legend: { display: false } }
            };

            // 1. ATS Trend (Line)
            const ctxAts = document.getElementById('chart-ats-trend').getContext('2d');
            if(charts.ats) charts.ats.destroy();
            charts.ats = new Chart(ctxAts, {
                type: 'line',
                data: {
                    labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
                    datasets: [{
                        label: 'ATS Score',
                        data: data.ats_trend || [60, 65, 72, 75, 80, 85],
                        borderColor: '#3b82f6',
                        tension: 0.4,
                        borderWidth: 2,
                        fill: true,
                        backgroundColor: 'rgba(59, 130, 246, 0.1)'
                    }]
                },
                options: commonOptions
            });

            // 2. Interview Trend (Bar)
            const ctxInt = document.getElementById('chart-interview-trend').getContext('2d');
            if(charts.int) charts.int.destroy();
            charts.int = new Chart(ctxInt, {
                type: 'bar',
                data: {
                    labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
                    datasets: [{
                        label: 'Avg Score',
                        data: data.interview_trend || [5, 6, 7, 7.5, 8, 8.5],
                        backgroundColor: '#8b5cf6',
                        borderRadius: 4
                    }]
                },
                options: commonOptions
            });

            // 3. Career Readiness (Doughnut)
            const ctxRead = document.getElementById('chart-readiness').getContext('2d');
            if(charts.read) charts.read.destroy();
            charts.read = new Chart(ctxRead, {
                type: 'doughnut',
                data: {
                    labels: ['ATS', 'Interview', 'Skills', 'Portfolio'],
                    datasets: [{
                        data: [
                            data.readiness?.ats_score || 80,
                            (data.readiness?.interview_score || 8) * 10,
                            data.readiness?.skill_match || 85,
                            (data.readiness?.portfolio_score || 7.5) * 10
                        ],
                        backgroundColor: ['#3b82f6', '#8b5cf6', '#10b981', '#f59e0b'],
                        borderWidth: 0
                    }]
                },
                options: { ...commonOptions, cutout: '70%', plugins: { legend: { display: true, position: 'bottom' } }, scales: {} }
            });

            // 4. Skill Growth (Radar)
            const ctxSkill = document.getElementById('chart-skill-growth').getContext('2d');
            if(charts.skill) charts.skill.destroy();
            charts.skill = new Chart(ctxSkill, {
                type: 'radar',
                data: {
                    labels: ['Python', 'React', 'System Design', 'AWS', 'Docker'],
                    datasets: [{
                        label: 'Current Level',
                        data: data.skill_growth?.current || [80, 90, 60, 70, 65],
                        borderColor: '#06b6d4',
                        backgroundColor: 'rgba(6, 182, 212, 0.2)',
                        pointBackgroundColor: '#06b6d4'
                    }, {
                        label: 'Target Level',
                        data: data.skill_growth?.target || [90, 95, 80, 90, 85],
                        borderColor: '#94a3b8',
                        borderDash: [5, 5],
                        backgroundColor: 'transparent'
                    }]
                },
                options: {
                    responsive: true, maintainAspectRatio: false,
                    scales: { r: { grid: { color: theme.grid }, angleLines: { color: theme.grid }, pointLabels: { color: theme.text } } },
                    plugins: { legend: { display: true, position: 'top' } }
                }
            });

            // 5. Job Applications (Bar)
            const ctxApp = document.getElementById('chart-applications').getContext('2d');
            if(charts.app) charts.app.destroy();
            charts.app = new Chart(ctxApp, {
                type: 'bar',
                data: {
                    labels: ['Wishlist', 'Applied', 'Interview', 'Offer', 'Rejected'],
                    datasets: [{
                        label: 'Count',
                        data: data.applications_summary || [5, 12, 4, 1, 3],
                        backgroundColor: ['#64748b', '#3b82f6', '#f59e0b', '#10b981', '#ef4444'],
                        borderRadius: 4
                    }]
                },
                options: commonOptions
            });

        } catch (e) {
            console.error("Analytics load failed", e);
        }
    }

    // Initialize initial active section (C9 is default)
    loadC9Analytics();
});
