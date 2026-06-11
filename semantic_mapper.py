import re
from typing import List, Dict, Any
from pydantic import BaseModel

class NormalizedProfile(BaseModel):
    candidate_name: str
    top_skills: List[str]
    years_of_experience: float
    experience_summary: str

class SemanticMapper:
    # Simulating a technical skill taxonomy hierarchy (Knowledge Graph concept)
    SKILL_TAXONOMY = {
        "java": ["java", "jvm", "spring boot", "jakarta", "jee"],
        "machine learning": ["pytorch", "tensorflow", "scikit-learn", "keras", "ml"],
        "frontend": ["react", "vue", "angular", "typescript", "javascript"]
    }

    @classmethod
    def normalize_profile(cls, raw_text: str, filename: str) -> NormalizedProfile:
        """Maps unstructured text to structured technical data objects."""
        text_lower = raw_text.lower()
        detected_skills = set()

        # Taxonomy and hierarchy synonym matching
        for canonical_skill, synonyms in cls.SKILL_TAXONOMY.items():
            for synonym in synonyms:
                if re.search(r'\b' + re.escape(synonym) + r'\b', text_lower):
                    detected_skills.add(canonical_skill.title())
                    # Include the concrete matching variant as well
                    if synonym != canonical_skill:
                        detected_skills.add(synonym.title())

        # Simple regex heuristic to approximate total experience numbers
        exp_match = re.search(r'(\d+)\+?\s*(?:years?|yrs?)\s+(?:of\s+)?experience', text_lower)
        years = float(exp_match.group(1)) if exp_match else 2.0  # Fallback baseline default

        # Basic name extraction heuristic clean up from filename
        clean_name = filename.split(".")[0].replace("_", " ").replace("-", " ").title()

        return NormalizedProfile(
            candidate_name=clean_name,
            top_skills=list(detected_skills),
            years_of_experience=years,
            experience_summary=raw_text[:300].strip().replace("\n", " ") + "..."
        )