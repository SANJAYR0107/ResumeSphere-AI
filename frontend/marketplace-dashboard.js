/**
 * marketplace-dashboard.js
 * Handles UI interactions, API fetches, and dynamic DOM updates for Phase I.
 */

document.addEventListener('DOMContentLoaded', () => {
    // Mock Data for demonstration since we don't have a populated DB initially
    const mockGigs = [
        { id: 1, seller: "Alex D.", category: "development", title: "I will build a custom AI-powered web scraper", price: 150, rating: 4.9, icon: "bx-code-alt" },
        { id: 2, seller: "Sarah J.", category: "design", title: "I will design a premium portfolio website", price: 299, rating: 5.0, icon: "bx-palette" },
        { id: 3, seller: "Mike T.", category: "writing", title: "I will optimize your resume for ATS systems", price: 49, rating: 4.8, icon: "bx-file" },
        { id: 4, seller: "Elena R.", category: "development", title: "I will develop a Python data analysis script", price: 120, rating: 4.7, icon: "bx-data" }
    ];

    const mockProjects = [
        { id: 101, title: "Need a full-stack developer for a FinTech app MVP", skills: "React, Python, PostgreSQL", budget: 3500, deadline: "30 Days" },
        { id: 102, title: "UX/UI redesign for an enterprise recruitment platform", skills: "Figma, User Research", budget: 1200, deadline: "14 Days" }
    ];

    // Initialize UI
    renderGigs(mockGigs);
    renderRecommendations(mockGigs.slice(0, 2)); // Just taking first two as mock 'AI recommended'
    renderProjects(mockProjects);

    // Filter Logic
    const filterBtns = document.querySelectorAll('.filter-btn');
    filterBtns.forEach(btn => {
        btn.addEventListener('click', (e) => {
            // Update active class
            filterBtns.forEach(b => b.classList.remove('active'));
            e.target.classList.add('active');

            const filter = e.target.dataset.filter;
            if (filter === 'all') {
                renderGigs(mockGigs);
            } else {
                const filtered = mockGigs.filter(g => g.category === filter);
                renderGigs(filtered);
            }
        });
    });
});

function renderGigs(gigs) {
    const container = document.getElementById('gigs-container');
    container.innerHTML = '';

    gigs.forEach(gig => {
        const card = document.createElement('div');
        card.className = 'gig-card';
        card.innerHTML = `
            <div class="gig-img">
                <i class='bx ${gig.icon}'></i>
            </div>
            <div class="gig-content">
                <div class="gig-seller">
                    <img src="https://ui-avatars.com/api/?name=${gig.seller}&background=random&color=fff" alt="${gig.seller}">
                    <span>${gig.seller}</span>
                </div>
                <div class="gig-title">${gig.title}</div>
                <div class="gig-footer">
                    <div class="gig-rating"><i class='bx bxs-star'></i> ${gig.rating}</div>
                    <div class="gig-price">$${gig.price}</div>
                </div>
            </div>
        `;
        // Add click event for mock payment flow
        card.addEventListener('click', () => {
            showToast(`Initiating order for "${gig.title}" at $${gig.price}...`, 'success');
        });
        container.appendChild(card);
    });
}

function renderRecommendations(gigs) {
    const container = document.getElementById('recommendations-container');
    container.innerHTML = '';
    
    gigs.forEach(gig => {
        const card = document.createElement('div');
        card.className = 'gig-card';
        card.style.borderColor = 'rgba(139, 92, 246, 0.4)'; // Highlight recommended
        card.innerHTML = `
            <div class="gig-img" style="color: var(--brand-primary)">
                <i class='bx ${gig.icon}'></i>
            </div>
            <div class="gig-content">
                <div class="gig-seller">
                    <img src="https://ui-avatars.com/api/?name=${gig.seller}&background=random&color=fff" alt="${gig.seller}">
                    <span>${gig.seller}</span>
                </div>
                <div class="gig-title">${gig.title}</div>
                <div class="gig-footer">
                    <div class="gig-rating"><i class='bx bxs-star'></i> ${gig.rating}</div>
                    <div class="gig-price">$${gig.price}</div>
                </div>
            </div>
        `;
        container.appendChild(card);
    });
}

function renderProjects(projects) {
    const container = document.getElementById('projects-container');
    container.innerHTML = '';

    projects.forEach(proj => {
        const item = document.createElement('div');
        item.className = 'project-item';
        item.innerHTML = `
            <div class="project-info">
                <h3>${proj.title}</h3>
                <div class="project-meta">
                    <span><i class='bx bx-code-alt'></i> ${proj.skills}</span>
                    <span><i class='bx bx-time-five'></i> ${proj.deadline}</span>
                </div>
            </div>
            <div class="project-budget">
                <span class="amount">$${proj.budget}</span>
                <small>Fixed Budget</small>
                <button class="btn-outline" style="margin-top: 10px; font-size: 0.8rem; padding: 0.5rem 1rem;">Submit Proposal</button>
            </div>
        `;
        item.querySelector('button').addEventListener('click', () => {
            showToast(`Proposal submission opened for "${proj.title}"`, 'success');
        });
        container.appendChild(item);
    });
}

function showToast(message, type = 'info') {
    const container = document.getElementById('toast-container') || createToastContainer();
    
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.style.cssText = `
        background: var(--bg-panel);
        border-left: 4px solid var(--brand-primary);
        color: white;
        padding: 1rem;
        margin-bottom: 1rem;
        border-radius: 4px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.2);
        animation: slideIn 0.3s ease forwards;
        display: flex;
        align-items: center;
        gap: 1rem;
    `;
    
    toast.innerHTML = `
        <i class='bx bx-info-circle' style="font-size: 1.5rem; color: var(--brand-primary)"></i>
        <span>${message}</span>
    `;
    
    container.appendChild(toast);
    
    setTimeout(() => {
        toast.style.animation = 'slideOut 0.3s ease forwards';
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

function createToastContainer() {
    const container = document.createElement('div');
    container.id = 'toast-container';
    container.style.cssText = `
        position: fixed;
        bottom: 20px;
        right: 20px;
        z-index: 9999;
    `;
    document.body.appendChild(container);
    
    // Add animations to document if not present
    const style = document.createElement('style');
    style.textContent = `
        @keyframes slideIn { from { transform: translateX(100%); opacity: 0; } to { transform: translateX(0); opacity: 1; } }
        @keyframes slideOut { from { transform: translateX(0); opacity: 1; } to { transform: translateX(100%); opacity: 0; } }
    `;
    document.head.appendChild(style);
    
    return container;
}
