import threading
from typing import Dict, Any
from config import INITIAL_GAME_STATE

class GameStateManager:
    def __init__(self):
        self._state = INITIAL_GAME_STATE.copy()
        self._lock = threading.Lock()

    def get_state(self) -> Dict[str, Any]:
        with self._lock:
            return self._state.copy()

    def update_state(self, updates: Dict[str, Any]):
        with self._lock:
            self._state.update(updates)

    def set_value(self, key: str, value: Any):
        with self._lock:
            self._state[key] = value

    def get_value(self, key: str) -> Any:
        with self._lock:
            return self._state.get(key)

    def reset_events(self):
        with self._lock:
            self._state.update({
                "holy_event_active": False,
                "ice_event_active": False,
                "fire_event_active": False,
                "memory_event_active": False,
            })

    def increment_click_count(self):
        with self._lock:
            self._state["click_count"] += 1

    def get_memory_player(self) -> Dict[str, Any]:
        with self._lock:
            player = self._state.get("memory_player_state")
            if not isinstance(player, dict) or not player:
                player = {
                    "lives": self._state["memory_lives_default"],
                    "locked": False,
                    "won": False,
                    "selected": []
                }
                self._state["memory_player_state"] = player
            return player

    def reset_memory_players(self):
        with self._lock:
            self._state["memory_player_state"] = {
                "lives": self._state["memory_lives_default"],
                "locked": False,
                "won": False,
                "selected": []
            }

    def check_expiration(self, now_ms_func):
        with self._lock:
            s = self._state
            if (
                s["active"]
                and not s["holy_event_active"]
                and not s["ice_event_active"]
                and not s["fire_event_active"]
                and not s["memory_event_active"]
                and s["start_time"] is not None
            ):
                elapsed_ms = now_ms_func() - s["start_time"]
                if elapsed_ms >= (s["total_seconds"] * 1000):
                    s["active"] = False
                    s["revealed"] = True

    def check_memory_timeout(self, now_ms_func):
        with self._lock:
            s = self._state
            if s["memory_event_active"] and not s["memory_game_over"] and s["memory_start_time"]:
                elapsed = now_ms_func() - s["memory_start_time"]
                if elapsed >= (s["memory_total_seconds"] * 1000):
                    s["memory_game_over"] = True


game_manager = GameStateManager()
