import random
from typing import List, Dict, Any

class NetworkAIService:
    @staticmethod
    def recommend_connections(user_skills: str, all_profiles: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Suggests professional connections based on skill overlap and industry.
        """
        if not all_profiles:
            return []
            
        user_skills_set = set([s.strip().lower() for s in user_skills.split(',')])
        
        scored_profiles = []
        for profile in all_profiles:
            prof_skills = set([s.strip().lower() for s in profile.get('skills', '').split(',')])
            overlap = len(user_skills_set.intersection(prof_skills))
            
            # Simple heuristic: heavily weight overlap, add random factor for discovery
            score = (overlap * 2) + random.uniform(0, 1.5)
            scored_profiles.append((score, profile))
            
        scored_profiles.sort(key=lambda x: x[0], reverse=True)
        return [p for score, p in scored_profiles]

    @staticmethod
    def match_teams(project_requirements: str, available_users: List[Dict[str, Any]], team_size: int = 3) -> List[Dict[str, Any]]:
        """
        AI Team Formation logic. Matches complementary skills.
        """
        if len(available_users) < team_size:
            return available_users
            
        req_skills = [s.strip().lower() for s in project_requirements.split(',')]
        team = []
        
        # Iteratively pick best candidate to fill missing skills
        covered_skills = set()
        candidates = available_users.copy()
        
        for _ in range(team_size):
            best_candidate = None
            best_score = -1
            
            for c in candidates:
                c_skills = set([s.strip().lower() for s in c.get('skills', '').split(',')])
                # Score based on how many NEW required skills this candidate brings
                new_skills = c_skills.intersection(req_skills) - covered_skills
                score = len(new_skills) + random.uniform(0, 0.5)
                
                if score > best_score:
                    best_score = score
                    best_candidate = c
                    
            if best_candidate:
                team.append(best_candidate)
                c_skills = set([s.strip().lower() for s in best_candidate.get('skills', '').split(',')])
                covered_skills.update(c_skills.intersection(req_skills))
                candidates.remove(best_candidate)
                
        return team

    @staticmethod
    def semantic_search_network(query: str, entities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Mock semantic search for posts, people, communities.
        """
        query_terms = set(query.lower().split())
        
        scored_entities = []
        for entity in entities:
            text = f"{entity.get('title', '')} {entity.get('description', '')} {entity.get('content', '')}".lower()
            score = sum(1 for term in query_terms if term in text)
            
            if score > 0:
                score += random.uniform(0, 0.5)
                scored_entities.append((score, entity))
                
        scored_entities.sort(key=lambda x: x[0], reverse=True)
        return [e for score, e in scored_entities]

    @staticmethod
    def analyze_influence(connections_count: int, posts_count: int, total_reactions: int) -> float:
        """
        Calculates Network Influence Score (0-100).
        """
        conn_score = min(connections_count / 10.0, 30) # Max 30 from connections
        post_score = min(posts_count * 2.0, 30)        # Max 30 from posting volume
        react_score = min(total_reactions / 5.0, 40)   # Max 40 from engagement
        
        return round(conn_score + post_score + react_score, 1)

network_ai = NetworkAIService()
