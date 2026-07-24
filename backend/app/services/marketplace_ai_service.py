import random
from typing import List, Dict, Any

class MarketplaceAIService:
    @staticmethod
    def recommend_gigs(user_skills: str, available_gigs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        AI Gig Recommendation Engine.
        Matches user skills with gig descriptions and categories.
        """
        if not available_gigs:
            return []
        
        user_skills_set = set([s.strip().lower() for s in user_skills.split(',')])
        
        scored_gigs = []
        for gig in available_gigs:
            gig_text = f"{gig.get('title', '')} {gig.get('description', '')}".lower()
            match_score = sum(1 for skill in user_skills_set if skill in gig_text)
            
            # Add some randomness to simulate discovery
            final_score = match_score + random.uniform(0, 0.5)
            scored_gigs.append((final_score, gig))
            
        # Sort by score descending
        scored_gigs.sort(key=lambda x: x[0], reverse=True)
        return [gig for score, gig in scored_gigs]

    @staticmethod
    def recommend_mentors(user_goals: str, available_mentors: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Mentor Recommendation Engine.
        """
        if not available_mentors:
            return []
            
        scored_mentors = []
        user_goals_lower = user_goals.lower()
        
        for mentor in available_mentors:
            expertise = str(mentor.get('expertise', '')).lower()
            bio = str(mentor.get('bio', '')).lower()
            rating = float(mentor.get('rating', 5.0))
            
            match_score = 0
            if any(word in expertise for word in user_goals_lower.split()):
                match_score += 2
            if any(word in bio for word in user_goals_lower.split()):
                match_score += 1
                
            final_score = match_score + (rating * 0.2) + random.uniform(0, 0.2)
            scored_mentors.append((final_score, mentor))
            
        scored_mentors.sort(key=lambda x: x[0], reverse=True)
        return [m for score, m in scored_mentors]

    @staticmethod
    def match_projects(freelancer_skills: str, open_projects: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Project Matching Engine.
        """
        if not open_projects:
            return []
            
        skills_set = set([s.strip().lower() for s in freelancer_skills.split(',')])
        scored_projects = []
        
        for proj in open_projects:
            req_skills = set([s.strip().lower() for s in proj.get('skills_required', '').split(',')])
            match_count = len(skills_set.intersection(req_skills))
            
            final_score = match_count + random.uniform(0, 0.5)
            scored_projects.append((final_score, proj))
            
        scored_projects.sort(key=lambda x: x[0], reverse=True)
        return [p for score, p in scored_projects]

    @staticmethod
    def suggest_pricing(category: str, skills: str, experience_level: str) -> Dict[str, float]:
        """
        Pricing Intelligence Engine.
        Suggests an optimal hourly rate or gig price.
        """
        base_rate = 20.0
        
        category_multipliers = {
            "Development": 1.5,
            "Design": 1.2,
            "Writing": 1.0,
            "Marketing": 1.1,
            "Data Science": 1.6
        }
        
        exp_multipliers = {
            "Beginner": 1.0,
            "Intermediate": 1.5,
            "Expert": 2.5
        }
        
        cat_mult = category_multipliers.get(category, 1.0)
        exp_mult = exp_multipliers.get(experience_level, 1.0)
        
        suggested_rate = base_rate * cat_mult * exp_mult
        
        return {
            "suggested_hourly_rate": round(suggested_rate, 2),
            "min_rate": round(suggested_rate * 0.8, 2),
            "max_rate": round(suggested_rate * 1.5, 2)
        }

    @staticmethod
    def calculate_trust_score(total_completed_orders: int, average_rating: float, account_age_days: int) -> float:
        """
        Trust Scoring Engine.
        Outputs a score from 0 to 100.
        """
        order_score = min(total_completed_orders * 2, 40) # Max 40 points from orders
        rating_score = (average_rating / 5.0) * 40 # Max 40 points from ratings
        age_score = min(account_age_days / 30, 20) # Max 20 points from age (approx 2 years)
        
        return round(order_score + rating_score + age_score, 1)

    @staticmethod
    def check_fraud(transaction_amount: float, user_trust_score: float, is_new_device: bool) -> Dict[str, Any]:
        """
        Fraud Detection Hooks.
        """
        risk_score = 0
        
        if transaction_amount > 1000:
            risk_score += 30
        if user_trust_score < 40:
            risk_score += 40
        if is_new_device:
            risk_score += 20
            
        return {
            "risk_score": risk_score,
            "is_flagged": risk_score >= 70,
            "reason": "High transaction value on new device with low trust score" if risk_score >= 70 else None
        }

    @staticmethod
    def forecast_demand(category: str) -> Dict[str, Any]:
        """
        Demand Forecasting.
        """
        trends = ["Increasing", "Stable", "Decreasing"]
        trend = "Increasing" if category in ["Development", "Data Science", "AI"] else random.choice(trends)
        
        return {
            "category": category,
            "demand_trend": trend,
            "forecast_growth_percentage": random.randint(5, 25) if trend == "Increasing" else random.randint(-10, 5)
        }

marketplace_ai = MarketplaceAIService()
