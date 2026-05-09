"""训练数据管理器 - 收集、存储和管理微型模型训练样本"""
import json
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime, timezone
from loguru import logger
from app.core.config import config_manager

BASE = Path(config_manager.get("system.data_dir", "./data")) / "training"
SAMPLES_DIR = BASE / "samples"
SAMPLES_DIR.mkdir(parents=True, exist_ok=True)


class DatasetManager:
    """管理训练数据集"""
    
    def __init__(self, dataset_name: str):
        self.dataset_name = dataset_name
        self.dataset_dir = SAMPLES_DIR / dataset_name
        self.dataset_dir.mkdir(parents=True, exist_ok=True)
        self.samples_file = self.dataset_dir / "samples.jsonl"
        self.metadata_file = self.dataset_dir / "metadata.json"
    
    def add_sample(self, input_text: str, output_text: str, metadata: Optional[Dict] = None):
        """添加训练样本"""
        sample = {
            "input": input_text,
            "output": output_text,
            "metadata": metadata or {},
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        with open(self.samples_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(sample, ensure_ascii=False) + "\n")
        logger.debug(f"Added sample to {self.dataset_name}")
        return sample
    
    def get_samples(self, limit: int = 1000) -> List[Dict]:
        """获取训练样本"""
        if not self.samples_file.exists():
            return []
        samples = []
        with open(self.samples_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    samples.append(json.loads(line))
                    if len(samples) >= limit:
                        break
        return samples
    
    def get_sample_count(self) -> int:
        """获取样本数量"""
        if not self.samples_file.exists():
            return 0
        with open(self.samples_file, "r", encoding="utf-8") as f:
            return sum(1 for line in f if line.strip())
    
    def save_metadata(self, metadata: Dict):
        """保存数据集元数据"""
        metadata["dataset_name"] = self.dataset_name
        metadata["sample_count"] = self.get_sample_count()
        metadata["updated_at"] = datetime.now(timezone.utc).isoformat()
        with open(self.metadata_file, "w", encoding="utf-8") as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)
    
    def load_metadata(self) -> Dict:
        """加载数据集元数据"""
        if self.metadata_file.exists():
            with open(self.metadata_file, "r", encoding="utf-8") as f:
                return json.load(f)
        return {}


# 便捷函数
def add_training_sample(dataset_name: str, input_text: str, output_text: str, metadata: Optional[Dict] = None):
    """便捷函数：添加训练样本"""
    manager = DatasetManager(dataset_name)
    return manager.add_sample(input_text, output_text, metadata)


def get_training_samples(dataset_name: str, limit: int = 1000) -> List[Dict]:
    """便捷函数：获取训练样本"""
    manager = DatasetManager(dataset_name)
    return manager.get_samples(limit)


def get_dataset_count(dataset_name: str) -> int:
    """便捷函数：获取数据集样本数量"""
    manager = DatasetManager(dataset_name)
    return manager.get_sample_count()