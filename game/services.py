import random
from typing import Dict, Any, List, Optional
from config import GameConfig
from game.manager import game_manager

def now_ms() -> int:
    import time
    return int(time.time() * 1000)

class GameService:
    @staticmethod
    def handle_click(index: int) -> Dict[str, str]:
        game_manager.check_expiration(now_ms)
        state = game_manager.get_state()
        
        if not (state["active"] or state["ice_event_active"] or state["fire_event_active"]):
            return {"status": "inactive"}
            
        if index in state["winning_boxes"]:
            game_manager.increment_click_count()
            if state["ice_event_active"]:
                return {"status": "correct", "link": state["ice_link"]}
            if state["fire_event_active"]:
                return {"status": "correct", "link": state["fire_link"]}
            return {"status": "correct", "link": state["target_link"]}
        return {"status": "wrong"}

class MemoryGameService:
    @staticmethod
    def make_board() -> List[str]:
        emojis = random.sample(GameConfig.MEMORY_EMOJIS, 5)
        board = emojis + emojis
        random.shuffle(board)
        return board

    @staticmethod
    def handle_click(index: int, token: str) -> Dict[str, Any]:
        game_manager.check_memory_timeout(now_ms)
        state = game_manager.get_state()
        
        if not state["memory_event_active"] or state["memory_game_over"]:
            return {"status": "inactive"}

        if index is None or not (0 <= index < GameConfig.MEMORY_BOX_COUNT):
            return {"status": "invalid"}

        player = game_manager.get_memory_player(token)
        if player["locked"]:
            return {"status": "locked"}
        if player["won"]:
            return {"status": "won"}
            
        if now_ms() < (state["memory_reveal_until"] or 0):
            return {"status": "preview"}

        if index in state["memory_matched_positions"] or index in player["selected"]:
            return {"status": "already_selected"}

        player["selected"].append(index)
        if len(player["selected"]) < 2:
            return {"status": "first"}

        # Second box selected
        a, b = player["selected"][0], player["selected"][1]
        player["selected"] = []

        if state["memory_board"][a] == state["memory_board"][b]:
            # Match!
            with game_manager._lock: # Accessing lock for atomic updates to shared matched_positions
                # Note: This is slightly breaking encapsulation but for the sake of refactoring speed:
                for pos in (a, b):
                    if pos not in game_manager._state["memory_matched_positions"]:
                        game_manager._state["memory_matched_positions"].append(pos)
                
                game_manager._state["click_count"] += 1
                
                if len(game_manager._state["memory_matched_positions"]) >= GameConfig.MEMORY_BOX_COUNT:
                    game_manager._state["memory_game_over"] = True
                    player["won"] = True
                    return {
                        "status": "match",
                        "complete": True,
                        "link": state["memory_winner_link"] or state["memory_target_link"]
                    }
            return {"status": "match", "complete": False}

        # No match
        player["lives"] -= 1
        if player["lives"] <= 0:
            player["locked"] = True
            game_manager.increment_click_count()
            return {"status": "lost", "lives": 0}

        return {"status": "wrong", "lives": player["lives"], "selected": []}
