"""
skill_gap_service.py  —  Phase 3 Skill Gap Analysis Engine

Purpose
-------
Analyze the skill gap between a candidate's resume and their top recommended job role.
Generate detailed category scores and learning priorities.
"""

import logging

logger = logging.getLogger(__name__)

# Categories for grouping skills
SKILL_CATEGORIES = {
    "Programming": ["Python", "Java", "JavaScript", "TypeScript", "C++"],
    "Frameworks": ["React", "Angular", "Vue.js", "Spring Boot", "Django", "Flask", "Node.js", "Express", "FastAPI"],
    "Databases": ["SQL", "PostgreSQL", "MongoDB", "MySQL", "Redis"],
    "Cloud": ["AWS", "Azure", "GCP"],
    "DevOps": ["Docker", "Kubernetes", "CI/CD", "Terraform", "Ansible", "Linux", "Bash"],
    "AI/ML": ["Machine Learning", "Deep Learning", "PyTorch", "TensorFlow", "NLP", "Scikit-Learn", "LLMs"],
    "Testing": ["Manual Testing", "Automated Testing", "Selenium", "Cypress", "Appium", "API Testing"],
    "Version Control": ["Git", "GitHub", "GitLab"],
    "Soft Skills": ["Communication", "Leadership", "Teamwork", "Problem Solving"]
}

# Metadata for skills (importance, learning time, difficulty, resources)
SKILL_METADATA = {
    "Python": {"importance": "High", "learning_time": "3 weeks", "difficulty": "Medium", "recommended_resources": ["Python.org", "Coursera Python for Everybody"]},
    "Java": {"importance": "High", "learning_time": "4 weeks", "difficulty": "Medium", "recommended_resources": ["Codecademy Java", "Mooc.fi Java"]},
    "JavaScript": {"importance": "High", "learning_time": "3 weeks", "difficulty": "Medium", "recommended_resources": ["MDN Web Docs", "JavaScript.info"]},
    "TypeScript": {"importance": "High", "learning_time": "2 weeks", "difficulty": "Medium", "recommended_resources": ["TypeScript Handbook", "Frontend Masters"]},
    "React": {"importance": "High", "learning_time": "4 weeks", "difficulty": "Medium", "recommended_resources": ["React Docs", "Epic React by Kent C. Dodds"]},
    "Spring Boot": {"importance": "High", "learning_time": "4 weeks", "difficulty": "Hard", "recommended_resources": ["Spring Guides", "Baeldung Spring"]},
    "Django": {"importance": "High", "learning_time": "3 weeks", "difficulty": "Medium", "recommended_resources": ["Django Docs", "Corey Schafer Tutorials"]},
    "Node.js": {"importance": "High", "learning_time": "3 weeks", "difficulty": "Medium", "recommended_resources": ["Node.js Docs", "The Net Ninja"]},
    "SQL": {"importance": "Critical", "learning_time": "2 weeks", "difficulty": "Medium", "recommended_resources": ["SQLBolt", "Mode SQL Tutorial"]},
    "PostgreSQL": {"importance": "High", "learning_time": "2 weeks", "difficulty": "Medium", "recommended_resources": ["PostgreSQL Tutorial", "DataCamp"]},
    "MongoDB": {"importance": "Medium", "learning_time": "2 weeks", "difficulty": "Medium", "recommended_resources": ["MongoDB University"]},
    "AWS": {"importance": "High", "learning_time": "6 weeks", "difficulty": "Hard", "recommended_resources": ["AWS Skill Builder", "A Cloud Guru"]},
    "Docker": {"importance": "High", "learning_time": "2 weeks", "difficulty": "Medium", "recommended_resources": ["Docker Docs", "KodeKloud"]},
    "Kubernetes": {"importance": "High", "learning_time": "4 weeks", "difficulty": "Hard", "recommended_resources": ["Kubernetes Docs", "KubeAcademy"]},
    "CI/CD": {"importance": "High", "learning_time": "2 weeks", "difficulty": "Medium", "recommended_resources": ["GitHub Actions Docs", "Jenkins Tutorial"]},
    "Machine Learning": {"importance": "High", "learning_time": "8 weeks", "difficulty": "Hard", "recommended_resources": ["Andrew Ng ML Course", "Fast.ai"]},
    "PyTorch": {"importance": "High", "learning_time": "4 weeks", "difficulty": "Hard", "recommended_resources": ["PyTorch Tutorials", "DeepLizard"]},
    "Git": {"importance": "Critical", "learning_time": "1 week", "difficulty": "Easy", "recommended_resources": ["Pro Git Book", "Learn Git Branching"]},
}

def analyze_role_skill_gap(
    resume_skills: list[str],
    top_role_required_skills: list[str],
    top_role_preferred_skills: list[str]
) -> dict:
    """
    Generate skill gap analysis based on the resume and the top recommended role.
    """
    resume_lower = {s.lower() for s in resume_skills}
    
    missing_required = [s for s in top_role_required_skills if s.lower() not in resume_lower]
    missing_preferred = [s for s in top_role_preferred_skills if s.lower() not in resume_lower]
    
    all_role_skills = top_role_required_skills + top_role_preferred_skills
    matched_skills = [s for s in all_role_skills if s.lower() in resume_lower]
    
    overall_score = 0
    if len(all_role_skills) > 0:
        overall_score = int((len(matched_skills) / len(all_role_skills)) * 100)
        
    category_scores = {}
    for cat, cat_skills in SKILL_CATEGORIES.items():
        role_skills_in_cat = [s for s in all_role_skills if s in cat_skills]
        if not role_skills_in_cat:
            continue
        
        matched_in_cat = [s for s in role_skills_in_cat if s.lower() in resume_lower]
        score = int((len(matched_in_cat) / len(role_skills_in_cat)) * 100)
        category_scores[cat] = score
        
    missing_skill_details: list[dict] = []
    
    critical_skills: list[str] = []
    top_missing: list[str] = []
    nice_to_have: list[str] = []
    
    for skill in missing_required:
        metadata = SKILL_METADATA.get(skill, {
            "importance": "High",
            "learning_time": "2 weeks",
            "difficulty": "Medium",
            "recommended_resources": ["YouTube", "Official Documentation"]
        })
        detail = {
            "skill": skill,
            "priority": "P1 - Critical",
            "importance": metadata["importance"],
            "learning_time": metadata["learning_time"],
            "difficulty": metadata["difficulty"],
            "recommended_resources": metadata["recommended_resources"]
        }
        missing_skill_details.append(detail)
        critical_skills.append(skill)
        if len(top_missing) < 3:
            top_missing.append(skill)
            
    for skill in missing_preferred:
        metadata = SKILL_METADATA.get(skill, {
            "importance": "Medium",
            "learning_time": "2 weeks",
            "difficulty": "Medium",
            "recommended_resources": ["YouTube", "Official Documentation"]
        })
        detail = {
            "skill": skill,
            "priority": "P2 - Important",
            "importance": metadata["importance"],
            "learning_time": metadata["learning_time"],
            "difficulty": metadata["difficulty"],
            "recommended_resources": metadata["recommended_resources"]
        }
        missing_skill_details.append(detail)
        nice_to_have.append(skill)
        if len(top_missing) < 5:
            top_missing.append(skill)
            
    logger.info(f"skill_gap_service: overall_score={overall_score}, missing={len(missing_skill_details)}")
    
    return {
        "overall_score": overall_score,
        "category_scores": category_scores,
        "missing_skills": missing_skill_details,
        "top_missing_skills": top_missing,
        "critical_skills": critical_skills,
        "nice_to_have_skills": nice_to_have
    }

def analyze_skill_gap(matched_skills: list[str], missing_skills: list[str]) -> dict:
    """
    Legacy JD skill gap analysis to maintain backward compatibility with /skill-gap endpoint.
    """
    recommended_skills = []
    learning_suggestions = []
    
    for skill in missing_skills:
        skill_lower = skill.lower()
        if skill_lower in [s.lower() for s in SKILL_CATEGORIES.get("Cloud", [])]:
            recommended_skills.append(skill)
            learning_suggestions.append(f"Consider a cloud certification covering {skill}.")
        elif skill_lower in [s.lower() for s in SKILL_CATEGORIES.get("Programming", [])]:
            recommended_skills.append(skill)
            learning_suggestions.append(f"Practice {skill} algorithms on LeetCode.")
        else:
            recommended_skills.append(skill)
            learning_suggestions.append(f"Review standard tutorials and documentation for {skill}.")
            
    return {
        "matched_skills": matched_skills,
        "missing_skills": missing_skills,
        "recommended_skills": recommended_skills,
        "learning_suggestions": learning_suggestions
    }
