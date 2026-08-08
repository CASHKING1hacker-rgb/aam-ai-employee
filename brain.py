import requests
import re

from config import API_KEY, MODEL

from memory import (
    get_recent_chats,
    create_order,
    pending_order_exists,
    SERVICES,
    log_action,
    save_invoice
)

URL = (
    f"https://generativelanguage.googleapis.com/v1beta/"
    f"{MODEL}:generateContent?key={API_KEY}"
)


def reply(message, customer_id):

    msg = message.lower().strip()

    # ==========================
    # MENU SELECTION
    # ==========================

    if msg == "1":
        msg = "activation"

    elif msg == "2":
        msg = "monthly premium"

    elif msg == "3":
        msg = "weekly premium"

    # ==========================
    # INVOICE / PAYMENT REFERENCE
    # ==========================

    invoice_pattern = r"^(AAM-\d{6}|[A-Za-z0-9]{6,20})$"

    if re.match(invoice_pattern, message.strip()):

        save_invoice(
            customer_id,
            message.strip()
        )

        return (
            "✅ Invoice received successfully.\n\n"
            "📦 Your payment reference has been attached to your order.\n"
            "⏳ Status: Waiting for verification.\n\n"
            "Our team will verify your payment and update your order."
        )

    invoice = None
    order_id = None
    service = None
    amount = None

    # ==========================
    # ORDER DETECTION
    # ==========================

    if any(word in msg for word in [
        "activate",
        "activation",
        "airtel"
    ]):

        service = "Unlimited Airtel Data Activation"

        if pending_order_exists(customer_id, service):

            amount = SERVICES.get(service, 0)

            return (
                "✅ You already have a pending order.\n\n"
                f"📦 Service: {service}\n"
                f"💰 Amount: {amount:,} UGX\n\n"
                "Please complete your payment for the existing order.\n\n"
                "If you have already paid, upload your payment screenshot "
                "using the Upload Payment Screenshot button in My Orders."
            )

        order_id, invoice = create_order(
            customer_id,
            service
        )

        amount = SERVICES.get(service, 0)

        log_action(
            f"New order created: {invoice}"
        )

    elif any(word in msg for word in [
        "monthly premium",
        "monthly files",
        "weekly premium",
        "weekly files"
    ]):

        if "weekly" in msg:
            service = "Weekly Premium Files"
        else:
            service = "Monthly Premium Files"

        if pending_order_exists(customer_id, service):

            amount = SERVICES.get(service, 0)

            return (
                "✅ You already have a pending order.\n\n"
                f"📦 Service: {service}\n"
                f"💰 Amount: {amount:,} UGX\n\n"
                "Please complete your payment for the existing order.\n\n"
                "If you have already paid, upload your payment screenshot "
                "using the Upload Payment Screenshot button in My Orders."
            )

        order_id, invoice = create_order(
            customer_id,
            service
        )

        amount = SERVICES.get(service, 0)

        log_action(
            f"New order created: {invoice}"
        )

    # ==========================
    # LOAD KNOWLEDGE
    # ==========================

    with open(
        "knowledge.txt",
        "r",
        encoding="utf-8"
    ) as f:

        knowledge = f.read()

    # ==========================
    # CHAT MEMORY
    # ==========================

    chats = get_recent_chats(
        customer_id,
        limit=10
    )

    messages = []

    system_prompt = f"""
You are the AI employee for A.A.M CASH KING1.

Use the following business knowledge:

{knowledge}

Be helpful, concise and professional.

If an order has already been created by the system, do not create
another order yourself.
"""

    messages.append({
        "role": "user",
        "parts": [
            {
                "text": system_prompt
            }
        ]
    })

    for chat in chats:

        messages.append({
            "role": "user",
            "parts": [
                {
                    "text": chat["user_message"]
                }
            ]
        })

        messages.append({
            "role": "model",
            "parts": [
                {
                    "text": chat["ai_reply"]
                }
            ]
        })

    messages.append({
        "role": "user",
        "parts": [
            {
                "text": message
            }
        ]
    })

    # ==========================
    # GEMINI REQUEST
    # ==========================

    payload = {
        "contents": messages
    }

    try:

        response = requests.post(
            URL,
            json=payload,
            timeout=30
        )

        data = response.json()

        if response.status_code != 200:

            error = data.get(
                "error",
                {}
            )

            return error.get(
                "message",
                "AI service temporarily unavailable."
            )

        answer = (
            data["candidates"][0]["content"]["parts"][0]["text"]
        )

    except Exception as e:

        print("GEMINI ERROR:", e)

        answer = (
            "Sorry, I am temporarily unable to respond. "
            "Please try again shortly."
        )

    # ==========================
    # ADD ORDER DETAILS
    # ==========================

    if order_id:

        answer += f"""

📦 ORDER DETAILS

✅ Service: {service}

💰 Amount: {amount:,} UGX

🧾 Invoice: {invoice}

💳 Please make payment using the payment method provided above.

📸 After payment, upload your payment screenshot here:

/payment/{order_id}
"""

    return answer
