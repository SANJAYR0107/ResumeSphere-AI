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

    const API_URL = 'http://127.0.0.1:8000/api';

    // Radial Progress Configuration
    const radius = scoreRing.r.baseVal.value;
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

        if (percent >= 85) {
            scoreEvaluation.textContent = "Excellent Match Potential!";
            scoreEvaluation.style.color = "#00f2fe";
        } else if (percent >= 70) {
            scoreEvaluation.textContent = "Good Match Potential";
            scoreEvaluation.style.color = "#4facfe";
        } else {
            scoreEvaluation.textContent = "Needs Optimization";
            scoreEvaluation.style.color = "#e100ff";
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

        // Render ATS Score
        setScore(atsData.ats_score || 0);

        // Render Skills
        if (skillsGrid) {
            skillsGrid.innerHTML = analyzeData.skills.length > 0 
                ? analyzeData.skills.map(s => `<span class="skill-tag">${escapeHtml(s)}</span>`).join('')
                : '<span class="skill-tag">No skills detected</span>';
        }

        // Render Job Recommendations
        if (jobList) {
            if (recData.recommendations && recData.recommendations.length > 0) {
                jobList.innerHTML = recData.recommendations.map(job => `
                    <div style="background: rgba(255,255,255,0.03); padding: 1rem; border-radius: 8px; margin-bottom: 0.75rem; border-left: 3px solid #00f2fe;">
                        <h4 style="margin: 0 0 0.5rem 0; color: #fff;">${escapeHtml(job.title)} <span style="float: right; color: #00f2fe; font-size: 0.9rem;">${job.match_score}% Match</span></h4>
                        <p style="margin: 0 0 0.5rem 0; font-size: 0.85rem; color: #9aa2b1;">${escapeHtml(job.description)}</p>
                        <div style="font-size: 0.8rem; color: #10b981;"><i class="fa-solid fa-check"></i> Skills: ${job.matched_skills.slice(0,5).map(escapeHtml).join(', ')}</div>
                    </div>
                `).join('');
            } else {
                jobList.innerHTML = '<p style="color:var(--text-secondary);">No recommendations found.</p>';
            }
        }

        // Render Suggestions (from analyzeData.suggestions)
        if (suggestionsList && analyzeData.suggestions) {
            suggestionsList.innerHTML = analyzeData.suggestions.length > 0
                ? analyzeData.suggestions.map(s => `<li style="margin-bottom:8px; padding-left:20px; position:relative;"><i class="fa-solid fa-check text-accent" style="position:absolute; left:0; top:4px;"></i> ${escapeHtml(s)}</li>`).join('')
                : '<li style="color:#10b981;">No suggestions! Your resume is looking great.</li>';
        }

        // Extracted Text Accordion
        if (extractedTextDisplay) {
            extractedTextDisplay.textContent = analyzeData.clean_text || "No text extracted.";
        }
    }

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
