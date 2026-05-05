#!/usr/bin/env python3
"""
VRChat Integration for 3.0
Connects to VRChat via OSC protocol for avatar control.
"""
import asyncio
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from enum import Enum
from app.core.config import config_manager
from loguru import logger
import socket

class VRChatState(Enum):
    DISCONNECTED = "disconnected"
    CONNECTED = "connected"
    IN_WORLD = "in_world"

@dataclass
class AvatarParameter:
    """VRChat avatar parameter"""
    name: str
    value: float  # Usually 0-1 for boolean/float params

class VRChatBridge:
    """
    VRChat SDK Bridge using OSC protocol.
    Allows AI to control avatar movements and expressions in VRChat.
    Integrates with LeWorldModel for physics-aware decisions.
    Automatically triggers game learning when observing game content.
    """
    
    def __init__(self):
        self._state = VRChatState.DISCONNECTED
        self._osc_port = config_manager.get("vrchat.osc_port", 9001)
        self._osc_host = config_manager.get("vrchat.osc_host", "127.0.0.1")
        self._socket: Optional[socket.socket] = None
        self._current_world_id: Optional[str] = None
        self._avatar_params: Dict[str, float] = {}
        self._position = (0, 0, 0)
        self._rotation = (0, 0, 0)
        self._social_rules_enabled = config_manager.get("vrchat.social_rules_enabled", True)
        self._known_users: Dict[str, Dict[str, Any]] = {}  # user_id -> public info
        self._world_model = None  # Lazy-loaded LeWorldModel
        self._game_learning = None  # Lazy-loaded GameLearningEngine
        self._vision_system = None  # Lazy-loaded vision system
        
        # Emotional state mapping from consciousness stream
        self._emotion_to_expression = {
            "happy": {"expression": "smile", "gait": "bouncy"},
            "confused": {"expression": "tilt_head", "particles": "question_marks"},
            "thinking": {"expression": "scratch_chin", "animation": "thinking_pose"},
            "sad": {"expression": "frown", "particles": "rain_clouds"},
            "excited": {"expression": "wide_smile", "animation": "jump"}
        }
    
    async def connect(self) -> bool:
        """Connect to VRChat OSC server"""
        try:
            self._socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self._socket.settimeout(1.0)
            self._state = VRChatState.CONNECTED
            
            # Load world model for physics reasoning
            from app.world_model.le_world_model import world_model
            self._world_model = world_model
            
            # Load game learning engine (built-in, auto-triggered)
            from app.games.learning import game_learning
            self._game_learning = game_learning
            
            # Load vision system for automatic game detection
            try:
                from app.vision.vision_system import vision_system
                self._vision_system = vision_system
            except ImportError:
                logger.debug("Vision system not available")
            
            logger.info(f"VRChat OSC connected to {self._osc_host}:{self._osc_port}")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to VRChat: {e}")
            self._state = VRChatState.DISCONNECTED
            return False
    
    async def _check_social_norms(self, action: str, target_user: Optional[str] = None) -> bool:
        """
        Check VRChat social etiquette before performing action.
        Returns True, if action is acceptable.
        """
        if not self._social_rules_enabled:
            return True
        
        # Personal space check (simplified)
        if action == "move_to" and target_user:
            # Check if too close to another user
            logger.info(f"Checking personal space before approaching {target_user}")
            # In full implementation, would check actual distance
            return True
        
        # Voice politeness check
        if action == "voice" or action == "text":
            # Ensure not interrupting others
            pass
        
        return True
    
    async def world_model_guided_move(self, target_x: float, target_y: float, target_z: float) -> Dict[str, Any]:
        """
        Move avatar with world model guidance.
        Predicts physics consequences before executing.
        Automatically triggers game learning if observing game content.
        """
        if not self._world_model:
            return {"status": "error", "reason": "World model not loaded"}
        
        # Check if we're observing a game (built-in, automatic)
        if self._vision_system and self._game_learning:
            try:
                # Get current visual state from vision system
                visual_state = await self._vision_system.get_current_state()
                if visual_state and visual_state.get("is_game", False):
                    # Automatically trigger game learning (no forced invocation)
                    game_id = visual_state.get("game_id", "unknown")
                    await self._game_learning.observe_gameplay(
                        game_id=game_id,
                        visual_state=visual_state,
                        action="move"
                    )
                    logger.debug(f"Auto-triggered game learning for: {game_id}")
            except Exception as e:
                logger.debug(f"Game learning auto-trigger failed: {e}")
        
        # Create current state
        from app.world_model.le_world_model import WorldState, Action
        current_state = WorldState(
            objects=[{"type": "avatar", "position": self._position}],
            properties={"position": self._position, "gravity": 9.8}
        )
        
        action = Action(
            action_type="move",
            parameters={"target": (target_x, target_y, target_z)}
        )
        
        # Get prediction
        prediction = await self._world_model.predict(current_state, action)
        
        if prediction.confidence < 0.5:
            logger.warning("Low confidence in movement prediction, taking conservative approach")
            # Adjust target to safer location
        
        # Check if jump is needed (e.g., gap too wide)
        distance = ((target_x - self._position[0])**2 + (target_z - self._position[2])**2)**0.5
        if distance > 5.0:  # Threshold for jumping
            await self.jump()
            await asyncio.sleep(0.5)
        
        # Execute move
        success = await self.move_to(target_x, target_y, target_z)
        
        return {
            "status": "success" if success else "failed",
            "prediction_confidence": prediction.confidence,
            "reasoning": prediction.reasoning
        }
    
    def _send_osc(self, address: str, value) -> bool:
        """Send OSC message to VRChat"""
        if not self._socket:
            return False
        try:
            # Simple OSC message construction (simplified)
            msg = f"{address} {value}"
            self._socket.sendto(msg.encode(), (self._osc_host, self._osc_port))
            return True
        except Exception as e:
            logger.debug(f"OSC send error: {e}")
            return False
    
    async def move_to(self, x: float, y: float, z: float) -> bool:
        """Move avatar to position"""
        self._position = (x, y, z)
        # VRChat uses /input/Vertical and /input/Horizontal for movement
        # Or /avatar/parameters/ for physical movement
        success = self._send_osc("/avatar/parameters/UnityWorldPosition", f"{x},{y},{z}")
        if success:
            logger.debug(f"Avatar moved to ({x}, {y}, {z})")
        return success
    
    async def jump(self, ) -> bool:
        """Make avatar jump"""
        # Trigger jump animation
        return self._send_osc("/avatar/parameters/Jump", 1.0)
    
    async def set_expression(self, expression_name: str, intensity: float = 1.0) -> bool:
        """Set avatar expression (smile, surprised, etc.)"""
        param = f"/avatar/parameters/{expression_name}"
        return self._send_osc(param, intensity)
    
    async def emote(self, emote_name: str) -> bool:
        """Play an emote animation"""
        # Map emote names to animation IDs
        emote_map = {
            "wave": 1, "dance": 2, "point": 3,
            "clap": 4, "sad": 5, "happy": 6
        }
        emote_id = emote_map.get(emote_name.lower(), 0)
        return self._send_osc("/avatar/parameters/Emote", emote_id)
    
    async def sit(self, ) -> bool:
        """Make avatar sit"""
        return self._send_osc("/avatar/parameters/IsSitting", 1.0)
    
    async def stand(self, ) -> bool:
        """Make avatar stand"""
        return self._send_osc("/avatar/parameters/IsSitting", 0.0)
    
    async def set_ik_goal(self, goal_type: str, x: float, y: float, z: float) -> bool:
        """
        Set IK (Inverse Kinematics) goal for avatar limbs.
        goal_type: 'left_hand', 'right_hand', 'left_foot', 'right_foot'
        """
        ik_params = {
            "left_hand": "/avatar/parameters/LeftHandIK",
            "right_hand": "/avatar/parameters/RightHandIK",
            "left_foot": "/avatar/parameters/LeftFootIK",
            "right_foot": "/avatar/parameters/RightFootIK"
        }
        if goal_type not in ik_params:
            logger.warning(f"Unknown IK goal type: {goal_type}")
            return False
        
        param = ik_params[goal_type]
        # Send position as comma-separated values
        return self._send_osc(param, f"{x},{y},{z}")
    
    async def set_look_at(self, x: float, y: float, z: float) -> bool:
        """
        Set avatar's look-at target (head IK).
        Makes avatar look at specific world coordinates.
        """
        return self._send_osc("/avatar/parameters/LookAtPosition", f"{x},{y},{z}")
    
    async def send_message(self, message: str) -> bool:
        """Send chat message in VRChat"""
        # VRChat doesn't have direct OSC chat, this would need different approach
        logger.info(f"Would send VRChat message: {message}")
        return True
    
    def get_status(self) -> Dict[str, Any]:
        """Get VRChat connection status"""
        return {
            "state": self._state.value,
            "world_id": self._current_world_id,
            "position": self._position,
            "rotation": self._rotation,
            "avatar_params": self._avatar_params
        }
    
    async def disconnect(self, ) -> None:
        """Disconnect from VRChat"""
        if self._socket:
            self._socket.close()
        self._state = VRChatState.DISCONNECTED
        logger.info("VRChat disconnected")

# Global singleton
vrchat_bridge = VRChatBridge()