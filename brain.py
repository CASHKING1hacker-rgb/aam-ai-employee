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

    msg = message.lower()

    if msg == "1":
        msg = "activation"

    elif msg == "2":
        msg = "monthly premium"

    elif msg == "3":
        msg = "weekly premium"

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

            return (
                "✅ You already have a pending order.\n\n"
                f"📦 Service: {service}\n"
                "💰 Amount: 53,000 UGX\n\n"
                "Please complete your payment for the existing order. "
                "If you have already paid, send your Invoice/Transaction ID "
                "and I will help you continue."
            )

        order_id, invoice = create_order(
            customer_id,
            service
        )

        amount = SERVICES.get(service, 0)

        log_action(f"New order created: {invoice}")

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
                "Please complete your payment for the existing order. "
                "If you have already paid, send your payment reference."
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

    history = get_recent_chats(
        customer_id,
        limit=10
    )

    history_text = ""

    for user_msg, ai_msg in history:
        history_text += f"User: {user_msg}\n"
        history_text += f"Assistant: {ai_msg}\n\n"

    prompt = f"""
{knowledge}

Previous conversation:
{history_text}

User: {message}

Assistant:
"""
    
    # ==========================
    # AI REQUEST
    # ==========================

    headers = {
        "Content-Type": "application/json"
    }

    data = {
        "contents": [
            {
                "parts": [
                    {
                        "text": prompt
                    }
                ]
            }
        ]
    }

    try:
        print(URL)

        response = requests.post(
            URL,
            headers=headers,
            json=data,
            timeout=60
        )

        print(response.status_code)
        print(response.text)

        result = response.json()

        if "error" in result:
            return result["error"]["message"]

        answer = result["candidates"][0]["content"]["parts"][0]["text"]

        if (
            "User Safety:" in answer
            or "Response Safety:" in answer
        ):
            answer = (
                "Hello! 👋 Welcome to A.A.M CASH KING1. "
                "How can I help you today?"
            )

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

    except Exception as e:
        return f"Connection error: {e}"

       

           
