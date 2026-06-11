import re
import numpy as np
from sentence_transformers import SentenceTransformer
from typing import List, Dict, Any
from semantic_mapper import NormalizedProfile

# Load a lightweight, performant semantic model
embedding_model = SentenceTransformer('all-MiniLM-L6-v2')

class RankingEngine:
    @staticmethod
    def calculate_cosine_similarity(vec_a: np.ndarray, vec_b: np.ndarray) -> float:
        dot_product = np.dot(vec_a, vec_b)
        norm_a = np.linalg.norm(vec_a)
        norm_b = np.linalg.norm(vec_b)
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return float(dot_product / (norm_a * norm_b))

    @classmethod
    def rank_candidates(cls, job_description: str, profiles: List[NormalizedProfile]) -> List[Dict[str, Any]]:
        ranked_list = []
        jd_vector = embedding_model.encode(job_description)

        # Parse target criteria from the JD text to inform constraints
        target_years = 3.0
        jd_lower = job_description.lower()
        exp_match = re.search(r'(\d+)\+?\s*(?:years?|yrs?)', jd_lower)
        if exp_match:
            target_years = float(exp_match.group(1))

        for profile in profiles:
            # Combine skills and summaries for complete candidate vectors
            profile_payload = f"Skills: {', '.join(profile.top_skills)}. Overview: {profile.experience_summary}"
            profile_vector = embedding_model.encode(profile_payload)

            # 1. Semantic Cosine Vector Score Base (0 to 100)
            semantic_score = cls.calculate_cosine_similarity(jd_vector, profile_vector) * 100
            
            # 2. Hard constraint tuning logic (Weighted experience alignment)
            if profile.years_of_experience >= target_years:
                experience_weight = 100.0
            else:
                # Apply penalty for shortfall matching
                experience_weight = (profile.years_of_experience / target_years) * 100

            # Combined system formula weight distribution: 60% Semantic Match + 40% Experience Depth
            final_compatibility_score = (semantic_score * 0.6) + (experience_weight * 0.4)
            final_compatibility_score = min(100.0, max(0.0, final_compatibility_score))

            # 3. Generating the AI Summary of Fit justification snippet
            justification = (
                f"Matches critical technical areas including {', '.join(profile.top_skills[:2])}. "
                f"Possesses {profile.years_of_experience} years of relevant timeline experience, aligning with core requirements."
            )

            ranked_list.append({
                "candidate_name": profile.candidate_name,
                "compatibility_score": round(final_compatibility_score, 2),
                "years_of_experience": profile.years_of_experience,
                "top_skills": profile.top_skills,
                "ai_justification": justification
            })

        # Sort the evaluated objects downwards from top matches
        return sorted(ranked_list, key=lambda x: x["compatibility_score"], reverse=True)