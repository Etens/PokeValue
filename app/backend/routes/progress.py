from flask import Blueprint, jsonify, request


progress = Blueprint("progress", __name__)
progress_state = {"step": "", "percent": 0}


@progress.route("/progress", methods=["POST"])
def receive_progress():
    data = request.json
    progress_state["step"] = data.get("step", "")
    progress_state["percent"] = data.get("percent", 0)
    return jsonify({"status": "ok"})


@progress.route("/progress/state", methods=["GET"])
def get_progress_state():
    return jsonify(progress_state)
