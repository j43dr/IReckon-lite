"""World Model module for 3.0 causal reasoning

包含:
- LeWorldModel: 轻量级因果推理世界模型
- WorldModelQuantizer: 世界模型量化器
- 便捷API
- 内置权重
"""
from .le_world_model import world_model, LeWorldModel, WorldState, Action, PredictedOutcome
from .quantization import (
    world_model_quantizer,
    WorldModelQuantizer,
    quantize_model,
    QuantizationType,
    QuantizationConfig
)
from .api import (
    predict_action,
    learn_rule,
    query_rule,
    quantize,
    get_quantization_info,
    list_quantization_types,
    get_model_status,
    create_snapshot,
    restore_snapshot
)

__all__ = [
    # 核心类
    "world_model",
    "LeWorldModel",
    "WorldState",
    "Action",
    "PredictedOutcome",
    # 量化
    "world_model_quantizer",
    "WorldModelQuantizer",
    "quantize_model",
    "QuantizationType",
    "QuantizationConfig",
    # API便捷函数
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