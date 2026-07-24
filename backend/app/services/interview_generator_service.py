"""
interview_generator_service.py - Phase B AI Interview Generator Service

Purpose
-------
Generates personalized, high-yield interview questions across Technical, HR,
Behavioral, Coding, and Managerial domains. Tailors questions based on candidate
resume skills, missing skills, experience level, target role, and target company.
"""

import logging
import random
from typing import TypedDict, Any

logger = logging.getLogger(__name__)


class InterviewQuestion(TypedDict):
    question_id: str
    category: str  # "Technical", "HR", "Behavioral", "Coding", "Managerial"
    difficulty: str  # "Easy", "Medium", "Hard"
    question_text: str
    target_skill: str
    expected_key_concepts: list[str]
    sample_answer_hint: str


class InterviewQuestionSet(TypedDict):
    session_id: str
    target_role: str
    target_company: str
    interview_type: str  # "Fresher", "Experienced", "Internship"
    difficulty: str
    total_questions: int
    questions: list[InterviewQuestion]


TECHNICAL_QUESTION_BANK: dict[str, list[dict[str, Any]]] = {
    "java": [
        {
            "question": "Explain Java Garbage Collection algorithms and how the JVM manages generational heap space (Young vs Old Gen).",
            "concepts": ["Garbage Collection", "Generational Heap", "Eden Space", "G1GC / ZGC", "Memory Leaks"],
            "hint": "Mention Eden space, Survivor spaces, Tenured generation, and G1GC pause-time optimization."
        },
        {
            "question": "How does Spring Boot Dependency Injection work under the hood? Contrast @Bean vs @Component.",
            "concepts": ["Dependency Injection", "IOC Container", "Bean Lifecycle", "Component Scanning"],
            "hint": "Explain how ApplicationContext scans components and wires dependencies via reflection."
        }
    ],
    "python": [
        {
            "question": "Explain Python GIL (Global Interpreter Lock) and how multiprocessing differs from multithreading for I/O vs CPU bound tasks.",
            "concepts": ["GIL", "Multiprocessing", "Threading", "Asyncio", "Concurrency"],
            "hint": "Discuss CPython execution lock, GIL release during I/O operations, and process memory isolation."
        },
        {
            "question": "How do Python decorators work? Write a concept explanation of a decorator function with arguments.",
            "concepts": ["Decorators", "First-class functions", "Closures", "*args and **kwargs"],
            "hint": "Explain higher-order functions wrapping target functions to inject cross-cutting logic like logging or timing."
        }
    ],
    "docker": [
        {
            "question": "How do multi-stage Docker builds reduce container image size and enhance security?",
            "concepts": ["Multi-stage builds", "Layer caching", "Non-root user", "Minimal base images"],
            "hint": "Explain builder stage compiling artifacts vs clean minimal runner stage without build tools."
        }
    ],
    "sql": [
        {
            "question": "How do B-Tree indexes improve database SELECT query performance, and when can indexing hurt write performance?",
            "concepts": ["B-Tree Indexes", "Query Optimizer", "Index Overhead", "Execution Plan"],
            "hint": "Discuss log-time lookup O(log N) vs write penalty during INSERT/UPDATE operations."
        }
    ]
}

GENERIC_QUESTIONS: dict[str, list[dict[str, Any]]] = {
    "HR": [
        {
            "question": "Why do you want to join {company} as a {role}, and what makes your background a strong fit?",
            "concepts": ["Company Values", "Role Alignment", "Career Trajectory", "Motivation"],
            "hint": "Connect your past achievements directly to company goals and growth trajectory."
        },
        {
            "question": "Where do you see your technical leadership evolving over the next 3 to 5 years?",
            "concepts": ["Growth Mindset", "Leadership", "Skill Mastership", "Ownership"],
            "hint": "Focus on driving architectural impact, mentoring peers, and expanding domain mastery."
        }
    ],
    "Behavioral": [
        {
            "question": "Describe a situation where you encountered a critical production issue under high time pressure. How did you diagnose and resolve it?",
            "concepts": ["STAR Method", "Root Cause Analysis", "Incident Response", "Blameless Post-Mortem"],
            "hint": "Use the STAR method: Situation, Task, Action taken, and measurable Result."
        },
        {
            "question": "Tell me about a technical disagreement you had with a senior teammate regarding architecture. How did you handle it?",
            "concepts": ["Technical Collaboration", "Data-driven Decisions", "Conflict Resolution", "Trade-off Evaluation"],
            "hint": "Emphasize benchmark evidence, listening to alternative perspectives, and aligning on team consensus."
        }
    ],
    "Managerial": [
        {
            "question": "How do you handle technical debt vs delivering high-priority business features under aggressive sprint deadlines?",
            "concepts": ["Technical Debt", "Sprint Planning", "Risk Mitigation", "Refactoring Strategy"],
            "hint": "Explain reserving fixed capacity (e.g. 20%) for refactoring and framing tech debt in business risk terms."
        }
    ],
    "Coding": [
        {
            "question": "Given an array of integers, write an efficient algorithm to find two numbers that sum up to a specific target.",
            "concepts": ["Hash Map", "Two Pointers", "Time Complexity O(N)", "Space-Time Tradeoff"],
            "hint": "Use a Hash Map to store complement values during a single linear pass O(N)."
        },
        {
            "question": "Implement a Function to Reverse a Linked List iteratively in O(N) time and O(1) space.",
            "concepts": ["Linked List", "Pointer Manipulation", "In-Place Algorithm", "Boundary Cases"],
            "hint": "Track previous, current, and next pointers during single traversal."
        }
    ]
}


def generate_interview_questions(
    resume_skills: list[str],
    missing_skills: list[str],
    interview_type: str = "Experienced",
    difficulty: str = "Medium",
    question_count: int = 5,
    target_role: str = "Software Engineer",
    target_company: str = "Tech Corporation"
) -> list[InterviewQuestion]:
    """Generate personalized interview questions based on candidate profile and target requirements."""
    
    questions: list[InterviewQuestion] = []
    skill_pool = [s.strip().lower() for s in (resume_skills + missing_skills) if s.strip()]
    if not skill_pool:
        skill_pool = ["python", "java", "sql", "docker"]

    q_counter = 1

    # 1. Technical Questions (50% of quota)
    tech_count = max(1, question_count // 2)
    for _ in range(tech_count):
        selected_skill = random.choice(skill_pool)
        matched_bank = TECHNICAL_QUESTION_BANK.get(selected_skill)
        
        if matched_bank:
            q_info = random.choice(matched_bank)
            questions.append(InterviewQuestion(
                question_id=f"q_{q_counter}",
                category="Technical",
                difficulty=difficulty,
                question_text=q_info["question"],
                target_skill=selected_skill.title(),
                expected_key_concepts=q_info["concepts"],
                sample_answer_hint=q_info["hint"]
            ))
        else:
            questions.append(InterviewQuestion(
                question_id=f"q_{q_counter}",
                category="Technical",
                difficulty=difficulty,
                question_text=f"How do you design, optimize, and test enterprise applications using {selected_skill.title()}?",
                target_skill=selected_skill.title(),
                expected_key_concepts=[selected_skill.title(), "System Design", "Testing", "Performance Tuning"],
                sample_answer_hint=f"Highlight core principles, architecture patterns, and tools used with {selected_skill.title()}."
            ))
        q_counter += 1

    # 2. Behavioral Questions
    for q_info in GENERIC_QUESTIONS["Behavioral"]:
        if len(questions) >= question_count:
            break
        questions.append(InterviewQuestion(
            question_id=f"q_{q_counter}",
            category="Behavioral",
            difficulty=difficulty,
            question_text=q_info["question"],
            target_skill="Problem Solving & Teamwork",
            expected_key_concepts=q_info["concepts"],
            sample_answer_hint=q_info["hint"]
        ))
        q_counter += 1

    # 3. HR Questions
    for q_info in GENERIC_QUESTIONS["HR"]:
        if len(questions) >= question_count:
            break
        formatted_q = q_info["question"].format(company=target_company, role=target_role)
        questions.append(InterviewQuestion(
            question_id=f"q_{q_counter}",
            category="HR",
            difficulty=difficulty,
            question_text=formatted_q,
            target_skill="Cultural Fit & Motivation",
            expected_key_concepts=q_info["concepts"],
            sample_answer_hint=q_info["hint"]
        ))
        q_counter += 1

    # 4. Coding / Managerial Questions fill-in
    categories_cycle = ["Coding", "Managerial"]
    cycle_idx = 0
    while len(questions) < question_count:
        cat = categories_cycle[cycle_idx % len(categories_cycle)]
        q_info = random.choice(GENERIC_QUESTIONS[cat])
        questions.append(InterviewQuestion(
            question_id=f"q_{q_counter}",
            category=cat,
            difficulty=difficulty,
            question_text=q_info["question"],
            target_skill=cat,
            expected_key_concepts=q_info["concepts"],
            sample_answer_hint=q_info["hint"]
        ))
        q_counter += 1
        cycle_idx += 1

    return questions[:question_count]
