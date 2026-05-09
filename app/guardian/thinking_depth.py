#!/usr/bin/env python3
"""
Thinking Depth Guardian for 3.0
Monitors user question patterns and provides graded interventions to protect independent thinking.
All data stored locally, never uploaded.
"""
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from app.core.config import config_manager
from app.personality.system import personality_system


@dataclass
class ThinkingMetrics:
    """Metrics for measuring thinking depth of user inputs."""
    has_reasoning: bool = False
    asks_for_complete: bool = False
    repeats_same_type: bool = False


class ThinkingDepthGuardian:
    """
    Tracks user thinking patterns and provides interventions.
    All data stored locally, never uploaded.
    Intervention messages are stylized by frontend based on user's persona.
    """
    
    def __init__(self):
        self._window_size = config_manager.get("guardian.window_size", 10)
        self._history: List[ThinkingMetrics] = []
        self._intervention_enabled = config_manager.get("guardian.enabled", True)
        self._intervention_level = 0
        self._tool_tutorial_mode = False  # Level 3 triggers this
        self._privacy_report_dir = Path(config_manager.get("system.data_dir", "./data")) / "guardian"
        self._privacy_report_dir.mkdir(parents=True, exist_ok=True)
    
    def _analyze_input(self, user_input: str) -> ThinkingMetrics:
        """Analyze user input for thinking depth indicators."""
        # Check for reasoning indicators
        reasoning_keywords = ["因为", "所以", "如果", "那么", "但是", "为什么", "如何", "怎么"]
        has_reasoning = any(kw in user_input for kw in reasoning_keywords)
        
        # Check if asking for complete answer
        complete_keywords = ["告诉我", "直接给", "给我答案", "完整回答", "全部告诉我"]
        asks_for_complete = any(kw in user_input for kw in complete_keywords)
        
        # Check for repetition (simplified - would need NLP in full implementation)
        # For skeleton, just check length as proxy
        repeats_same_type = len(user_input) < 20  # Short inputs often indicate low depth
        
        return ThinkingMetrics(
            has_reasoning=has_reasoning,
            asks_for_complete=asks_for_complete,
            repeats_same_type=repeats_same_type
        )
    
    def _calculate_depth_score(self) -> float:
        """Calculate overall thinking depth score (0-1, higher is better)."""
        if not self._history:
            return 0.5  # Default neutral
        
        recent = self._history[-self._window_size:]
        score = 0.0
        for m in recent:
            depth = 0.5
            if m.has_reasoning:
                depth += 0.25
            if not m.asks_for_complete:
                depth += 0.15
            if not m.repeats_same_type:
                depth += 0.1
            score += min(depth, 1.0)
        
        return score / len(recent)
    
    def _get_intervention_message(self, level: int) -> str:
        """
        Generate a neutral intervention message.
        The frontend stylizes this message based on the user's chosen persona.
        """
        if level == 1:
            return "Would you like to try guessing the answer first?"
        elif level == 2:
            return "Reminder: Relying completely on AI may hinder your independent thinking."
        elif level == 3:
            self._tool_tutorial_mode = True
            return "I will only give you hints this time. I believe you can solve it!"
        else:  # level 4
            self._generate_privacy_report()
            return "Thinking Depth Report: Your independent thinking score has dropped significantly. Please review the detailed report."
    
    def _generate_privacy_report(self) -> Dict:
        """Generate private thinking health report (user-visible only)."""
        from pathlib import Path
        import json
        
        score = self._calculate_depth_score()
        report = {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "depth_score": score,
            "warning": "Thinking depth has dropped significantly over recent interactions.",
            "recommendation": "Try to solve problems step-by-step before asking for the answer."
        }
        
        report_path = self._privacy_report_dir / "latest_report.json"
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f)
        return report
    
    def process_input(self, user_input: str) -> Optional[str]:
        """Process user input and return intervention if needed."""
        if not self._intervention_enabled:
            return None
        
        metrics = self._analyze_input(user_input)
        self._history.append(metrics)
        
        if len(self._history) > self._window_size:
            self._history = self._history[-self._window_size:]
        
        if len(self._history) >= 3:
            consecutive_low = 0
            for m in self._history[-5:]:
                if not m.has_reasoning and m.asks_for_complete:
                    consecutive_low += 1
            
            if consecutive_low >= 10:
                self._intervention_level = 4
            elif consecutive_low >= 5:
                self._intervention_level = 3
            elif consecutive_low >= 3:
                self._intervention_level = 2
            elif consecutive_low >= 1:
                self._intervention_level = 1
            else:
                self._intervention_level = 0
            
            if self._intervention_level > 0:
                return self._get_intervention_message(self._intervention_level)
        
        return None
    
    def get_status(self) -> Dict[str, Any]:
        """Get guardian status and metrics."""
        depth_score = self._calculate_depth_score()
        recent_low = sum(1 for m in self._history[-5:] if not m.has_reasoning and m.asks_for_complete)
        
        return {
            "enabled": self._intervention_enabled,
            "intervention_level": self._intervention_level,
            "thinking_depth_score": depth_score,
            "recent_low_depth_count": recent_low,
            "history_size": len(self._history),
            "tool_tutorial_mode": self._tool_tutorial_mode
        }
    
    def reset(self) -> None:
        """Reset guardian state."""
        self._history = []
        self._intervention_level = 0
        self._tool_tutorial_mode = False


# Global singleton
thinking_guardian = ThinkingDepthGuardian()
