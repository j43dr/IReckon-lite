#!/usr/bin/env python3
"""
World Model API - 便捷函数封装
"""
import asyncio
from typing import Dict, Any, List, Optional
from app.world_model import (
    world_model,
    LeWorldModel,
    WorldState,
    Action,
    PredictedOutcome,
    world_model_quantizer,
    quantize_model,
    QuantizationType
)


# ============ 预测接口 ============

async def predict_action(
    action_type: str,
    object_name: str = "object",
    force: float = 1.0,
    position: List[float] = None
) -> Dict[str, Any]:
    """
    预测动作结果
    
    Args:
        action_type: 动作类型 (push, pull, move, drop, etc.)
        object_name: 对象名称
        force: 力的大小
        position: 位置 [x, y, z]
    
    Returns:
        预测结果字典
    """
    state = WorldState(
        objects=[{"id": object_name, "position": position or [0, 0, 0], "mass": 1}],
        properties={"gravity": 9.8}
    )
    action = Action(action_type=action_type, parameters={"target": object_name, "force": force})
    
    result = await world_model.predict(state, action)
    
    return {
        "action": action_type,
        "object": object_name,
        "force": force,
        "new_state": {
            "objects": result.new_state.objects,
            "properties": result.new_state.properties
        },
        "confidence": result.confidence,
        "reasoning": result.reasoning
    }


# ============ 知识管理 ============

async def learn_rule(
    object1: str,
    relation: str,  # e.g., "heavier_than", "fragile", "floats_on"
    object2: str = None
) -> Dict[str, Any]:
    """
    学习物理规则
    
    Args:
        object1: 对象1
        relation: 关系/属性
        object2: 对象2 (如果是比较关系)
    """
    rule = {"object": object1, "relation": relation}
    if object2:
        rule["compared_to"] = object2
    
    world_model._physics_rules[f"{object1}:{relation}"] = rule
    
    return {"learned": True, "rule": rule}


async def query_rule(object_name: str, relation: str = None) -> List[Dict]:
    """
    查询物理规则
    
    Args:
        object_name: 对象名称
        relation: 关系 (可选，查询该对象所有规则)
    """
    if relation:
        key = f"{object_name}:{relation}"
        return [world_model._physics_rules.get(key, {})]
    else:
        return [
            v for k, v in world_model._physics_rules.items()
            if object_name in k
        ]


# ============ 量化接口 ============

async def quantize(
    input_path: str,
    output_path: str,
    quant_type: str = "int8",
    bits: int = 8
) -> Dict[str, Any]:
    """
    量化世界模型权重
    
    Args:
        input_path: 输入权重路径
        output_path: 输出路径
        quant_type: 量化类型 ("int8", "int4", "fp16", "ggml_q4_0", etc.)
        bits: 位数
    
    Returns:
        量化结果
    """
    return await quantize_model(input_path, output_path, quant_type, bits)


def get_quantization_info() -> Dict[str, Any]:
    """获取量化信息"""
    return world_model_quantizer.get_info()


def list_quantization_types() -> List[str]:
    """列出支持的量化类型"""
    return [qt.value for qt in QuantizationType]


# ============ 状态管理 ============

def get_model_status() -> Dict[str, Any]:
    """获取模型状态"""
    return {
        "trained": world_model._trained,
        "weights_loaded": world_model._weights_loaded,
        "weights_path": world_model._weights_path,
        "knowledge_count": len(world_model._knowledge_base),
        "physics_rules_count": len(world_model._physics_rules),
        "snapshots_count": len(world_model._snapshots)
    }


async def create_snapshot() -> str:
    """创建快照"""
    snapshot = {
        "timestamp": asyncio.get_event_loop().time(),
        "knowledge": world_model._knowledge_base.copy(),
        "rules": world_model._physics_rules.copy()
    }
    world_model._snapshots.append(snapshot)
    return f"snapshot-{len(world_model._snapshots)}"


async def restore_snapshot(snapshot_id: int) -> bool:
    """恢复快照"""
    if 0 <= snapshot_id < len(world_model._snapshots):
        snapshot = world_model._snapshots[snapshot_id]
        world_model._knowledge_base = snapshot["knowledge"]
        world_model._physics_rules = snapshot["rules"]
        return True
    return False


# ============ 导出 ============

__all__ = [
    "predict_action",
    "learn_rule",
    "query_rule",
    "quantize",
    "get_quantization_info",
    "list_quantization_types",
    "get_model_status",
    "create_snapshot",
    "restore_snapshot",
]