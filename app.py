import os
import json
from flask import Flask, request, jsonify
from bot import handle_message

app = Flask(__name__)

VERIFY_TOKEN = os.environ.get("VERIFY_TOKEN", "realtor_bot_secret")

# ── Webhook verification (Meta requires this on setup) ──────────────────────
@app.route("/webhook", methods=["GET"])
def verify():
    mode      = request.args.get("hub.mode")
    token     = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")
    if mode == "subscribe" and token == VERIFY_TOKEN:
        return challenge, 200
    return "Forbidden", 403

# ── Incoming messages ────────────────────────────────────────────────────────
@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json()
    try:
        entry   = data["entry"][0]
        changes = entry["changes"][0]["value"]
        if "messages" not in changes:
            return jsonify({"status": "no message"}), 200

        msg      = changes["messages"][0]
        from_num = msg["from"]          # sender's WhatsApp number
        msg_type = msg["type"]

        if msg_type == "text":
            user_text = msg["text"]["body"].strip()
        elif msg_type == "interactive":
            # Button / list reply
            interactive = msg["interactive"]
            if interactive["type"] == "button_reply":
                user_text = interactive["button_reply"]["id"]
            elif interactive["type"] == "list_reply":
                user_text = interactive["list_reply"]["id"]
            else:
                user_text = ""
        else:
            user_text = ""

        if user_text:
            handle_message(from_num, user_text, changes["metadata"]["phone_number_id"])

    except (KeyError, IndexError):
        pass  # silently ignore malformed payloads

    return jsonify({"status": "ok"}), 200


if __name__ == "__main__":
    app.run(port=5000, debug=True)
