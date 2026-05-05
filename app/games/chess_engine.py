#!/usr/bin/env python3
"""
Chess Engine Integration for 3.0
Implements AI chess playing with personality-driven style.
"""
import asyncio
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from enum import Enum
from app.core.config import config_manager
from app.personality.system import personality_system
from loguru import logger
import random

class ChessColor(Enum):
    WHITE = "white"
    BLACK = "black"

@dataclass
class ChessMove:
    """Represents a chess move"""
    from_square: str  # e.g., "e2"
    to_square: str    # e.g., "e4"
    promotion: Optional[str] = None  # queen, rook, bishop, knight

class ChessEngine:
    """
    Chess AI that plays with style based on personality parameters.
    Integrates with Stockfish/LC0 engine for move generation.
    Provides move evaluation scores and narrative commentary.
    """
    
    def __init__(self):
        self._board_state: List[str] = []  # FEN representation
        self._current_turn = ChessColor.WHITE
        self._move_history: List[ChessMove] = []
        self._engine_path = config_manager.get("chess.engine_path", "stockfish")
        self._thinking_time_ms = config_manager.get("chess.thinking_time", 1000)
        self._game_active = False
        self._player_color = ChessColor.WHITE
        self._stockfish_available = False
        self._stockfish_evaluation: Optional[float] = None  # Current position score
        self._move_scores: List[Dict] = []  # History of move evaluations
    
    def start_game(self, player_color: str = "white") -> Dict[str, Any]:
        """Start a new chess game"""
        # Standard starting position
        self._board_state = [
            "r", "n", "b", "q", "k", "b", "n", "r",  # Black pieces
            "p", "p", "p", "p", "p", "p", "p", "p",  # Black pawns
            "", "", "", "", "", "", "", "",
            "", "", "", "", "", "", "", "",
            "", "", "", "", "", "", "", "",
            "", "", "", "", "", "", "", "",
            "P", "P", "P", "P", "P", "P", "P", "P",  # White pawns
            "R", "N", "B", "Q", "K", "B", "N", "R"   # White pieces
        ]
        self._current_turn = ChessColor.WHITE
        self._move_history = []
        self._game_active = True
        self._player_color = ChessColor(player_color)
        
        logger.info(f"Chess game started. Player is {player_color}")
        
        return {
            "status": "ok",
            "player_color": player_color,
            "board": self._board_state,
            "turn": self._current_turn.value
        }
    
    def _apply_move(self, move: ChessMove) -> bool:
        """Apply a move to the board"""
        try:
            from_idx = self._square_to_index(move.from_square)
            to_idx = self._square_to_index(move.to_square)
            
            # Move the piece
            piece = self._board_state[from_idx]
            self._board_state[to_idx] = piece
            self._board_state[from_idx] = ""
            
            # Handle promotion
            if move.promotion:
                promo_piece = move.promotion.lower()
                if self._current_turn == ChessColor.WHITE:
                    self._board_state[to_idx] = promo_piece.upper()
                else:
                    self._board_state[to_idx] = promo_piece.lower()
            
            # Switch turns
            self._current_turn = (
                ChessColor.BLACK if self._current_turn == ChessColor.WHITE 
                else ChessColor.WHITE
            )
            
            self._move_history.append(move)
            return True,
        except Exception as e:
            logger.error(f"Failed to apply move: {e}")
            return False,
    
    def _square_to_index(self, square: str) -> int:
        """Convert chess notation to board index"""
        col = ord(square[0]) - ord('a')
        row = int(square[1]) - 1
        return (7 - row) * 8 + col
    
    def _get_valid_moves(self, color: ChessColor) -> List[str]:
        """Get all valid moves for a color (simplified)"""
        # In full implementation, would use chess library or engine
        moves = []
        for i, piece in enumerate(self._board_state):
            if not piece:
                continue
            is_white = piece.isupper()
            if (color == ChessColor.WHITE and is_white) or \
               (color == ChessColor.BLACK and not is_white):
                # Generate some basic moves (simplified)
                moves.append(f"{chr((i % 8) + ord('a'))}{8 - (i // 8)}")
        return moves[:20]  # Return limited moves for demo
    
    async def get_ai_move(self) -> Optional[Dict[str, Any]]:
        """Get AI's next move with Stockfish evaluation."""
        if not self._game_active:
            return None
        
        params = personality_system.get_params()
        style = self._apply_personality_style(params, )
        
        ai_color = ChessColor.BLACK if self._player_color == ChessColor.WHITE else ChessColor.WHITE
        valid_moves = self._get_valid_moves(ai_color, )
        
        if not valid_moves:
            return None
        
        # Try Stockfish if available
        if self._stockfish_available:
            stockfish_result = await self._get_stockfish_move(style, )
            if stockfish_result:
                move_obj, eval_score = stockfish_result
                self._stockfish_evaluation = eval_score
                narrative = self._generate_move_narrative(move_obj, style, eval_score)
                
                return {
                    "move": move_obj,
                    "narrative": narrative,
                    "style": style,
                    "evaluation": eval_score,
                    "engine": "stockfish"
                }
        
        # Fallback to simulated move
        selected = self._select_move_by_strategy(valid_moves, style)
        move_obj = ChessMove(from_square=selected, to_square=valid_moves[0] if valid_moves else selected)
        narrative = self._generate_move_narrative(move_obj, style, None)
        
        return {"move": move_obj, "narrative": narrative, "style": style, "engine": "simulated"}
    
    async def _get_stockfish_move(self, style: Dict) -> Optional[tuple]:
        """Get move from Stockfish engine."""
        try:
            import subprocess
            # Build FEN string (simplified)
            fen = self._board_to_fen()
            
            # Adjust skill level based on personality
            skill_level = int(style.get("elo_adjust",0) / 100 + 10)  # Scale to 0-20
            skill_level = max(0, min(20, skill_level))
            
            # Run Stockfish
            cmd = [self._engine_path, fen, str(self._thinking_time_ms), str(skill_level)]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
            
            if result.returncode == 0:
                output = result.stdout.strip()
                # Parse output: "e2e4 eval:+0.5"
                parts = output.split()
                if len(parts) >= 1:
                    move_str = parts[0]
                    eval_score = float(parts[1].split(":")[1]) if len(parts) > 1 else 0.0
                    
                    move_obj = ChessMove(
                        from_square=move_str[:2],
                        to_square=move_str[2:4],
                        promotion=move_str[4] if len(move_str) > 4 else None
                    )
                    return move_obj, eval_score
        except Exception as e:
            logger.error(f"Stockfish error: {e}")
            self._stockfish_available = False
        return None
    
    def _board_to_fen(self) -> str:
        """Convert internal board state to FEN notation (simplified)."""
        # This is a placeholder - would need proper FEN generation
        return "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
    
    def get_current_evaluation(self) -> Optional[float]:
        """Get current position evaluation score."""
        return self._stockfish_evaluation

    def _apply_personality_style(self, params: Dict) -> Dict:
        """Map personality parameters to chess engine style."""
        style = {"contempt": 0, "search_width": 1.0, "sacrifice_tendency": 0.0, "elo_adjust": 0}
        
        # Map Big Five to chess style
        if params["openness"] > 0.7:
            # High openness -> creative openings, varied play
            style["search_width"] = 1.5
            style["sacrifice_tendency"] = 0.3
            style["elo_adjust"] = -200  # Lower ELO for more creative/risky play
        elif params["openness"] < 0.3:
            # Low openness -> standard openings, conservative
            style["search_width"] = 0.7
            style["elo_adjust"] = 100
            
        if params["conscientiousness"] > 0.7:
            # High conscientiousness -> solid defense, thorough analysis
            style["contempt"] = 15
            style["search_width"] = 0.8
            style["elo_adjust"] = 200  # Higher ELO for solid play
        elif params["conscientiousness"] < 0.3:
            # Low conscientiousness -> aggressive, less careful
            style["contempt"] = -10
            style["sacrifice_tendency"] = 0.5
            
        if params["extraversion"] > 0.7:
            # High extraversion -> more social/narrative during play
            style["narrative_depth"] = "high"
        else:
            style["narrative_depth"] = "low"
            
        return style

    def _select_move_by_strategy(self, valid_moves: List[str], style: Dict) -> str:
        """Select move based on style strategy."""
        if style["sacrifice_tendency"] > 0.2 and len(valid_moves) > 2:
            return random.choice(valid_moves[2:])
        elif style["contempt"] > 5:
            return valid_moves[0]
        return random.choice(valid_moves)

    def _generate_move_narrative(self, move: ChessMove, style: Dict) -> str:
        """Generate narrative commentary for the move."""
        personality = personality_system.get_response_style()
        tone = personality.get("language", {}).get("humor_type", "dry")
        
        if style["sacrifice_tendency"] > 0.2:
            return f"Let's try something bold! {move.from_square} to {move.to_square}."
        if style["contempt"] > 5:
            return f"A solid choice. {move.from_square} to {move.to_square}."
        return f"I move {move.from_square} to {move.to_square}."
    
    async     def make_move(self, move: str) -> Dict[str, Any]:
        """
        Make a move in the game.
        Format: "e2e4" or "e2-e4", """
        if not self._game_active:
            return {"status": "error", "reason": "Game not active"}
        
        # Parse move
        move = move.replace("-", "")
        if len(move) != 4:
            return {"status": "error", "reason": "Invalid move format"}
        
        chess_move = ChessMove(
            from_square=move[:2],
            to_square=move[2:]
        )
        
        # Apply player's move
        if not self._apply_move(chess_move):
            return {"status": "error", "reason": "Invalid move"}
        
        # Get AI response if game still active
        if self._game_active:
            ai_result = await self.get_ai_move()
            if ai_result:
                ai_move = ai_result["move"]
                self._apply_move(ai_move)
                ai_move_str = f"{ai_move.from_square}{ai_move.to_square}"
                ai_narrative = ai_result.get("narrative", "")
            else:
                ai_move_str = "pass"
                ai_narrative = ""
        else:
            ai_move_str = "none"
            ai_narrative = ""
        
        return {
            "status": "ok",
            "your_move": move,
            "ai_move": ai_move_str,
            "ai_narrative": ai_narrative,
            "turn": self._current_turn.value,
            "move_count": len(self._move_history)
        }
    
    def get_board_state(self) -> Dict[str, Any]:
        """Get current board state"""
        return {
            "board": self._board_state,
            "turn": self._current_turn.value,
            "move_history": [
                f"{m.from_square}{m.to_square}" for m in self._move_history
            ],
            "game_active": self._game_active
        }
    
    def get_status(self) -> Dict[str, Any]:
        """Get chess engine status"""
        return {
            "game_active": self._game_active,
            "current_turn": self._current_turn.value,
            "moves_played": len(self._move_history),
            "player_color": self._player_color.value
        }
    
    def end_game(self, result: str) -> Dict[str, Any]:
        """End the current game"""
        self._game_active = False
        logger.info(f"Chess game ended: {result}")
        return {
            "status": "ok",
            "result": result,
            "total_moves": len(self._move_history)
        }

# Global singleton
chess_engine = ChessEngine()