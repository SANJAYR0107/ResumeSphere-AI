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

    // =========================================================================
    // Phase 4: Intelligent Resume vs Job Description Optimization Engine Logic
    // =========================================================================
    const jdTabPaste = document.getElementById('jd-tab-paste');
    const jdTabUpload = document.getElementById('jd-tab-upload');
    const jdPasteContainer = document.getElementById('jd-paste-container');
    const jdUploadContainer = document.getElementById('jd-upload-container');
    const p4JdBrowseBtn = document.getElementById('p4-jd-browse-btn');
    const p4JdFileInput = document.getElementById('p4-jd-file-input');
    const p4JdFilenameDisplay = document.getElementById('p4-jd-filename-display');
    const p4RunOptimizationBtn = document.getElementById('p4-run-optimization-btn');
    const p4ResultsDashboard = document.getElementById('p4-results-dashboard');
    const p4DownloadPdfBtn = document.getElementById('p4-download-pdf-btn');

    let p4SelectedJdFile = null;
    let lastP4AnalysisData = null;

    if (jdTabPaste && jdTabUpload) {
        jdTabPaste.addEventListener('click', () => {
            jdTabPaste.classList.add('active');
            jdTabUpload.classList.remove('active');
            jdPasteContainer.classList.remove('hidden');
            jdUploadContainer.classList.add('hidden');
        });

        jdTabUpload.addEventListener('click', () => {
            jdTabUpload.classList.add('active');
            jdTabPaste.classList.remove('active');
            jdUploadContainer.classList.remove('hidden');
            jdPasteContainer.classList.add('hidden');
        });
    }

    if (p4JdBrowseBtn && p4JdFileInput) {
        p4JdBrowseBtn.addEventListener('click', () => p4JdFileInput.click());
        p4JdFileInput.addEventListener('change', (e) => {
            if (e.target.files.length > 0) {
                p4SelectedJdFile = e.target.files[0];
                p4JdFilenameDisplay.innerHTML = `<i class="fa-solid fa-file-pdf"></i> ${p4SelectedJdFile.name}`;
            }
        });
    }

    if (p4RunOptimizationBtn) {
        p4RunOptimizationBtn.addEventListener('click', () => {
            const pastedJdText = document.getElementById('p4-jd-text-input')?.value.trim();

            if (!currentResumeText) {
                alert("Please upload a PDF resume first at the top of the page.");
                return;
            }

            if (!pastedJdText && !p4SelectedJdFile) {
                alert("Please paste Job Description text or select a JD PDF file.");
                return;
            }

            const origHtml = p4RunOptimizationBtn.innerHTML;
            p4RunOptimizationBtn.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i> Running Optimization Engine...`;
            p4RunOptimizationBtn.disabled = true;

            const formData = new FormData();
            formData.append('resume_text', currentResumeText);
            
            if (p4SelectedJdFile && jdTabUpload.classList.contains('active')) {
                formData.append('jd_file', p4SelectedJdFile);
            } else {
                formData.append('jd_text', pastedJdText);
            }

            fetch(`${API_URL}/jd-analysis`, {
                method: 'POST',
                body: formData
            })
            .then(res => {
                if (!res.ok) return res.json().then(err => { throw new Error(err.detail || 'Analysis failed'); });
                return res.json();
            })
            .then(data => {
                lastP4AnalysisData = data;
                renderPhase4Results(data);
            })
            .catch(err => {
                alert("Phase 4 Optimization Failed: " + err.message);
            })
            .finally(() => {
                p4RunOptimizationBtn.innerHTML = origHtml;
                p4RunOptimizationBtn.disabled = false;
            });
        });
    }

    function renderPhase4Results(data) {
        if (!p4ResultsDashboard) return;
        p4ResultsDashboard.classList.remove('hidden');

        document.getElementById('p4-target-role-display').textContent = data.role_title || "Target Role Optimization";
        
        const confBadge = document.getElementById('p4-confidence-badge');
        if (confBadge) confBadge.textContent = (data.match_scores?.confidence || "High") + " Confidence";

        // 1. Scores
        document.getElementById('p4-overall-match-text').textContent = (data.match_scores?.overall_match || 0) + "%";
        document.getElementById('p4-ats-match-text').textContent = (data.match_scores?.ats_match || 0) + "%";
        document.getElementById('p4-semantic-match-text').textContent = (data.match_scores?.semantic_match || 0) + "%";
        document.getElementById('p4-keyword-match-text').textContent = (data.match_scores?.keyword_match || 0) + "%";

        // 2. ATS Simulator
        const sim = data.ats_simulator || {};
        document.getElementById('p4-sim-curr-score').textContent = sim.current_ats_score || 70;
        document.getElementById('p4-sim-pred-score').textContent = sim.predicted_ats_score || 88;
        document.getElementById('p4-sim-gain').textContent = sim.expected_improvement || 18;

        const simList = document.getElementById('p4-sim-changes-list');
        if (simList && sim.score_boosting_changes) {
            simList.innerHTML = sim.score_boosting_changes.map(item => `
                <div style="display:flex; justify-content:space-between; align-items:center; background:rgba(255,255,255,0.03); padding:8px 12px; border-radius:6px;">
                    <span style="font-size:0.85rem; color:var(--text-primary);"><i class="fa-solid fa-circle-plus" style="color:#10b981;"></i> ${escapeHtml(item.change)}</span>
                    <span style="font-size:0.8rem; font-weight:bold; color:#10b981; background:rgba(16,185,129,0.15); padding:2px 8px; border-radius:10px;">+${item.score_boost} pts</span>
                </div>
            `).join('');
        }

        // 3. Keywords
        const kw = data.keyword_analysis || {};
        const skillTag = s => `<span class="skill-tag" style="font-size:0.8rem; margin:2px;">${escapeHtml(s)}</span>`;
        
        document.getElementById('p4-matched-kws-container').innerHTML = (kw.matched_keywords || []).map(skillTag).join('') || 'None';
        document.getElementById('p4-important-missing-kws-container').innerHTML = (kw.important_missing_keywords || []).map(skillTag).join('') || 'None';
        document.getElementById('p4-missing-kws-container').innerHTML = (kw.missing_keywords || []).map(skillTag).join('') || 'None';
        document.getElementById('p4-extra-kws-container').innerHTML = (kw.extra_resume_skills || []).map(skillTag).join('') || 'None';

        // 4. Section Analysis
        const secGrid = document.getElementById('p4-section-analysis-grid');
        if (secGrid && data.section_analysis) {
            secGrid.innerHTML = Object.entries(data.section_analysis).map(([name, sec]) => {
                const color = sec.score >= 80 ? '#10b981' : (sec.score >= 60 ? '#f59e0b' : '#ef4444');
                return `
                    <div style="background:rgba(255,255,255,0.03); padding:12px; border-radius:8px; border:1px solid var(--border-color);">
                        <div style="display:flex; justify-content:space-between; margin-bottom:6px;">
                            <strong style="color:#fff; font-size:0.9rem;">${escapeHtml(name)}</strong>
                            <span style="color:${color}; font-weight:bold; font-size:0.9rem;">${sec.score}%</span>
                        </div>
                        <p style="font-size:0.8rem; color:var(--text-secondary); margin:0 0 6px 0;">${escapeHtml(sec.explanation)}</p>
                    </div>
                `;
            }).join('');
        }

        // 5. Rewrites
        const rw = data.rewrite_suggestions || {};
        document.getElementById('p4-rewrite-summary').textContent = rw.professional_summary || '';
        document.getElementById('p4-rewrite-bullets').innerHTML = (rw.experience_bullets || []).map(b => `<li style="margin-bottom:4px;">${escapeHtml(b)}</li>`).join('');
        document.getElementById('p4-rewrite-projects').innerHTML = (rw.project_descriptions || []).map(p => `<li style="margin-bottom:4px;">${escapeHtml(p)}</li>`).join('');

        // 6. Interview & Learning
        const ia = data.interview_alignment || {};
        document.getElementById('p4-interview-tech-q').innerHTML = (ia.technical_questions || []).map(q => `<li>${escapeHtml(q)}</li>`).join('');
        document.getElementById('p4-interview-coding-topics').innerHTML = (ia.coding_topics || []).concat(ia.system_design_topics || []).map(t => `<li>${escapeHtml(t)}</li>`).join('');

        const lrContainer = document.getElementById('p4-learning-roadmap-container');
        if (lrContainer && data.learning_recommendations) {
            lrContainer.innerHTML = data.learning_recommendations.map(lr => `
                <div style="background:rgba(0,0,0,0.2); padding:10px; border-radius:6px;">
                    <div style="display:flex; justify-content:space-between;">
                        <strong style="color:#fff; font-size:0.85rem;">${escapeHtml(lr.skill)}</strong>
                        <span style="font-size:0.75rem; color:#10b981;">${escapeHtml(lr.estimated_learning_time)}</span>
                    </div>
                    <div style="font-size:0.75rem; color:var(--text-secondary); margin-top:4px;">Resource: <a href="#" style="color:#4facfe;">${escapeHtml((lr.recommended_free_resources||[])[0]||'Docs')}</a></div>
                </div>
            `).join('');
        }

        // Scroll smooth to dashboard
        p4ResultsDashboard.scrollIntoView({ behavior: 'smooth' });
    }

    if (p4DownloadPdfBtn) {
        p4DownloadPdfBtn.addEventListener('click', () => {
            if (!lastP4AnalysisData) {
                alert("Please run Phase 4 Optimization Engine first.");
                return;
            }

            p4DownloadPdfBtn.disabled = true;
            p4DownloadPdfBtn.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i> Generating PDF...`;

            fetch(`${API_URL}/download-report`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(lastP4AnalysisData)
            })
            .then(res => {
                if (!res.ok) throw new Error("Failed to generate PDF report.");
                return res.blob();
            })
            .then(blob => {
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.style.display = 'none';
                a.href = url;
                a.download = 'ResumeSphere_Optimization_Report.pdf';
                document.body.appendChild(a);
                a.click();
                window.URL.revokeObjectURL(url);
            })
            .catch(err => alert("Error downloading PDF: " + err.message))
            .finally(() => {
                p4DownloadPdfBtn.disabled = false;
                p4DownloadPdfBtn.innerHTML = `<i class="fa-solid fa-file-pdf"></i> Download PDF Optimization Report`;
            });
        });
    }

    // =========================================================================
    // Phase B: AI Interview Platform & Interactive Simulator Logic
    // =========================================================================
    const pbStartBtn = document.getElementById('pb-start-interview-btn');
    const pbSessionWorkspace = document.getElementById('pb-session-workspace');
    const pbQIndexText = document.getElementById('pb-q-index-text');
    const pbQTotalText = document.getElementById('pb-q-total-text');
    const pbQTimerText = document.getElementById('pb-q-timer-text');
    const pbProgressFill = document.getElementById('pb-progress-fill');
    const pbQCategoryBadge = document.getElementById('pb-q-category-badge');
    const pbQSkillBadge = document.getElementById('pb-q-skill-badge');
    const pbQTextDisplay = document.getElementById('pb-q-text-display');
    const pbQHintDisplay = document.getElementById('pb-q-hint-display');
    const pbAnswerInput = document.getElementById('pb-answer-input');
    const pbSubmitAnswerBtn = document.getElementById('pb-submit-answer-btn');
    const pbSkipQBtn = document.getElementById('pb-skip-q-btn');
    const pbEvalOutputCard = document.getElementById('pb-eval-output-card');
    const pbDownloadReportBtn = document.getElementById('pb-download-interview-report-btn');

    let currentPbSession = null;
    let pbTimerInterval = null;
    let pbTimerSeconds = 45;

    if (pbStartBtn) {
        pbStartBtn.addEventListener('click', () => {
            const targetRole = document.getElementById('pb-target-role-input')?.value || "Software Engineer";
            const targetCompany = document.getElementById('pb-target-company-input')?.value || "Tech Corporation";
            const difficulty = document.getElementById('pb-difficulty-select')?.value || "Medium";
            const count = parseInt(document.getElementById('pb-count-select')?.value || "5", 10);

            const origHtml = pbStartBtn.innerHTML;
            pbStartBtn.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i> Initializing Session...`;
            pbStartBtn.disabled = true;

            fetch(`${API_URL}/interview/session/start`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    resume_skills: extractedSkillsList || ["Python", "SQL"],
                    missing_skills: [],
                    interview_type: "Experienced",
                    difficulty: difficulty,
                    question_count: count,
                    target_role: targetRole,
                    target_company: targetCompany
                })
            })
            .then(res => {
                if (!res.ok) throw new Error("Failed to start interview session.");
                return res.json();
            })
            .then(session => {
                currentPbSession = session;
                renderPbQuestion(0);
                pbSessionWorkspace.classList.remove('hidden');
                pbSessionWorkspace.scrollIntoView({ behavior: 'smooth' });
            })
            .catch(err => alert("Error: " + err.message))
            .finally(() => {
                pbStartBtn.innerHTML = origHtml;
                pbStartBtn.disabled = false;
            });
        });
    }

    function renderPbQuestion(idx) {
        if (!currentPbSession || !currentPbSession.questions[idx]) return;
        const q = currentPbSession.questions[idx];

        pbQIndexText.textContent = idx + 1;
        pbQTotalText.textContent = currentPbSession.total_questions;
        pbProgressFill.style.width = `${((idx + 1) / currentPbSession.total_questions) * 100}%`;

        pbQCategoryBadge.textContent = q.category;
        pbQSkillBadge.textContent = `Target: ${q.target_skill}`;
        pbQTextDisplay.textContent = q.question_text;
        pbQHintDisplay.textContent = q.sample_answer_hint ? `Hint: ${q.sample_answer_hint}` : '';
        pbAnswerInput.value = '';
        pbEvalOutputCard.classList.add('hidden');

        startPbTimer();
    }

    function startPbTimer() {
        clearInterval(pbTimerInterval);
        pbTimerSeconds = 45;
        pbQTimerText.textContent = `00:45`;

        pbTimerInterval = setInterval(() => {
            pbTimerSeconds--;
            const secs = pbTimerSeconds < 10 ? `0${pbTimerSeconds}` : pbTimerSeconds;
            pbQTimerText.textContent = `00:${secs}`;

            if (pbTimerSeconds <= 0) {
                clearInterval(pbTimerInterval);
            }
        }, 1000);
    }

    function handleAnswerSubmit(isSkip = false) {
        if (!currentPbSession) return;
        const currentIdx = currentPbSession.current_question_index || 0;
        const q = currentPbSession.questions[currentIdx];
        const answerText = pbAnswerInput.value.trim();

        if (!isSkip && !answerText) {
            alert("Please type your answer or click 'Skip Question'.");
            return;
        }

        clearInterval(pbTimerInterval);

        pbSubmitAnswerBtn.disabled = true;
        pbSubmitAnswerBtn.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i> Evaluating...`;

        fetch(`${API_URL}/interview/session/submit-answer`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                session_id: currentPbSession.session_id,
                question_id: q.question_id,
                candidate_answer: answerText,
                time_spent_seconds: 45 - pbTimerSeconds,
                skip: isSkip
            })
        })
        .then(res => {
            if (!res.ok) throw new Error("Failed to evaluate answer.");
            return res.json();
        })
        .then(data => {
            renderEvaluationFeedback(data.evaluation);
            currentPbSession.current_question_index = data.current_question_index;

            if (data.status === "COMPLETED") {
                alert("🎉 Interview Session Completed! You can download your PDF performance report below.");
            }
        })
        .catch(err => alert("Error: " + err.message))
        .finally(() => {
            pbSubmitAnswerBtn.disabled = false;
            pbSubmitAnswerBtn.innerHTML = `<i class="fa-solid fa-paper-plane"></i> Submit Answer for AI Evaluation`;
        });
    }

    if (pbSubmitAnswerBtn) pbSubmitAnswerBtn.addEventListener('click', () => handleAnswerSubmit(false));
    if (pbSkipQBtn) pbSkipQBtn.addEventListener('click', () => handleAnswerSubmit(true));

    function renderEvaluationFeedback(evalRes) {
        if (!evalRes || !pbEvalOutputCard) return;

        document.getElementById('pb-eval-score-text').textContent = evalRes.overall_score || 0;
        document.getElementById('pb-eval-comm-text').textContent = `Communication: ${evalRes.communication_score || 0}/10`;

        document.getElementById('pb-eval-strengths').innerHTML = (evalRes.strengths || []).map(s => `<li>${escapeHtml(s)}</li>`).join('');
        document.getElementById('pb-eval-weaknesses').innerHTML = (evalRes.weaknesses || []).map(w => `<li>${escapeHtml(w)}</li>`).join('');
        
        const followupBox = document.getElementById('pb-followup-box');
        if (evalRes.follow_up_question) {
            document.getElementById('pb-followup-text').textContent = evalRes.follow_up_question;
            followupBox.classList.remove('hidden');
        } else {
            followupBox.classList.add('hidden');
        }

        pbEvalOutputCard.classList.remove('hidden');
    }

    if (pbDownloadReportBtn) {
        pbDownloadReportBtn.addEventListener('click', () => {
            if (!currentPbSession) {
                alert("Please start an interview session first.");
                return;
            }

            pbDownloadReportBtn.disabled = true;
            pbDownloadReportBtn.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i> Generating PDF...`;

            fetch(`${API_URL}/interview/download-report`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ session_id: currentPbSession.session_id })
            })
            .then(res => {
                if (!res.ok) throw new Error("Failed to generate PDF interview report.");
                return res.blob();
            })
            .then(blob => {
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.style.display = 'none';
                a.href = url;
                a.download = 'ResumeSphere_Interview_Report.pdf';
                document.body.appendChild(a);
                a.click();
                window.URL.revokeObjectURL(url);
            })
            .catch(err => alert("Error downloading PDF: " + err.message))
            .finally(() => {
                pbDownloadReportBtn.disabled = false;
                pbDownloadReportBtn.innerHTML = `<i class="fa-solid fa-file-pdf"></i> Download PDF Interview Report`;
            });
        });
    }

    // =========================================================================
    // Phase C: AI Career Assistant Chat & Cover Letter Logic
    // =========================================================================
    const pcChatInput = document.getElementById('pc-chat-input');
    const pcChatSendBtn = document.getElementById('pc-chat-send-btn');
    const pcChatBox = document.getElementById('pc-chat-box');

    if (pcChatSendBtn && pcChatInput) {
        pcChatSendBtn.addEventListener('click', () => {
            const query = pcChatInput.value.trim();
            if (!query) return;

            // Append User Message
            pcChatBox.innerHTML += `<div style="text-align: right; margin-bottom: 8px;"><span style="background: rgba(245, 158, 11, 0.2); padding: 4px 10px; border-radius: 12px; font-size: 0.8rem; color: #f59e0b;">${escapeHtml(query)}</span></div>`;
            pcChatInput.value = '';
            pcChatBox.scrollTop = pcChatBox.scrollHeight;

            fetch(`${API_URL}/career/chat`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    query: query,
                    resume_skills: extractedSkillsList || ["Python", "SQL"],
                    ats_score: 75,
                    missing_skills: ["Docker", "AWS"],
                    target_role: "Software Engineer"
                })
            })
            .then(res => res.json())
            .then(data => {
                const respText = data.assistant_response || "No response received.";
                pcChatBox.innerHTML += `<div style="text-align: left; margin-bottom: 8px;"><span style="background: rgba(255,255,255,0.08); padding: 6px 10px; border-radius: 12px; font-size: 0.8rem; color: #fff; display: inline-block;">${escapeHtml(respText).replace(/\n/g, '<br/>')}</span></div>`;
                pcChatBox.scrollTop = pcChatBox.scrollHeight;
            })
            .catch(err => {
                pcChatBox.innerHTML += `<div style="color: #ef4444; font-size: 0.8rem;">Error: ${err.message}</div>`;
            });
        });
    }

    const pcClGenerateBtn = document.getElementById('pc-cl-generate-btn');
    const pcClOutputPreview = document.getElementById('pc-cl-output-preview');

    if (pcClGenerateBtn) {
        pcClGenerateBtn.addEventListener('click', () => {
            const candidate = document.getElementById('pc-cl-candidate')?.value || "Jane Doe";
            const company = document.getElementById('pc-cl-company')?.value || "Tech Corporation";
            const role = document.getElementById('pc-cl-role')?.value || "Software Engineer";
            const type = document.getElementById('pc-cl-type')?.value || "Experienced";

            pcClGenerateBtn.disabled = true;
            pcClGenerateBtn.textContent = "Generating Cover Letter...";

            fetch(`${API_URL}/career/cover-letter/generate`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    candidate_name: candidate,
                    company_name: company,
                    target_role: role,
                    experience_type: type,
                    resume_skills: extractedSkillsList || ["Java", "Spring Boot"]
                })
            })
            .then(res => res.json())
            .then(data => {
                pcClOutputPreview.innerHTML = `<strong>Generated Cover Letter:</strong><br/>${escapeHtml(data.cover_letter_text).replace(/\n/g, '<br/>')}`;
                pcClOutputPreview.classList.remove('hidden');
            })
            .catch(err => alert("Error: " + err.message))
            .finally(() => {
                pcClGenerateBtn.disabled = false;
                pcClGenerateBtn.textContent = "Generate Cover Letter";
            });
        });
    }
});

