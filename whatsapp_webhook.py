from fastapi import FastAPI, Request
from fastapi.responses import PlainTextResponse
from dotenv import load_dotenv
import os
import requests

# Load .env variables
load_dotenv()

app = FastAPI()

# Read values from .env
VERIFY_TOKEN = os.getenv("VERIFY_TOKEN")
ACCESS_TOKEN = os.getenv("WHATSAPP_ACCESS_TOKEN")
PHONE_NUMBER_ID = os.getenv("WHATSAPP_PHONE_NUMBER_ID")


@app.get("/webhook")
async def verify_webhook(request: Request):
    params = request.query_params
    mode = params.get("hub.mode")
    token = params.get("hub.verify_token")
    challenge = params.get("hub.challenge")

    if mode == "subscribe" and token == VERIFY_TOKEN:
        return PlainTextResponse(challenge)

    return PlainTextResponse("Verification failed", status_code=403)


@app.post("/webhook")
async def receive_message(request: Request):
    data = await request.json()
    print("📩 Incoming webhook:", data)

    try:
        entry = data["entry"][0]
        changes = entry["changes"][0]
        value = changes["value"]

        if "messages" in value:
            message = value["messages"][0]
            from_number = message["from"]  # FIXED
            text = message.get("text", {}).get("body", "")

            print(f"Message from {from_number}: {text}")

            # Run spam / fraud check
            reply_text = check_spam(text)

            # Send WhatsApp reply
            send_whatsapp_message(from_number, reply_text)

    except Exception as e:
        print("❌ Error while processing webhook:", e)

    return {"status": "ok"}


def check_spam(text: str) -> str:
    suspicious_keywords = [
        "lottery", "win money", "prize", "jackpot", "free gift",
        "click link", "click here", "upi", "otp", "kbc", "verification code"
    ]

    if any(word in text.lower() for word in suspicious_keywords):
        return (
            "🚨 *Warning: This message looks suspicious!*\n\n"
            "⚠️ Do NOT click any links.\n"
            "⚠️ Do NOT share OTP, PIN, or bank details with anyone.\n\n"
            "If someone is asking for money or personal information, it may be a scam."
        )
    else:
        return (
            "✅ This message does not match common scam patterns.\n"
            "But always be careful and never share OTP, PIN or bank details."
        )


def send_whatsapp_message(to: str, text: str):
    url = f"https://graph.facebook.com/v21.0/{PHONE_NUMBER_ID}/messages"

    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json",
    }

    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "text",
        "text": {
            "preview_url": False,
            "body": text,
        },
    }

    response = requests.post(url, json=payload, headers=headers)
    print("📤 WhatsApp API response:", response.status_code, response.text)
