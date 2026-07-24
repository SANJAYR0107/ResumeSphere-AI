import random
from typing import Dict, Any, List
from datetime import datetime, timedelta

class CopilotAIService:
    def __init__(self):
        self.coordinator = CoordinatorAgent(self)

    def dispatch_query(self, query: str, user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Routes a natural language query to the appropriate specialized agent."""
        return self.coordinator.route(query, user_context)

    def analyze_salary(self, job_title: str, location: str, current_salary: float) -> Dict[str, Any]:
        """Provides salary benchmarking and negotiation tips."""
        # Simulated logic
        market_median = current_salary * random.uniform(0.9, 1.2) if current_salary else 120000.0
        return {
            "job_title": job_title,
            "market_median": market_median,
            "min_expected": market_median * 0.85,
            "max_expected": market_median * 1.15,
            "negotiation_tip": "Focus on your recent architectural leadership experience to push for the upper quartile."
        }

    def monitor_skills(self, current_skills: List[str]) -> Dict[str, Any]:
        """Skill Gap Detection and Trending Skills alert."""
        trending = ["GraphQL", "Rust", "Generative AI", "Web3"]
        gaps = [skill for skill in trending if skill.lower() not in [s.lower() for s in current_skills]]
        return {
            "trending_skills": trending,
            "skill_gaps": gaps[:2],
            "recommendation": f"Consider picking up {gaps[0] if gaps else 'a new framework'} to stay competitive."
        }

    def generate_career_plan(self, goal: str) -> List[Dict[str, Any]]:
        """Generates a weekly breakdown for a career goal."""
        return [
            {"week": 1, "task": f"Research requirements for {goal}"},
            {"week": 2, "task": "Update resume and LinkedIn profile"},
            {"week": 3, "task": "Begin targeted networking and mock interviews"},
            {"week": 4, "task": "Submit first batch of applications"}
        ]


class CoordinatorAgent:
    """The central orchestrator of the Multi-Agent system."""
    def __init__(self, copilot_service: CopilotAIService):
        self.service = copilot_service

    def route(self, query: str, context: Dict[str, Any]) -> Dict[str, Any]:
        q_lower = query.lower()
        if "salary" in q_lower or "offer" in q_lower or "negotiate" in q_lower:
            return self._handle_salary_agent(query, context)
        elif "skill" in q_lower or "learn" in q_lower or "trend" in q_lower:
            return self._handle_learning_agent(query, context)
        elif "goal" in q_lower or "plan" in q_lower or "achieve" in q_lower:
            return self._handle_planning_agent(query, context)
        elif "resume" in q_lower or "cv" in q_lower:
            return self._handle_resume_agent(query, context)
        else:
            return {
                "agent": "Career Coach",
                "response": "I'm here to help with your career! You can ask me to analyze a salary offer, check your skills against market trends, or help you plan a career goal."
            }

    def _handle_salary_agent(self, query: str, context: Dict[str, Any]) -> Dict[str, Any]:
        res = self.service.analyze_salary(context.get("title", "Software Engineer"), context.get("location", "Remote"), context.get("current_salary", 0))
        return {
            "agent": "Salary Agent",
            "response": f"Based on the market, the median salary is ${res['market_median']:,.2f}. {res['negotiation_tip']}",
            "data": res
        }

    def _handle_learning_agent(self, query: str, context: Dict[str, Any]) -> Dict[str, Any]:
        res = self.service.monitor_skills(context.get("skills", []))
        return {
            "agent": "Learning Agent",
            "response": res["recommendation"],
            "data": res
        }

    def _handle_planning_agent(self, query: str, context: Dict[str, Any]) -> Dict[str, Any]:
        goal = "getting a promotion" if "promotion" in query else "finding a new job"
        res = self.service.generate_career_plan(goal)
        return {
            "agent": "Planning Agent",
            "response": f"I've generated a 4-week plan for {goal}.",
            "data": {"plan": res}
        }
        
    def _handle_resume_agent(self, query: str, context: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "agent": "Resume Agent",
            "response": "Your resume is currently scoring 85%. Consider adding more quantified metrics to the 'Experience' section to boost it to 90%+.",
            "data": {"score": 85}
        }

copilot_ai = CopilotAIService()
