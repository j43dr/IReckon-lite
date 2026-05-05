from loguru import logger
import subprocess
import os
import platform
from typing import Dict, Any, Optional


class GameLauncher:
    def __init__(self):
        self.system = platform.system()
        
        # 常用游戏路径配置
        self.game_paths = {
            "minecraft": {
                "windows": [
                    os.path.expandvars("%APPDATA%\\.minecraft\\Minecraft.exe"),
                    os.path.expandvars("%PROGRAMFILES%\\Minecraft\\Minecraft.exe"),
                    "C:\\Minecraft\\Minecraft.exe",
                ],
                "linux": ["~/.minecraft/MinecraftLauncher"],
                "android": ["com.mojang.minecraftpe"]
            },
            "minecraft_java": {
                "windows": [
                    os.path.expandvars("%APPDATA%\\.minecraft\\launcher\\MinecraftLauncher.exe"),
                ],
            }
        }

    def _find_executable(self, paths: list) -> Optional[str]:
        """查找可执行文件"""
        for path in paths:
            expanded = os.path.expandvars(path)
            if os.path.exists(expanded):
                return expanded
        return None

    async def launch(self, game: str) -> Dict[str, Any]:
        """启动游戏"""
        logger.info(f"正在启动: {game}")
        
        if game not in self.game_paths:
            return {"status": "error", "message": f"不支持的游戏: {game}"}
        
        game_config = self.game_paths[game]
        
        if self.system == "Windows":
            paths = game_config.get("windows", [])
            exe = self._find_executable(paths)
            
            if exe:
                try:
                    subprocess.Popen([exe], shell=True)
                    logger.info(f"已启动 Minecraft: {exe}")
                    return {"status": "launched", "game": game, "path": exe}
                except Exception as e:
                    return {"status": "error", "message": str(e)}
            else:
                # 没找到，尝试启动 Minecraft Launcher
                try:
                    subprocess.Popen(["start", "minecraft://"], shell=True)
                    return {"status": "launched", "game": game, "method": "protocol"}
                except Exception as e:
                    return {"status": "error", "message": f"未找到Minecraft，请安装或手动启动"}
                    
        elif self.system == "Linux":
            # 尝试使用 Minecraft Launcher
            try:
                subprocess.Popen(["minecraft-launcher"], shell=True)
                return {"status": "launched", "game": game}
            except:
                return {"status": "error", "message": "Linux需要安装Minecraft Launcher"}
                
        elif self.system == "Android":
            # 使用 Android Intent 启动
            try:
                import androidhelper
                droid = androidhelper.Android()
                # 尝试启动 Minecraft PE
                result = droid.startActivity("com.mojang.minecraftpe",
                    "com.mojang.minecraftpe.MainActivity")
                return {"status": "launched", "game": game}
            except:
                return {"status": "error", "message": "请在手机上手动打开Minecraft"}
        
        return {"status": "error", "message": f"不支持的平台: {self.system}"}

    async def close(self, game: str) -> Dict[str, Any]:
        """关闭游戏"""
        if self.system == "Windows":
            try:
                subprocess.run(["taskkill", "/F", "/IM", "Minecraft.exe"], 
                             capture_output=True)
                return {"status": "closed", "game": game}
            except:
                pass
        return {"status": "error", "message": "无法关闭"}

    async def is_installed(self, game: str) -> bool:
        """检查游戏是否安装"""
        if game in self.game_paths:
            paths = self.game_paths[game].get(self.system.lower(), [])
            return self._find_executable(paths) is not None
        return False

    def list_games(self) -> Dict[str, str]:
        """列出支持的游戏"""
        return {
            "minecraft": "Minecraft (基岩版)",
            "minecraft_java": "Minecraft Java版",
        }


game_launcher = GameLauncher()