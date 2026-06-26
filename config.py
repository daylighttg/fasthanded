import string

class GameConfig:
    BOX_COUNT = 200  # Regular game boxes
    MEMORY_BOX_COUNT = 10  # Memory game boxes (5 pairs)
    MEMORY_EMOJIS = ["🍎", "🍌", "🍇", "🍓", "🍉", "🍒", "⭐", "💎", "🔥", "⚡", "🌙", "🎯"]
    MEMORY_REVEAL_MS = 2000
    MEMORY_MIN_SECONDS = 5
    PLAYER_TIMEOUT_MS = 100
    DEFAULT_SERVER_CLOSED_LINK = ""

INITIAL_GAME_STATE = {
    "title": "Fast Handed Yarn??",
    "announcement": "Waiting for host to broadcast...",
    "global_message": "",
    "target_link": "",
    "total_seconds": 30,
    "start_time": None,
    "active": False,
    "winning_boxes": [],
    "click_count": 0,
    "revealed": False,

    # Celestial Holy Event
    "holy_event_active": False,
    "holy_link": "",
    "holy_speed": 60,

    # Ice Event
    "ice_event_active": False,
    "ice_link": "",

    # Fire Event
    "fire_event_active": False,
    "fire_link": "",

    # Memory Event
    "memory_event_active": False,
    "memory_target_link": "",
    "memory_winner_link": "",
    "memory_total_seconds": 30,
    "memory_lives_default": 3,
    "memory_start_time": None,
    "memory_reveal_until": None,
    "memory_board": [],
    "memory_matched_positions": [],
    "memory_game_over": False,
    "memory_player_state": {},  # anonymous memory player -> {lives, locked, won, selected}

    # Server Shutdown Redirect
    "server_closed": False,
    "server_closed_link": GameConfig.DEFAULT_SERVER_CLOSED_LINK,
}
