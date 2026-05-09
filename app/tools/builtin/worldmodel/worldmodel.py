#!/usr/bin/env python3
"""
worldmodel - 世界模型因果推理
"""
from typing import Dict, Any, Optional


async def run(action_type: str, object: str = "object", force: float = 1.0, position: Optional[list] = None, **kwargs) -> Dict:
    """使用世界模型预测动作结果"""
    try:
        from app.world_model.le_world_model import LeWorldModel, WorldState, Action
        
        wm = LeWorldModel()
        
        state = WorldState(
            objects=[{"id": object, "position": position or [0, 0, 0], "mass": 1}],
            properties={"gravity": 9.8}
        )
        action = Action(action_type=action_type, parameters={"target": object, "force": force})
        
        result = await wm.predict(state, action)
        
        return {
            "new_state": {
                "objects": [o.__dict__ for o in result.new_state.objects],
                "properties": result.new_state.properties
            },
            "confidence": result.confidence,
            "reasoning": result.reasoning
        }
    except Exception as e:
        return {
            "new_state": {},
            "confidence": 0,
            "error": str(e),
            "reasoning": f"Error: {e}"
        }


if __name__ == "__main__":
    import asyncio
    print(asyncio.run(run("push")))