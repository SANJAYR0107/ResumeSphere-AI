document.addEventListener('DOMContentLoaded', () => {
    // DOM Elements
    const dropZone = document.getElementById('drop-zone');
    const fileInput = document.getElementById('file-input');
    const browseBtn = document.getElementById('browse-btn');
    const progressContainer = document.getElementById('progress-container');
    const progressBarFill = document.getElementById('progress-bar-fill');
    const filenameDisplay = document.getElementById('filename-display');
    const filesizeDisplay = document.getElementById('filesize-display');
    const statusMessage = document.getElementById('status-message');
    const resultsContainer = document.getElementById('results-container');
    
    // Results DOM Elements
    const scoreNumber = document.getElementById('score-number');
    const scoreRing = document.getElementById('score-ring');
    const scoreEvaluation = document.getElementById('score-evaluation');
    const skillsGrid = document.getElementById('skills-grid');
    const jobList = document.getElementById('job-list');
    const suggestionsList = document.getElementById('suggestions-list');
    const extractedTextDisplay = document.getElementById('extracted-text-display');
    
    // Accordion Elements
    const accordionToggle = document.getElementById('accordion-toggle');
    const accordionContent = document.getElementById('accordion-content');
    const accordionIcon = document.getElementById('accordion-icon');

    // Job Match DOM Elements
    const jdMatchBtn = document.getElementById('jd-match-btn');
    const jdInput = document.getElementById('jd-input');
    const jdResults = document.getElementById('jd-results');

    // Global state
    let currentResumeText = '';
    let currentResumeSkills = [];

    let API_URL = 'http://127.0.0.1:8001/api';
    if (window.location.port === '8001' || (window.location.hostname !== 'localhost' && window.location.hostname !== '127.0.0.1' && window.location.protocol !== 'file:')) {
        API_URL = '/api';
    }

    // Theme Logic
    const themeBtn = document.getElementById('theme-toggle-btn');
    if (themeBtn) {
        if (localStorage.getItem('theme') === 'light') document.body.classList.add('light-mode');
        themeBtn.addEventListener('click', () => {
            document.body.classList.toggle('light-mode');
            localStorage.setItem('theme', document.body.classList.contains('light-mode') ? 'light' : 'dark');
        });
    }

    // Radial Progress Configuration
    const radius = 100;
    const circumference = radius * 2 * Math.PI;
    scoreRing.style.strokeDasharray = `${circumference} ${circumference}`;
    scoreRing.style.strokeDashoffset = circumference;

    function setScore(percent) {
        const offset = circumference - (percent / 100) * circumference;
        scoreRing.style.strokeDashoffset = offset;
        
        let current = 0;
        const duration = 800; // ms
        const stepTime = Math.abs(Math.floor(duration / percent)) || 10;
        const timer = setInterval(() => {
            current += 1;
            scoreNumber.textContent = current;
            if (current >= percent) {
                clearInterval(timer);
                scoreNumber.textContent = percent;
            }
        }, stepTime);
    }

    function setGauge(ring, textEl, evalEl, percent) {
        const offset = circumference - (percent / 100) * circumference;
        ring.style.strokeDashoffset = offset;
        
        let current = 0;
        const duration = 800; // ms
        const stepTime = Math.abs(Math.floor(duration / percent)) || 10;
        const timer = setInterval(() => {
            current += 1;
            textEl.textContent = current;
            if (current >= percent) {
                clearInterval(timer);
                textEl.textContent = percent;
            }
        }, stepTime);

        if (percent >= 85) {
            evalEl.textContent = "Excellent";
            evalEl.style.color = "#00f2fe";
        } else if (percent >= 70) {
            evalEl.textContent = "Good";
            evalEl.style.color = "#4facfe";
        } else {
            evalEl.textContent = "Needs Work";
            evalEl.style.color = "#e100ff";
        }
    }

    // Drag and Drop
    ['dragenter', 'dragover'].forEach(eventName => {
        dropZone.addEventListener(eventName, (e) => {
            e.preventDefault(); e.stopPropagation();
            dropZone.classList.add('dragover');
        }, false);
    });

    ['dragleave', 'drop'].forEach(eventName => {
        dropZone.addEventListener(eventName, (e) => {
            e.preventDefault(); e.stopPropagation();
            dropZone.classList.remove('dragover');
        }, false);
    });

    dropZone.addEventListener('drop', (e) => {
        const dt = e.dataTransfer;
        if (dt.files.length > 0) handleFile(dt.files[0]);
    });

    browseBtn.addEventListener('click', () => fileInput.click());
    fileInput.addEventListener('change', (e) => {
        if (e.target.files.length > 0) handleFile(e.target.files[0]);
    });

    function handleFile(file) {
        if (file.type !== 'application/pdf') {
            alert('Please upload a PDF file only.');
            return;
        }

        filenameDisplay.innerHTML = `<i class="fa-solid fa-file-invoice"></i> ${file.name}`;
        filesizeDisplay.textContent = formatBytes(file.size);
        progressContainer.classList.remove('hidden');
        resultsContainer.classList.add('hidden');
        jdResults.classList.add('hidden');
        jdInput.value = '';
        progressBarFill.style.width = '0%';
        statusMessage.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i> Analyzing resume...`;

        const formData = new FormData();
        formData.append('resume', file);

        // 1. Call /api/analyze to extract core NLP data
        fetch(`${API_URL}/analyze`, { method: 'POST', body: formData })
        .then(response => {
            if (!response.ok) return response.json().then(err => { throw new Error(err.detail) });
            return response.json();
        })
        .then(data => {
            currentResumeText = data.clean_text;
            currentResumeSkills = data.skills;

            progressBarFill.style.width = '50%';
            statusMessage.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i> Fetching ATS Score & Recommendations...`;
            
            // 2. Parallel fetch for Recommendations and ATS Score
            const p1 = fetch(`${API_URL}/recommendations`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ resume_skills: data.skills, resume_text: data.clean_text })
            }).then(r => r.json());

            const p2 = fetch(`${API_URL}/ats-score`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ resume_text: data.clean_text })
            }).then(r => r.json());

            return Promise.all([data, p1, p2]);
        })
        .then(([analyzeData, recData, atsData]) => {
            progressBarFill.style.width = '100%';
            statusMessage.innerHTML = `<i class="fa-solid fa-check"></i> Analysis complete!`;
            
            setTimeout(() => {
                progressContainer.classList.add('hidden');
                renderResults(analyzeData, recData, atsData);
            }, 400);
        })
        .catch(error => {
            progressBarFill.style.width = '0%';
            statusMessage.innerHTML = `<i class="fa-solid fa-circle-xmark" style="color: #ff3366"></i> Error: ${error.message}`;
            alert(`Analysis failed: ${error.message}`);
        });
    }

    function renderResults(analyzeData, recData, atsData) {
        resultsContainer.classList.remove('hidden');
        document.getElementById('export-pdf-btn').style.display = 'inline-flex';

        // 1. Overall Score
        const overall = analyzeData.overall_score || { overall_score: 0, explanation: "N/A" };
        setScore(overall.overall_score);
        document.getElementById('score-explanation').textContent = overall.explanation;

        // Hero Summary Card updates
        document.getElementById('hero-ats-grade').textContent = analyzeData.ats_grade || "N/A";
        document.getElementById('hero-hiring-prob').textContent = analyzeData.hiring_probability || "N/A";
        document.getElementById('hero-strength-index').textContent = analyzeData.resume_strength_index || "N/A";
        document.getElementById('hero-confidence').textContent = analyzeData.recruiter_confidence || "N/A";

        // Gauges
        const atsRing = document.getElementById('ats-ring');
        const atsScoreText = document.getElementById('ats-score-number');
        const atsEval = document.getElementById('ats-score-evaluation');
        if (atsRing) setGauge(atsRing, atsScoreText, atsEval, analyzeData.ats_score || 0);

        const intRing = document.getElementById('interview-ring');
        const intScoreText = document.getElementById('interview-score-number');
        const intEval = document.getElementById('interview-score-evaluation');
        if (intRing) {
            const intScore = analyzeData.interview_readiness?.interview_score || 0;
            setGauge(intRing, intScoreText, intEval, intScore);
        }

        // 2. Section Scores Grid
        const grid = document.getElementById('section-scores-grid');
        grid.innerHTML = '';
        if (analyzeData.section_scores) {
            Object.entries(analyzeData.section_scores).forEach(([key, data]) => {
                const color = data.score >= 80 ? '#10b981' : (data.score >= 50 ? '#f59e0b' : '#ef4444');
                grid.innerHTML += `
                    <div style="background: rgba(255,255,255,0.03); border: 1px solid var(--border-color); padding: 15px; border-radius: 10px;">
                        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:10px;">
                            <strong style="text-transform:capitalize; font-size:0.95rem;">${key.replace('_', ' ')}</strong>
                            <span style="font-weight:bold; color:${color};">${data.score}%</span>
                        </div>
                        <div style="width:100%; height:6px; background:rgba(255,255,255,0.1); border-radius:3px; overflow:hidden;">
                            <div style="height:100%; width:${data.score}%; background:${color};"></div>
                        </div>
                        <div style="font-size:0.75rem; color:var(--text-muted); margin-top:8px;">${escapeHtml(data.reason)}</div>
                    </div>
                `;
            });
        }

        // 3. Radar Chart for Skills
        const ctx = document.getElementById('skillRadarChart').getContext('2d');
        if (window.myRadarChart) {
            window.myRadarChart.destroy();
        }
        
        const skillGroups = analyzeData.skill_analysis?.groups || {};
        const labels = Object.keys(skillGroups);
        const dataPoints = labels.map(l => skillGroups[l].length);
        
        if (labels.length > 0) {
            window.myRadarChart = new Chart(ctx, {
                type: 'radar',
                data: {
                    labels: labels,
                    datasets: [{
                        label: 'Skill Count',
                        data: dataPoints,
                        backgroundColor: 'rgba(0, 242, 254, 0.2)',
                        borderColor: '#00f2fe',
                        pointBackgroundColor: '#e100ff',
                        pointBorderColor: '#fff',
                        pointHoverBackgroundColor: '#fff',
                        pointHoverBorderColor: '#e100ff'
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        r: {
                            angleLines: { color: 'rgba(255, 255, 255, 0.1)' },
                            grid: { color: 'rgba(255, 255, 255, 0.1)' },
                            pointLabels: { color: '#9aa2b1', font: { size: 12 } },
                            ticks: { display: false, max: Math.max(...dataPoints) + 2 }
                        }
                    },
                    plugins: {
                        legend: { display: false }
                    }
                }
            });
        }

        // 4. Strengths & Weaknesses
        const slist = document.getElementById('strengths-list');
        const wlist = document.getElementById('weaknesses-list');
        slist.innerHTML = (analyzeData.strengths || []).map(s => `<li>${escapeHtml(s)}</li>`).join('');
        wlist.innerHTML = (analyzeData.weaknesses || []).map(w => `<li>${escapeHtml(w)}</li>`).join('');

        // 5. Actionable Suggestions
        const actionList = document.getElementById('actionable-suggestions-list');
        if (analyzeData.actionable_suggestions) {
            actionList.innerHTML = analyzeData.actionable_suggestions.map(s => {
                const badgeColor = s.priority === 'High' ? '#ef4444' : (s.priority === 'Medium' ? '#f59e0b' : '#3b82f6');
                return `
                    <div style="background: rgba(255,255,255,0.03); padding: 12px; border-left: 3px solid ${badgeColor}; border-radius: 6px;">
                        <div style="display:flex; justify-content:space-between; margin-bottom:5px;">
                            <strong style="color:var(--text-primary); font-size:0.95rem;">${escapeHtml(s.suggestion)}</strong>
                            <span style="font-size:0.75rem; background: ${badgeColor}20; color:${badgeColor}; padding:2px 8px; border-radius:12px;">${s.priority} Priority</span>
                        </div>
                        <div style="font-size:0.8rem; color:var(--text-muted);">
                            <i class="fa-solid fa-hammer"></i> Difficulty: ${s.difficulty} &nbsp;|&nbsp; 
                            <i class="fa-solid fa-clock"></i> Time: ${s.estimated_learning_time}
                        </div>
                    </div>
                `;
            }).join('');
        }

        // Recruiter Insights DOM Updates
        if (analyzeData.recruiter_summary) {
            document.getElementById('recruiter-impression').textContent = analyzeData.recruiter_summary.overall_impression;
            const recEl = document.getElementById('recruiter-recommendation');
            recEl.textContent = analyzeData.recruiter_summary.hiring_recommendation;
            recEl.style.color = analyzeData.recruiter_summary.pass_ats ? '#10b981' : '#ef4444';
        }
        if (analyzeData.career_insights) {
            document.getElementById('career-level').textContent = analyzeData.career_insights.career_level;
            document.getElementById('career-roles').textContent = analyzeData.career_insights.best_job_roles.join(', ');
            document.getElementById('career-roadmap-list').innerHTML = analyzeData.career_insights.learning_roadmap.map(s => `<li>${escapeHtml(s)}</li>`).join('');
        }
        if (analyzeData.interview_readiness) {
            document.getElementById('interview-questions-list').innerHTML = analyzeData.interview_readiness.likely_questions.map(s => `<li>${escapeHtml(s)}</li>`).join('');
        }

        // Section Breakdown Bar Chart
        if (analyzeData.ats_breakdown) {
            const barCtx = document.getElementById('sectionBarChart')?.getContext('2d');
            if (barCtx) {
                if (window.myBarChart) window.myBarChart.destroy();
                const bLabels = Object.keys(analyzeData.ats_breakdown).map(l => l.replace(/_/g, ' '));
                const bData = Object.values(analyzeData.ats_breakdown).map(v => typeof v === 'object' && v !== null && 'score' in v ? v.score : (typeof v === 'number' ? v : 0));
                window.myBarChart = new Chart(barCtx, {
                    type: 'bar',
                    data: {
                        labels: bLabels,
                        datasets: [{
                            label: 'ATS Breakdown Score',
                            data: bData,
                            backgroundColor: 'rgba(79, 172, 254, 0.5)',
                            borderColor: '#4facfe',
                            borderWidth: 1
                        }]
                    },
                    options: {
                        responsive: true, maintainAspectRatio: false,
                        scales: { y: { beginAtZero: true, max: 100, grid: { color: 'rgba(255,255,255,0.05)' } }, x: { grid: { display: false } } },
                        plugins: { legend: { display: false } }
                    }
                });
            }
        }

        // 6. Deep Analysis
        if (analyzeData.project_analysis) {
            const p = analyzeData.project_analysis;
            document.getElementById('project-analysis-content').innerHTML = `
                <p><strong>Complexity:</strong> ${escapeHtml(p.complexity || 'Standard')}</p>
                <p><strong>Action Verbs Used:</strong> ${p.action_verbs_used ?? 0}</p>
                <p><strong>Missing Metrics:</strong> ${p.missing_metrics ? "Yes" : "No"}</p>
                <p><strong>Suggestions:</strong> ${escapeHtml((p.suggestions || []).join(', '))}</p>
            `;
        }
        if (analyzeData.experience_analysis) {
            const e = analyzeData.experience_analysis;
            document.getElementById('experience-analysis-content').innerHTML = `
                <p><strong>Estimated YOE:</strong> ${escapeHtml(String(e.estimated_years ?? 'N/A'))}</p>
                <p><strong>Achievements Found:</strong> ${e.achievements_found ?? 0}</p>
                <p><strong>Leadership Detected:</strong> ${e.leadership_detected ? "Yes" : "No"}</p>
                <p><strong>Suggestions:</strong> ${escapeHtml((e.suggestions || []).join(', '))}</p>
            `;
        }
        if (analyzeData.grammar_analysis) {
            const g = analyzeData.grammar_analysis;
            document.getElementById('grammar-analysis-content').innerHTML = `
                <p><strong>Passive Voice Instances:</strong> ${g.passive_voice_instances ?? 0}</p>
                <p><strong>Capitalization Issues:</strong> ${g.capitalization_issues ? "Yes" : "No"}</p>
                <p><strong>Bullet Consistency:</strong> ${escapeHtml(g.bullet_consistency || 'Good')}</p>
                <p><strong>Findings:</strong> ${escapeHtml((g.findings || []).join(', '))}</p>
            `;
        }

        // 7. Render Skills
        if (skillsGrid) {
            skillsGrid.innerHTML = (analyzeData.skills || []).length > 0 
                ? analyzeData.skills.map(s => `<span class="skill-tag">${escapeHtml(s)}</span>`).join('')
                : '<span class="skill-tag">No skills detected</span>';
        }

        // 8. Phase 3: Recommended Jobs & Skill Gap
        if (analyzeData.recommended_jobs && analyzeData.recommended_jobs.length > 0) {
            const jobs = analyzeData.recommended_jobs;
            
            // Job Cards
            const cardsContainer = document.getElementById('job-cards-container');
            if (cardsContainer) {
                cardsContainer.innerHTML = jobs.map(job => `
                    <div style="background: rgba(255,255,255,0.03); padding: 1rem; border-radius: 8px; border-left: 4px solid var(--accent-cyan);">
                        <div style="display: flex; justify-content: space-between; align-items: flex-start;">
                            <h4 style="margin: 0 0 0.5rem 0; color: #fff;">${escapeHtml(job.role_name)}</h4>
                            <span style="background: rgba(0, 242, 254, 0.15); color: #00f2fe; padding: 2px 8px; border-radius: 12px; font-size: 0.8rem; font-weight: bold;">${job.match_percentage}% Match</span>
                        </div>
                        <div style="display: flex; gap: 15px; font-size: 0.8rem; margin-bottom: 8px;">
                            <span style="color: var(--text-secondary);"><i class="fa-solid fa-bullseye"></i> Confidence: <span style="color: ${job.confidence === 'High' ? '#10b981' : (job.confidence === 'Medium' ? '#f59e0b' : '#ef4444')}">${job.confidence}</span></span>
                            <span style="color: var(--text-secondary);"><i class="fa-solid fa-layer-group"></i> Difficulty: <span style="color: ${job.difficulty === 'Easy' ? '#10b981' : (job.difficulty === 'Medium' ? '#f59e0b' : '#ef4444')}">${job.difficulty}</span></span>
                        </div>
                        <div style="font-size: 0.8rem; color: #10b981; margin-bottom: 4px;"><i class="fa-solid fa-check"></i> Skills: ${escapeHtml((job.matched_skills || []).slice(0,5).join(', '))}</div>
                    </div>
                `).join('');
            }

            // Comparison Bars
            const barsContainer = document.getElementById('job-comparison-bars');
            if (barsContainer) {
                barsContainer.innerHTML = jobs.map(job => `
                    <div>
                        <div style="display: flex; justify-content: space-between; font-size: 0.85rem; margin-bottom: 4px; color: var(--text-secondary);">
                            <span>${escapeHtml(job.role_name)}</span>
                            <span style="color: #fff; font-weight: bold;">${job.match_percentage}%</span>
                        </div>
                        <div style="width: 100%; height: 8px; background: rgba(255,255,255,0.05); border-radius: 4px; overflow: hidden;">
                            <div style="height: 100%; width: ${job.match_percentage}%; background: linear-gradient(90deg, #00f2fe 0%, #4facfe 100%); border-radius: 4px;"></div>
                        </div>
                    </div>
                `).join('');
            }
        }

        // Skill Gap
        if (analyzeData.skill_gap && analyzeData.skill_gap.skill_gap_details) {
            const missingList = document.getElementById('missing-skills-list');
            if (missingList) {
                missingList.innerHTML = analyzeData.skill_gap.skill_gap_details.slice(0, 5).map(skill => {
                    const resource = (skill.recommended_resources && skill.recommended_resources.length > 0) ? skill.recommended_resources[0] : 'Documentation';
                    return `
                    <li style="margin-bottom: 8px;">
                        <strong style="color: #fff;">${escapeHtml(skill.skill)}</strong> 
                        <span style="font-size: 0.75rem; background: rgba(239, 68, 68, 0.15); color: #ef4444; padding: 2px 6px; border-radius: 4px; margin-left: 5px;">${escapeHtml(skill.priority || 'Medium')}</span>
                        <div style="font-size: 0.75rem; margin-top: 2px;">Time: ${escapeHtml(skill.learning_time || '1-2 Weeks')} | Resource: <a href="#" style="color: #4facfe;">${escapeHtml(resource)}</a></div>
                    </li>
                `}).join('');
            }
        }

        // Career Roadmap
        if (analyzeData.career_roadmap) {
            const targetEl = document.getElementById('roadmap-target');
            if (targetEl) targetEl.textContent = analyzeData.career_roadmap.next_target;
            
            const weeksContainer = document.getElementById('roadmap-weeks');
            if (weeksContainer && analyzeData.career_roadmap.roadmap_weeks) {
                weeksContainer.innerHTML = Object.entries(analyzeData.career_roadmap.roadmap_weeks).map(([week, task]) => `
                    <div style="display: flex; gap: 10px; padding-left: 10px; border-left: 2px solid var(--border-color);">
                        <strong style="color: #fff; min-width: 50px;">${escapeHtml(week)}</strong>
                        <span>${escapeHtml(task)}</span>
                    </div>
                `).join('');
            }
        }

        // Interview Prep
        if (analyzeData.interview_preparation && analyzeData.interview_preparation.length > 0) {
            const prep = analyzeData.interview_preparation[0];
            const roleEl = document.getElementById('interview-role');
            if (roleEl) roleEl.textContent = prep.role_name;
            
            const qContainer = document.getElementById('interview-questions');
            if (qContainer) {
                qContainer.innerHTML = prep.likely_technical_questions.map(q => `
                    <div style="background: rgba(255,255,255,0.03); padding: 8px 12px; border-radius: 4px; margin-bottom: 8px; border-left: 2px solid var(--accent-purple);">
                        ${escapeHtml(q)}
                    </div>
                `).join('');
            }
        }

        if (extractedTextDisplay) {
            extractedTextDisplay.textContent = analyzeData.clean_text || "No text extracted.";
        }
    }

    // Export PDF Logic
    document.getElementById('export-pdf-btn')?.addEventListener('click', () => {
        const element = document.getElementById('results-container');
        const opt = {
            margin:       0.5,
            filename:     'resume-analysis.pdf',
            image:        { type: 'jpeg', quality: 0.98 },
            html2canvas:  { scale: 2, useCORS: true },
            jsPDF:        { unit: 'in', format: 'letter', orientation: 'portrait' }
        };
        html2pdf().set(opt).from(element).save();
    });

    // JD Matching Flow
    if (jdMatchBtn) {
        jdMatchBtn.addEventListener('click', () => {
            const jdText = jdInput.value.trim();
            if (!jdText || jdText.length < 20) {
                alert("Please paste a valid job description (at least 20 characters).");
                return;
            }
            if (!currentResumeText) {
                alert("Please upload a resume first.");
                return;
            }

            const originalBtnHtml = jdMatchBtn.innerHTML;
            jdMatchBtn.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i> Analyzing...`;
            jdMatchBtn.disabled = true;

            // 1. Call /job-match
            fetch(`${API_URL}/job-match`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ resume_text: currentResumeText, job_description: jdText })
            })
            .then(res => res.json())
            .then(matchData => {
                // 2. Call /skill-gap
                return fetch(`${API_URL}/skill-gap`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ matched_skills: matchData.matched_skills, missing_skills: matchData.missing_skills })
                })
                .then(res => res.json())
                .then(gapData => ({ matchData, gapData }));
            })
            .then(({ matchData, gapData }) => {
                document.getElementById('jd-match-score').textContent = matchData.match_score;
                document.getElementById('jd-semantic-score').textContent = Math.round(matchData.semantic_similarity * 100);
                
                const skillPill = (s, cls) => `<span style="display:inline-block; margin:3px; padding:3px 8px; border-radius:12px; font-size:0.8rem; background:rgba(255,255,255,0.1);" class="${cls}">${escapeHtml(s)}</span>`;
                
                document.getElementById('jd-matched-skills').innerHTML = matchData.matched_skills.map(s => skillPill(s, '')).join('');
                document.getElementById('jd-missing-skills').innerHTML = matchData.missing_skills.map(s => skillPill(s, '')).join('');
                
                document.getElementById('jd-learning-suggestions').innerHTML = gapData.learning_suggestions.map(s => `<li style="margin-bottom:8px;">${escapeHtml(s)}</li>`).join('');
                
                jdResults.classList.remove('hidden');
            })
            .catch(err => alert("Error: " + err.message))
            .finally(() => {
                jdMatchBtn.innerHTML = originalBtnHtml;
                jdMatchBtn.disabled = false;
            });
        });
    }

    // Accordion Logic
    accordionToggle.addEventListener('click', () => {
        const isCollapsed = accordionContent.classList.contains('collapsed');
        if (isCollapsed) {
            accordionContent.classList.remove('collapsed');
            accordionContent.style.maxHeight = accordionContent.scrollHeight + 'px';
            accordionIcon.style.transform = 'rotate(180deg)';
        } else {
            accordionContent.classList.add('collapsed');
            accordionContent.style.maxHeight = '0px';
            accordionIcon.style.transform = 'rotate(0deg)';
        }
    });

    function escapeHtml(str) {
        return (str||'').replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;').replace(/'/g, '&#039;');
    }

    function formatBytes(bytes, decimals = 2) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024, dm = decimals < 0 ? 0 : decimals;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i];
    }
});
