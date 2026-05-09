#!/usr/bin/env python3
"""
Personality System for 3.0 Style-based Character Management.
Implements Big Five personality model (Openness, Conscientiousness, Extraversion,
Agreeableness, Emotional Stability). All specific character personas (e.g. catgirl,
strict reviewer) are managed via frontend stylization; the backend only provides
the raw parameters and behavioral mapping.
"""
from typing import Dict, Any, Optional
from dataclasses import dataclass
from app.core.config import config_manager
from datetime import datetime, timezone

@dataclass
class PersonalityParams:
    """Big Five personality parameters (0-1 scale)."""
    openness: float = 0.5      # Creativity, curiosity
    conscientiousness: float = 0.5  # Organization, discipline
    extraversion: float = 0.5  # Sociability
    agreeableness: float = 0.5 # Cooperation, trust
    emotional_stability: float = 0.5  # Calmness, resilience

class PersonalitySystem:
    """Manages AI character personalities and behavior mapping."""
    
    def __init__(self):
        # Load initial parameters from config (can be overridden via API)
        defaults = config_manager.get("personality.params", {})
        self._params = PersonalityParams(
            openness=defaults.get("openness", 0.5),
            conscientiousness=defaults.get("conscientiousness", 0.5),
            extraversion=defaults.get("extraversion", 0.5),
            agreeableness=defaults.get("agreeableness", 0.5),
            emotional_stability=defaults.get("emotional_stability", 0.5)
        )
        self._last_evolution = datetime.now(timezone.utc)

    def update_params(self, params: Dict[str, float]) -> bool:
        """Update Big Five parameters directly."""
        valid_keys = {"openness", "conscientiousness", "extraversion", "agreeableness", "emotional_stability"}
        if not all(k in valid_keys for k in params.keys()):
            return False
        if hasattr(self._params, '__dict__'):
            for k, v in params.items():
                if k in valid_keys:
                    setattr(self._params, k, float(v))
        return True

    def get_params(self) -> Dict[str, float]:
        """Get current personality parameters."""
        return {
            "openness": self._params.openness,
            "conscientiousness": self._params.conscientiousness,
            "extraversion": self._params.extraversion,
            "agreeableness": self._params.agreeableness,
            "emotional_stability": self._params.emotional_stability
        }
    
    def get_response_style(self) -> Dict[str, Any]:
        """
        Map Big Five personality parameters to response style parameters.
        These are consumed by the frontend stylization layer.
        """
        p = self._params
        
        # Language style mapping
        if p.openness > 0.7:
            word_freq = "creative"
            sentence_complexity = "high"
        elif p.openness < 0.4:
            word_freq = "conservative"
            sentence_complexity = "low"
        else:
            word_freq = "balanced"
            sentence_complexity = "medium"
        
        # Decision style mapping
        if p.conscientiousness > 0.7:
            risk_preference = "low"
            info_gathering = "deep"
            self_check_count = 3
        elif p.conscientiousness < 0.4:
            risk_preference = "high"
            info_gathering = "shallow"
            self_check_count = 1
        else:
            risk_preference = "medium"
            info_gathering = "balanced"
            self_check_count = 2
        
        # Interaction style mapping
        initiative_probability = p.extraversion * 0.8
        interrupt_tolerance = "high" if p.agreeableness > 0.6 else "low"
        
        # Note: "humor_type", "user_name" etc. are provided by the frontend/stylization layer.
        # If not present in config, we default to 'none' and 'User'.
        humor = config_manager.get("personality.humor_type", "none")
        user_name = config_manager.get("personality.user_name", "User")
        
        return {
            "language": {
                "word_frequency": word_freq,
                "sentence_complexity": sentence_complexity,
                "humor_type": humor,
                "user_name": user_name
            },
            "decision": {
                "risk_preference": risk_preference,
                "info_gathering_depth": info_gathering,
                "self_check_before_submit": self_check_count
            },
            "interaction": {
                "initiative_probability": initiative_probability,
                "interrupt_tolerance": interrupt_tolerance
            },
            "params": self.get_params()
        }

    async def get_memory_recall(self, current_topic: str, memories: list) -> Optional[str]:
        """Trigger personality-based memory recall based on topic distance."""
        if not memories:
            return None
        
        # Simulate vector distance check
        for mem in memories:
            topic = mem.get("topic", "")
            if any(word in current_topic for word in topic.split()):
                style = self.get_response_style()["language"]["humor_type"]
                # The content is generic; the frontend stylizes the phrasing.
                return f"Recalling memory related to: {topic}"
        return None
    
    def get_status(self) -> Dict[str, Any]:
        """Get current personality status."""
        return {
            "parameters": self.get_params(),
            "response_style": self.get_response_style()
        }

# Global singleton
personality_system = PersonalitySystem()