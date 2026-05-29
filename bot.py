import os
import re
import requests
from openai import OpenAI

WHATSAPP_TOKEN = os.environ.get("WHATSAPP_TOKEN")
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

# In-memory sessions { phone_number: { state, address, is_rent, price } }
sessions = {}

BOND_RATE = 0.0105  # ~10.5% interest over 20 years


def fmt(n):
    return f"R {int(n):,}".replace(",", " ")


def monthly_bond(price):
    return round(price * BOND_RATE)


def send_text(to, text, phone_id):
    requests.post(
        f"https://graph.facebook.com/v19.0/{phone_id}/messages",
        headers={"Authorization": f"Bearer {WHATSAPP_TOKEN}", "Content-Type": "application/json"},
        json={"messaging_product": "whatsapp", "to": to, "type": "text", "text": {"body": text}},
        timeout=10,
    )


def send_buttons(to, body, buttons, phone_id):
    requests.post(
        f"https://graph.facebook.com/v19.0/{phone_id}/messages",
        headers={"Authorization": f"Bearer {WHATSAPP_TOKEN}", "Content-Type": "application/json"},
        json={
            "messaging_product": "whatsapp",
            "to": to,
            "type": "interactive",
            "interactive": {
                "type": "button",
                "body": {"text": body},
                "action": {
                    "buttons": [
                        {"type": "reply", "reply": {"id": b["id"], "title": b["title"]}}
                        for b in buttons
                    ]
                },
            },
        },
        timeout=10,
    )


def extract_number(text):
    """Pull the first number out of a message (handles R25000, 25 000, 25k etc.)"""
    text = text.lower().replace(" ", "")
    # Handle shorthand like 25k, 1.2m
    match_k = re.search(r"(\d+\.?\d*)k", text)
    match_m = re.search(r"(\d+\.?\d*)m", text)
    if match_m:
        return int(float(match_m.group(1)) * 1_000_000)
    if match_k:
        return int(float(match_k.group(1)) * 1_000)
    digits = re.sub(r"[^\d]", "", text)
    return int(digits) if digits else None


def qualify(to, session, phone_id):
    price   = session["price"]
    salary  = session["salary"]
    is_rent = session["is_rent"]
    address = session["address"]

    monthly = price if is_rent else monthly_bond(price)
    required = monthly * 3
    qualified = salary >= required
    pct = round((monthly / salary) * 100)

    lines = [
        "📊 *Qualification Result*",
        "─────────────────────────",
        f"Property:  {address}",
    ]
    if not is_rent:
        lines.append(f"Purchase price:  {fmt(price)}")
    lines += [
        f"{'Monthly rent' if is_rent else 'Est. bond/mo'}:  {fmt(monthly)}/mo",
        f"Net salary:  {fmt(salary)}/mo",
        f"3x required:  {fmt(required)}/mo",
        f"Income used:  {pct}%",
        "─────────────────────────",
    ]

    if qualified:
        lines.append("✅ *QUALIFIED* — meets the 3x rule!")
    else:
        lines.append(f"❌ *NOT QUALIFIED*\nNeeds at least {fmt(required)}/mo salary.")

    send_text(to, "\n".join(lines), phone_id)

    if qualified:
        send_text(to, "🎉 Our agent will be in touch to arrange a viewing!\n\nTo check another property reply *hi*.", phone_id)
    else:
        send_buttons(to, "Would you like to check a different property?",
                     [{"id": "restart", "title": "Check another"}, {"id": "done", "title": "No thanks"}],
                     phone_id)


def handle_message(from_num, user_msg, phone_id):
    msg = user_msg.strip()
    s   = sessions.get(from_num, {"state": "start"})

    # ── Reset triggers ───────────────────────────────────────────────────────
    if msg.lower() in ("hi", "hello", "hey", "start", "menu", "restart"):
        sessions[from_num] = {"state": "address"}
        send_text(from_num,
                  "👋 Hi! Welcome.\n\nWhat is the *address or name* of the property you are interested in?",
                  phone_id)
        return

    # ── Step 1: capture address ──────────────────────────────────────────────
    if s["state"] == "address":
        sessions[from_num] = {"state": "type", "address": msg}
        send_buttons(from_num,
                     f"Got it — *{msg}*\n\nAre you buying or renting?",
                     [{"id": "buying", "title": "Buying"}, {"id": "renting", "title": "Renting"}],
                     phone_id)
        return

    # ── Step 2: buying or renting ────────────────────────────────────────────
    if s["state"] == "type" and msg.lower() in ("buying", "renting"):
        is_rent = msg.lower() == "renting"
        sessions[from_num] = {**s, "state": "price", "is_rent": is_rent}
        label = "monthly rent" if is_rent else "purchase price"
        send_text(from_num, f"What is the *{label}*? (e.g. 850000 or 15000)", phone_id)
        return

    # ── Step 3: capture price ────────────────────────────────────────────────
    if s["state"] == "price":
        amount = extract_number(msg)
        if not amount or amount < 500:
            send_text(from_num, "Please enter a valid amount (numbers only, e.g. *15000* or *1500000*).", phone_id)
            return
        sessions[from_num] = {**s, "state": "salary", "price": amount}
        send_text(from_num, "What is your *net monthly salary*? (e.g. 35000)", phone_id)
        return

    # ── Step 4: capture salary & qualify ────────────────────────────────────
    if s["state"] == "salary":
        salary = extract_number(msg)
        if not salary or salary < 500:
            send_text(from_num, "Please enter a valid salary (e.g. *25000*).", phone_id)
            return
        sessions[from_num] = {**s, "salary": salary}
        qualify(from_num, sessions[from_num], phone_id)
        sessions[from_num]["state"] = "done"
        return

    # ── Fallback ─────────────────────────────────────────────────────────────
    resp = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a friendly WhatsApp assistant for a South African property agent. Keep replies under 2 sentences. Always end by asking the user to reply 'hi' to start a qualification."},
            {"role": "user",   "content": msg},
        ],
        max_tokens=80,
    )
    send_text(from_num, resp.choices[0].message.content.strip(), phone_id)
    sessions[from_num] = {"state": "start"}
