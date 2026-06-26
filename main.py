from pathlib import Path
import random
from flask import Flask, render_template, jsonify, request, redirect
from config import GameConfig, INITIAL_GAME_STATE
from game.manager import game_manager
from game.services import GameService, MemoryGameService, now_ms

BASE_DIR = Path(__file__).resolve().parent
app = Flask(
    __name__,
    root_path=str(BASE_DIR),
    template_folder="templates",
)


def parse_index(payload):
    try:
        return int(payload.get("index"))
    except (TypeError, ValueError, AttributeError):
        return None


@app.route("/")
def index() -> str:
    game_manager.check_expiration(now_ms)
    return render_template("index.html")


@app.route("/bakla")
def admin_panel() -> str:
    game_manager.check_expiration(now_ms)
    return render_template("admin.html", state=game_manager.get_state())


@app.route("/api/state", methods=["GET"])
def get_state():
    game_manager.check_expiration(now_ms)
    state = game_manager.get_state()
    player = game_manager.get_memory_player() if state["memory_event_active"] else {
        "lives": state["memory_lives_default"],
        "locked": False,
        "won": False,
        "selected": []
    }
    
    response_state = state.copy()
    response_state["my_memory_player"] = player
    return jsonify(response_state)


@app.route("/api/configure", methods=["POST"])
def configure_game():
    title = request.form.get("title", "Fast Handed Yarn??").strip()
    announcement = request.form.get("announcement", "").strip()
    target_link = request.form.get("target_link", "").strip()
    try:
        num_links = max(1, min(int(request.form.get("num_links", 5)), GameConfig.BOX_COUNT))
        duration = max(5, int(request.form.get("duration", 30)))
    except ValueError:
        return redirect("/bakla")

    winning_boxes = random.sample(list(range(GameConfig.BOX_COUNT)), num_links)

    game_manager.reset_events()
    game_manager.update_state({
        "title": title,
        "announcement": announcement or "Game is live!",
        "global_message": "",
        "target_link": target_link,
        "total_seconds": duration,
        "start_time": now_ms(),
        "active": True,
        "winning_boxes": winning_boxes,
        "click_count": 0,
        "revealed": False,
    })
    return redirect("/bakla")


@app.route("/api/ice/trigger", methods=["POST"])
def trigger_ice():
    ice_link = request.form.get("ice_link", "").strip()
    if ice_link:
        game_manager.reset_events()
        game_manager.update_state({
            "ice_event_active": True,
            "ice_link": ice_link,
            "winning_boxes": random.sample(list(range(GameConfig.BOX_COUNT)), 5),
            "click_count": 0,
            "start_time": now_ms(),
        })
    return redirect("/bakla")


@app.route("/api/ice/stop", methods=["POST"])
def stop_ice():
    game_manager.set_value("ice_event_active", False)
    return redirect("/bakla")


@app.route("/api/fire/trigger", methods=["POST"])
def trigger_fire():
    fire_link = request.form.get("fire_link", "").strip()
    if fire_link:
        game_manager.reset_events()
        game_manager.update_state({
            "fire_event_active": True,
            "fire_link": fire_link,
            "winning_boxes": random.sample(list(range(GameConfig.BOX_COUNT)), 5),
            "click_count": 0,
            "start_time": now_ms(),
        })
    return redirect("/bakla")


@app.route("/api/fire/stop", methods=["POST"])
def stop_fire():
    game_manager.set_value("fire_event_active", False)
    return redirect("/bakla")


@app.route("/api/holy/trigger", methods=["POST"])
def trigger_holy():
    holy_link = request.form.get("holy_link", "").strip()
    try:
        speed = int(request.form.get("holy_speed", 60))
    except ValueError:
        speed = 60

    if holy_link:
        game_manager.reset_events()
        game_manager.update_state({
            "holy_event_active": True,
            "holy_link": holy_link,
            "holy_speed": speed,
            "ice_event_active": False,
            "fire_event_active": False,
            "memory_event_active": False,
            "start_time": now_ms(),
        })
    return redirect("/bakla")


@app.route("/api/holy/stop", methods=["POST"])
def stop_holy():
    game_manager.set_value("holy_event_active", False)
    return redirect("/bakla")


@app.route("/api/holy/click", methods=["POST"])
def holy_click():
    game_manager.increment_click_count()
    return jsonify({"status": "success"})


@app.route("/api/memory/trigger", methods=["POST"])
def trigger_memory():
    memory_target_link = request.form.get("memory_target_link", "").strip()
    memory_winner_link = request.form.get("memory_winner_link", "").strip() or memory_target_link
    try:
        memory_total_seconds = max(5, int(request.form.get("memory_total_seconds", 30)))
        memory_lives_default = max(1, int(request.form.get("memory_lives_default", 3)))
    except ValueError:
        return redirect("/bakla")

    if memory_target_link:
        game_manager.reset_events()
        game_manager.update_state({
            "memory_event_active": True,
            "memory_target_link": memory_target_link,
            "memory_winner_link": memory_winner_link,
            "memory_total_seconds": memory_total_seconds,
            "memory_lives_default": memory_lives_default,
            "memory_start_time": now_ms(),
            "memory_reveal_until": now_ms() + GameConfig.MEMORY_REVEAL_MS,
            "memory_board": MemoryGameService.make_board(),
            "memory_matched_positions": [],
            "memory_game_over": False,
            "click_count": 0,
            "active": False,
            "revealed": False,
            "winning_boxes": [],
        })
        game_manager.reset_memory_players()
    return redirect("/bakla")


@app.route("/api/memory/stop", methods=["POST"])
def stop_memory():
    game_manager.update_state({
        "memory_event_active": False,
        "memory_game_over": False,
        "memory_reveal_until": None,
    })
    return redirect("/bakla")


@app.route("/api/memory/click", methods=["POST"])
def memory_click():
    data = request.get_json() or {}
    index = parse_index(data)
    if index is None:
        return jsonify({"status": "invalid"})
    result = MemoryGameService.handle_click(index)
    return jsonify(result)


@app.route("/api/broadcast", methods=["POST"])
def send_broadcast():
    message = request.form.get("global_message", "").strip()
    game_manager.set_value("global_message", message)
    return redirect("/bakla")


@app.route("/api/reset", methods=["POST"])
def reset_game():
    game_manager.update_state(INITIAL_GAME_STATE.copy())
    return redirect("/bakla")


@app.route("/api/shutdown", methods=["POST"])
def shutdown_server():
    game_manager.set_value("server_closed", True)
    return redirect("/bakla")


@app.route("/api/reopen", methods=["POST"])
def reopen_server():
    game_manager.set_value("server_closed", False)
    return redirect("/bakla")


@app.route("/api/click", methods=["POST"])
def handle_click():
    data = request.get_json() or {}
    index = parse_index(data)
    if index is None:
        return jsonify({"status": "invalid"})
    result = GameService.handle_click(index)
    return jsonify(result)


@app.before_request
def _before():
    game_manager.check_expiration(now_ms)
    game_manager.check_memory_timeout(now_ms)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
