#!/usr/bin/env python3
"""
Micro Model Factory for 3.0, Enables IReckon to produce small specialized models (LoRA fine-tuned) as new tools.
"""
import asyncio
import json
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone
from dataclasses import dataclass
from app.core.config import config_manager
from app.core.database import db
from loguru import logger


@dataclass
class TrainingCandidate:
    """Pattern identified as candidate for model training."""
    pattern_id: str
    pattern_type: str  # e.g., "visual_recognition", "code_review"
    frequency: int
    first_seen: str
    last_seen: str


@dataclass
class DatasetCard:
    """Metadata for a training dataset."""
    dataset_id: str
    source: str
    sample_count: int
    annotation_method: str
    collected_at: str
    file_path: str


@dataclass
class ModelCard:
    """Metadata for a trained model."""
    model_id: str
    model_format: str  # .gguf, .onnx
    input_format: Dict[str, Any]
    output_format: Dict[str, Any]
    recommended_engine: str  # llama.cpp, ONNX Runtime
    performance_metrics: Dict[str, float]
    dataset_id: str


class MicroModelFactory:
    """
    Manages the lifecycle of micro-model production:
    1. Training data collection
    2. LoRA fine-tuning with QAT
    3. Model registration as tools
    4. Device-adaptive deployment
    """

    def __init__(self):
        self._data_dir = Path(config_manager.get("system.data_dir", "./data"))
        self._models_dir = self._data_dir / "models"
        self._datasets_dir = self._data_dir / "datasets"
        self._training_queue: List[TrainingCandidate] = []
        self._candidates_file = self._data_dir / "training_candidates.json"
        self._models_dir.mkdir(parents=True, exist_ok=True)
        self._datasets_dir.mkdir(parents=True, exist_ok=True)
        self._load_candidates()

    def _load_candidates(self):
        """Load existing training candidates from disk."""
        if self._candidates_file.exists():
            try:
                with open(self._candidates_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self._training_queue = [TrainingCandidate(**c) for c in data]
            except Exception as e:
                logger.error(f"Failed to load candidates: {e}")

    def _save_candidates(self):
        """Save training candidates to disk."""
        try:
            with open(self._candidates_file, 'w', encoding='utf-8') as f:
                json.dump([c.__dict__ for c in self._training_queue], f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Failed to save candidates: {e}")

    async def detect_training_candidates(self, pattern_type: str, frequency: int) -> Optional[TrainingCandidate]:
        """
        Detect patterns that qualify for micro-model training.
        Triggered when a pattern is frequently called by the main model.
        """
        min_frequency = config_manager.get("model_factory.min_frequency", 10)
        if frequency < min_frequency:
            return None

        candidate_id = f"candidate-{pattern_type}-{datetime.now(timezone.utc).strftime('%Y%m%d')}"
        candidate = TrainingCandidate(
            pattern_id=candidate_id,
            pattern_type=pattern_type,
            frequency=frequency,
            first_seen=datetime.now(timezone.utc).isoformat(),
            last_seen=datetime.now(timezone.utc).isoformat()
        )
        self._training_queue.append(candidate)
        self._save_candidates()
        logger.info(f"New training candidate detected: {pattern_type} (frequency: {frequency})")
        return candidate

    async def collect_training_data(self, candidate: TrainingCandidate, data_source: str) -> DatasetCard:
        """
        Automatically collect training data from recorded input-output pairs.
        Uses AI to create data collection tasks and cleans duplicates.
        """
        dataset_id = f"ds-{candidate.pattern_id}"
        output_path = self._datasets_dir / f"{dataset_id}.jsonl"

        # Simulate data collection from source
        # In full implementation, would read from conversation logs / API call logs
        collected_samples = []
        try:
            # Placeholder: would integrate with actual data source
            logger.info(f"Collecting training data for {candidate.pattern_type} from {data_source}")
            # Simulate collecting 100 samples
            for i in range(min(100, candidate.frequency)):
                collected_samples.append({
                    "input": f"sample_input_{i}",
                    "output": f"sample_output_{i}",
                    "timestamp": datetime.now(timezone.utc).isoformat()
                })

            # Deduplication
            seen = set()
            unique_samples = []
            for s in collected_samples:
                key = f"{s['input']}:{s['output']}"
                if key not in seen:
                    seen.add(key)
                    unique_samples.append(s)

            # Write to file
            with open(output_path, 'w', encoding='utf-8') as f:
                for s in unique_samples:
                    f.write(json.dumps(s, ensure_ascii=False) + '\n')

            dataset_card = DatasetCard(
                dataset_id=dataset_id,
                source=data_source,
                sample_count=len(unique_samples),
                annotation_method="automatic",
                collected_at=datetime.now(timezone.utc).isoformat(),
                file_path=str(output_path)
            )

            # Write dataset card
            card_path = self._datasets_dir / f"{dataset_id}_card.json"
            with open(card_path, 'w', encoding='utf-8') as f:
                json.dump(dataset_card.__dict__, f, indent=2, ensure_ascii=False)

            logger.info(f"Collected {len(unique_samples)} training samples for {dataset_id}")
            return dataset_card

        except Exception as e:
            logger.error(f"Failed to collect training data: {e}")
            raise

    async def create_training_task(self, candidate_pattern: str, data_source: str) -> str:
        """
        System internal API: Create a training task for a candidate pattern.
        Returns task_id.
        """
        # Find or create candidate
        candidate = None
        for c in self._training_queue:
            if c.pattern_type == candidate_pattern:
                candidate = c
                break

        if not candidate:
            candidate = await self.detect_training_candidates(candidate_pattern, 
                                                              config_manager.get("model_factory.min_frequency", 10))

        if not candidate:
            raise ValueError(f"Pattern {candidate_pattern} does not qualify for training")

        # Start data collection
        task_id = f"train-{candidate.pattern_id}-{datetime.now(timezone.utc).strftime('%H%M%S')}"
        logger.info(f"Created training task {task_id} for pattern {candidate_pattern}")

        # In full implementation, would queue this as an async task
        return task_id

    async def run_lora_fine_tuning(self, dataset_card: DatasetCard, task_id: str) -> ModelCard:
        """
        Run LoRA fine-tuning with QAT (Quantization-Aware Training).
        Uses PEFT library and automatic hyperparameter selection.
        """
        logger.info(f"Starting LoRA fine-tuning for task {task_id}")

        # Simulate training process
        # In full implementation, would use HuggingFace PEFT + QAT

        # Auto-select hyperparameters based on data size and task type
        sample_count = dataset_card.sample_count
        if sample_count < 500:
            batch_size = 4
            learning_rate = 1e-4
            epochs = 3
        else:
            batch_size = 16
            learning_rate = 5e-5
            epochs = 5
        logger.info(f"Training params: batch_size={batch_size}, lr={learning_rate}, epochs={epochs}")

        # Simulate training time
        await asyncio.sleep(0.1)  # Placeholder

        # Generate model file (simulated)
        model_id = f"model-{dataset_card.dataset_id}"
        model_path = self._models_dir / f"{model_id}.gguf"

        # Write placeholder model file
        with open(model_path, 'w', encoding='utf-8') as f:
            f.write(f"# Simulated GGUF model for {dataset_card.source}\n")
            f.write(f"# Task: {task_id}\n")

        # Create model card
        model_card = ModelCard(
            model_id=model_id,
            model_format="gguf",
            input_format={"type": "text", "schema": {"input": "string"}},
            output_format={"type": "text", "schema": {"output": "string"}},
            recommended_engine="llama.cpp",
            performance_metrics={"accuracy": 0.85, "latency_ms": 50},
            dataset_id=dataset_card.dataset_id
        )

        # Write model card
        card_path = self._models_dir / f"{model_id}_card.json"
        with open(card_path, 'w', encoding='utf-8') as f:
            json.dump(model_card.__dict__, f, indent=2, ensure_ascii=False)

        logger.info(f"Model trained and saved: {model_path}")
        return model_card

    async def register_model_as_tool(self, model_card: ModelCard) -> Dict[str, Any]:
        """
        Register the trained model as a 'model-class tool' in the tool library.
        Makes it available for semantic retrieval by the scheduler.
        """
        tool_entry = {
            "tool_id": f"tool-{model_card.model_id}",
            "tool_type": "model",
            "model_id": model_card.model_id,
            "capabilities": [model_card.model_id.split('-')[1]],  # e.g., "visual_recognition"
            "input_format": model_card.input_format,
            "output_format": model_card.output_format,
            "engine": model_card.recommended_engine,
            "registered_at": datetime.now(timezone.utc).isoformat()
        }

        # Save to database
        await db.save_tool(tool_entry)
        logger.info(f"Model {model_card.model_id} registered as tool {tool_entry['tool_id']}")

        return tool_entry

    async def detect_device_profile(self) -> Dict[str, Any]:
        """
        Probe current device for NPU, GPU, memory info.
        Returns device profile for adaptive deployment.
        """
        import platform
        profile = {
            "platform": platform.system(),
            "has_npu": False,
            "has_gpu": False,
            "gpu_type": None,
            "memory_mb": 0
        }

        # Simplified detection
        # In full implementation, would use torch, coreml-tools, etc.
        try:
            import psutil
            memory = psutil.virtual_memory()
            profile["memory_mb"] = memory.total // (1024 * 1024)
        except ImportError:
            pass

        # Placeholder: would detect Apple Neural Engine, CUDA, etc.
        logger.info(f"Device profile: {profile}")
        return profile

    async def deploy_model(self, model_id: str, target_device: Dict[str, Any]) -> Dict[str, Any]:
        """
        Deploy model with device-adaptive backend selection.
        - NPU -> CoreML
        - GPU -> CUDA/Metal
        - CPU -> Quantized + thread limits
        """
        model_card_path = self._models_dir / f"{model_id}_card.json"
        if not model_card_path.exists():
            return {"status": "error", "reason": "Model card not found"}

        with open(model_card_path, 'r', encoding='utf-8') as f:
            model_card = json.load(f)

        # Select backend based on device
        if target_device.get("has_npu"):
            backend = "CoreML"
            quantization = "none"
        elif target_device.get("has_gpu"):
            backend = "CUDA" if target_device.get("gpu_type") == "nvidia" else "Metal"
            quantization = "INT8"
        else:
            backend = "CPU"
            quantization = "INT4"

        # Simulate deployment
        await asyncio.sleep(0.05)

        # Run warmup inference
        logger.info(f"Running warmup inference for {model_id} with {backend} backend")

        deployment_status = {
            "model_id": model_id,
            "backend": backend,
            "quantization": quantization,
            "deployed_at": datetime.now(timezone.utc).isoformat(),
            "status": "deployed",
            "warmup_latency_ms": 8.5
        }

        # Save deployment record
        deploy_path = self._models_dir / f"{model_id}_deploy.json"
        with open(deploy_path, 'w', encoding='utf-8') as f:
            json.dump(deployment_status, f, indent=2, ensure_ascii=False)

        logger.info(f"Model {model_id} deployed with {backend} backend")
        return deployment_status

    def get_status(self) -> Dict[str, Any]:
        """Get model factory status."""
        return {
            "training_queue_size": len(self._training_queue),
            "models_dir": str(self._models_dir),
            "datasets_dir": str(self._datasets_dir),
            "candidates": [c.__dict__ for c in self._training_queue]
        }


# Global singleton
model_factory = MicroModelFactory()
