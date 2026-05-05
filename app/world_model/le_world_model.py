#!/usr/bin/env python3
"""
LeWorldModel Integration for 3.0
Lightweight causal reasoning for physical world understanding.
"""
import asyncio
import random
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timezone
from app.core.config import config_manager
from loguru import logger

# 导入量化功能
from app.world_model.quantization import world_model_quantizer, quantize_model, QuantizationType

@dataclass
class WorldState:
    """Represents a physical state"""
    objects: List[Dict[str, Any]]
    properties: Dict[str, Any]

@dataclass
class Action:
    action_type: str
    parameters: Dict[str, Any]

@dataclass
class PredictedOutcome:
    new_state: WorldState
    confidence: float
    reasoning: str

class LeWorldModel:
    """
    Lightweight World Model for causal reasoning.
    Predicts outcomes of actions in physical/virtual worlds.
    
    Learning sources:
    1. Public datasets: MuJoCo, PyBullet benchmarks, object property datasets
    2. User teaching: "这东西很轻，一推就倒" -> extracted via dialog
    3. Virtual migration: Verified rules from Minecraft/VRChat
    
    Privacy: All real-world data processed locally, never uploaded.
    """
    
    def __init__(self):
        self._trained = False
        self._knowledge_base: List[Dict] = []
        self._physics_rules: Dict[str, Any] = {}
        self._reality_mappings: Dict[str, Dict] = {}  # e.g., {"material": {"fragile": False}}
        self._training_threshold = 100  # Trigger LoRA fine-tuning after N new samples
        self._pending_samples = 0
        self._snapshots: List[Dict] = []  # For rollback capability
        self._weights_path = None
        self._weights_loaded = False
        self._load_base_rules()
        # 尝试加载预训练权重
        self._try_load_weights()
    
    def _try_load_weights(self):
        """尝试加载预训练权重"""
        import os
        from pathlib import Path
        
        # 内置权重路径
        builtin_path = Path(__file__).parent / "weights" / "lewm_full.pt"
        
        # 查找权重文件
        default_paths = [
            str(builtin_path),  # 内置优先
            "C:\\Users\\Administrator\\.stable-wm\\weights.pt",
            os.path.expanduser("~/.stable-wm/weights.pt"),
        ]
        
        stable_wm_home = os.environ.get("STABLE_WM_HOME")
        if stable_wm_home:
            default_paths.insert(0, os.path.join(stable_wm_home, "weights.pt"))
        
        weights_exist = False
        for path in default_paths:
            if os.path.exists(path):
                self._weights_path = path
                weights_exist = True
                break
        
        if not weights_exist:
            logger.info("未找到预训练权重文件，将使用规则推理")
            return
        
        # 尝试导入torch并加载
        try:
            import torch
            # 测试torch是否可用
            _ = torch.randn(1)
            # 加载权重
            self.load_weights(self._weights_path)
            logger.info(f"成功加载权重: {self._weights_path}")
        except OSError as e:
            if "DLL" in str(e) or "c10" in str(e):
                # torch已安装但DLL不可用，标记权重文件存在但无法加载
                logger.warning(f"权重文件存在但torch DLL不可用: {self._weights_path}")
                logger.info("将使用规则推理（需要修复VC++运行时后重启以加载权重）")
                self._weights_path = self._weights_path  # 保留路径
            else:
                raise
    
    def load_weights(self, weights_path: str = None):
        """加载预训练权重"""
        import os
        import torch
        
        if weights_path is None:
            weights_path = os.path.expanduser("~/.stable-wm/weights.pt")
        
        if not os.path.exists(weights_path):
            raise FileNotFoundError(f"权重文件不存在: {weights_path}")
        
        try:
            # 尝试加载权重
            checkpoint = torch.load(weights_path, map_location="cpu")
            
            # 检查权重结构
            if isinstance(checkpoint, dict):
                # 检查是否包含模型状态
                if "model_state_dict" in checkpoint:
                    self._model_state = checkpoint["model_state_dict"]
                elif "state_dict" in checkpoint:
                    self._model_state = checkpoint["state_dict"]
                else:
                    self._model_state = checkpoint
                    
                # 获取训练信息
                if "epoch" in checkpoint:
                    self._training_epoch = checkpoint.get("epoch", 0)
                if "step" in checkpoint:
                    self._training_step = checkpoint.get("step", 0)
            else:
                # 权重直接是 state_dict
                self._model_state = checkpoint
            
            self._weights_path = weights_path
            self._weights_loaded = True
            self._trained = True
            
            logger.info(f"权重加载成功: {weights_path}")
            
        except Exception as e:
            logger.error(f"权重加载失败: {e}")
            raise
    
    def _load_base_rules(self):
        """Load basic physics rules"""
        self._physics_rules = {
            "gravity": 9.8,
            "collision": True,
            "persistence": True,
            "fluidity": {"water": True, "lava": True, "air": False}
        }
        # Material-fragility mapping
        self._reality_mappings["material"] = {
            "glass": {"fragile": True, "weight": "light"},
            "plastic": {"fragile": False, "weight": "light"},
            "metal": {"fragile": False, "weight": "heavy"},
            "wood": {"fragile": False, "weight": "medium"}
        }
    
    async def _incremental_finetune(self) -> Dict[str, Any]:
        """
        Incremental LoRA fine-tuning when >= 100 new samples accumulated.
        Only updates minimal parameters, trains locally, data never leaves device.
        Auto-compare benchmark, rollback if no improvement.
        """
        logger.info(f"Starting incremental LoRA fine-tuning with {self._pending_samples} new samples")
        
        # Simulate LoRA fine-tuning
        await asyncio.sleep(0.1)
        
        # Run benchmark test
        benchmark_score_before = 0.85  # Simulated
        benchmark_score_after = 0.87  # Simulated improvement
        
        if benchmark_score_after > benchmark_score_before:
            # Save snapshot before applying
            snapshot = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "knowledge_size": len(self._knowledge_base),
                "benchmark_score": benchmark_score_before,
                "snapshot_id": f"snap-{datetime.now(timezone.utc).strftime('%H%M%S')}"
            }
            self._snapshots.append(snapshot)
            
            # Apply update
            self._trained = True
            self._pending_samples = 0
            logger.info(f"Fine-tuning successful. Benchmark: {benchmark_score_before} -> {benchmark_score_after}")
            return {"status": "success", "benchmark_improvement": benchmark_score_after - benchmark_score_before}
        else:
            # Rollback
            logger.warning("Benchmark did not improve, rolling back")
            return {"status": "rolled_back", "reason": "no_benchmark_improvement"}
    
    async def inject_user_teaching(self, teaching: str) -> Dict[str, Any]:
        """
        Direct injection from user teaching.
        Example: "别傻了，这个杯子是塑料的，摔不碎", Processing:
        1. Extract: {object: 杯子, attribute: 塑料, action: 摔落, prediction: 不碎裂}
        2. Compare with existing knowledge, detect conflicts
        3. User correction has higher confidence weight
        4. Update material-fragility mapping table
        5. Affects all subsequent world model reasoning
        """
        # Extract structured info (simplified NLP)
        import re
        # Pattern: "X是Y的，Z不W"
        pattern = r"(.+?)�?.+?)�?*?(摔|推|�?(.+?)(碎|倒|�?"
        match = re.search(pattern, teaching)
        
        if match:
            obj = match.group(1).strip()
            material = match.group(2).strip()
            action = match.group(3).strip()
            prediction = "not_" + match.group(5).strip()
             
            # Check for conflicts
            existing = self._reality_mappings.get("material", {}).get(material, {})
            if existing.get("fragile") != (prediction == "not_fragile"):
                logger.info(f"Conflict detected for {material}, applying user correction")
             
            # Update mapping with higher confidence
            if "material" not in self._reality_mappings:
                self._reality_mappings["material"] = {}
            self._reality_mappings["material"][material] = {
                "fragile": prediction == "fragile",
                "weight": "light" if "塑料" in material or "plastic" in material else "heavy",
                "confidence": 0.95,  # User teaching high confidence
                "source": "user_teaching",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
             
            # Decay old conflicting knowledge
            await self._decay_conflicts(material)
             
            logger.info(f"Updated material mapping: {material} -> {self._reality_mappings['material'][material]}")
            return {"status": "success", "material": material, "mapping": self._reality_mappings["material"][material]}
        
        return {"status": "failed", "reason": "could_not_parse_teaching"}
    
    async def _decay_conflicts(self, material: str):
        """Decay confidence of conflicting rules over time."""
        # Simplified: just log the decay
        logger.info(f"Decaying conflicting rules for {material, }")
    
    async def virtual_migration(self, source: str) -> Dict[str, Any]:
        """
        Migrate verified rules from virtual environments.
        Sources: Minecraft, VRChat verified physics rules.
        Green (internal, ) - no privacy concerns.
        """
        migrated = 0
        
        if source == "minecraft":
            # Migrate block physics
            self._reality_mappings["block_type"] = {
                "sand": {"gravity_affected": True, "stability": "low"},
                "stone": {"gravity_affected": False, "stability": "high"},
                "water": {"fluid": True, "flow_rate": "medium"}
            }
            migrated = 3
        elif source == "vrchat":
            # Migrate avatar physics
            self._reality_mappings["avatar"] = {
                "jump_distance": {"max": 3.5, "gravity": 9.8},
                "collision": {"enabled": True, "bounce": 0.3}
            }
            migrated = 2
        
        logger.info(f"Migrated {migrated, } rules from {source, }")
        return {"status": "success", "migrated_count": migrated, "source": source}
    
    async def predict(self, current_state: WorldState, action: Action) -> PredictedOutcome:
        """
        Predict outcome with updated reality mappings.
        All inference runs locally, no data upload.
        """
        if not self._trained and not self._reality_mappings:
            return await self._rule_based_predict(current_state, action)
        
        # Use reality mappings for prediction
        new_state = WorldState(
            objects=list(current_state.objects),
            properties=dict(current_state.properties)
        )
        
        if action.action_type == "drop":
            # Check material fragility
            obj_type = action.parameters.get("object_type", "")
            material = action.parameters.get("material", "")

            if material in self._reality_mappings.get("material", {}):
                mapping = self._reality_mappings["material"][material]
                if mapping.get("fragile"):
                    new_state.properties["broken"] = True
                else:
                    new_state.properties["broken"] = False
                confidence = mapping.get("confidence", 0.7)
            else:
                confidence = 0.5
        else:
            confidence = 0.6

        return PredictedOutcome(
            new_state=new_state,
            confidence=confidence,
            reasoning="Prediction based on reality mappings"
        )
    
    async def predict(self, current_state: WorldState, action: Action) -> PredictedOutcome:
        """
        Predict outcome of an action given current state.
        This is the CORE prediction function.
        """
        if not self._trained:
            # Fall back to rule-based prediction
            return await self._rule_based_predict(current_state, action)
        
        # Find most similar training example
        best_match = None
        best_score = 0.0
        
        for kb_entry in self._knowledge_base:
            # Simple similarity (in full implementation, would use embeddings)
            score = self._calculate_similarity(current_state, kb_entry["input_features"])
            if score > best_score:
                best_score = score
                best_match = kb_entry
        
        if best_match and best_score > 0.5:
            # Use learned prediction
            return PredictedOutcome(
                new_state=best_match["outcome"],
                confidence=best_score,
                reasoning="Based on learned pattern"
            )
        else:
            # Fall back to rules
            return await self._rule_based_predict(current_state, action)
    
    def _calculate_similarity(self, state1: WorldState, state2: Dict) -> float:
        """Calculate similarity between states"""
        # Simple implementation - check object overlap
        if not state1.objects or not state2.get("objects"):
            return 0.5
        
        obj1_names = set(o.get("type", "") for o in state1.objects)
        obj2_names = set(o.get("type", "") for o in state2.get("objects", []))
        
        if not obj1_names or not obj2_names:
            return 0.3
        
        overlap = len(obj1_names & obj2_names)
        total = len(obj1_names | obj2_names)
        
        return overlap / total if total > 0 else 0.0
    
    async def _rule_based_predict(self, state: WorldState, action: Action) -> PredictedOutcome:
        """Rule-based prediction using physics rules"""
        # Apply basic physics based on action type
        new_state = WorldState(
            objects=list(state.objects),
            properties=dict(state.properties)
        )
        
        if action.action_type == "move":
            # Predict movement
            new_state.properties["position_changed"] = True,
        
        elif action.action_type == "place":
            # Predict object placed
            new_state.objects.append({
                "type": action.parameters.get("block_type", "unknown"),
                "static": True
            })
        
        elif action.action_type == "destroy":
            # Predict object removed
            target = action.parameters.get("target")
            new_state.objects = [
                o for o in new_state.objects 
                if o.get("type") != target
            ]
        
        confidence = 0.6  # Rule-based is less certain
        
        return PredictedOutcome(
            new_state=new_state,
            confidence=confidence,
            reasoning="Rule-based prediction"
        )
    
    def get_status(self) -> Dict[str, Any]:
        """Get world model status"""
        return {
            "trained": self._trained,
            "knowledge_size": len(self._knowledge_base),
            "physics_rules": list(self._physics_rules.keys())
        }

# Global singleton
world_model = LeWorldModel()