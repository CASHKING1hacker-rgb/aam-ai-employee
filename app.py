from flask import (
    Flask,
    render_template,
    request,
    redirect,
    session,
    jsonify,
    send_from_directory
)

import os

from werkzeug.utils import secure_filename

from brain import reply

from admin_config import (
    ADMIN_USERNAME,
    ADMIN_PASSWORD
)

from memory import (
    create_database,
    create_customer,
    get_customer,
    save_chat,
    get_recent_chats,
    get_orders,
    search_orders,
    update_order_status,
    delete_order,
    save_payment_proof,
    approve_payment,
    reject_payment,
    count_customers,
    count_orders,
    count_chats,
    get_order,
    get_all_payments,
    revenue_today,
    get_recent_activity,
    create_notification,
    log_action,
    get_customer_orders,
    get_customers,
    get_customer_chats,
    get_notifications,
    get_customer_chat
)

# ===============================
# APP SETUP
# ===============================

app = Flask(__name__)

app.secret_key = os.getenv("FLASK_SECRET_KEY")

UPLOAD_FOLDER = "static/uploads"

os.makedirs(
    UPLOAD_FOLDER,
    exist_ok=True
)

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

create_database()


# ===============================
# CUSTOMER REGISTRATION
# ===============================

@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        name = request.form["name"].strip()
        phone = request.form["phone"].strip()

        if not name or not phone:

            return render_template(
                "register.html",
                error="Please fill in all fields."
            )

        customer_id = create_customer(
            name,
            phone
        )

        session["customer_id"] = customer_id
        session["customer_name"] = name

        return redirect("/")

    return render_template("register.html")


# ===============================
# HOME PAGE
# ===============================

@app.route("/")
def home():

    if "customer_id" not in session:
        return redirect("/register")

    customer_id = session["customer_id"]

    chats = get_recent_chats(
        customer_id,
        limit=100
    )

    notifications = get_notifications(
        customer_id
    )
    
    orders = get_customer_orders(customer_id)

    return render_template(
        "index.html",
        chats=chats,
        customer=session["customer_name"],
        notifications=notifications,
        orders=orders
    )


# ===============================
# CUSTOMER LOGOUT
# ===============================

@app.route("/logout")
def logout():

    session.clear()

    return redirect("/register")
    
# ===============================
# LIVE AI CHAT (AJAX)
# ===============================

@app.route("/send", methods=["POST"])
def send():

    if "customer_id" not in session:
        return jsonify({
            "reply": "Session expired. Please register again."
        })

    data = request.get_json()

    if not data:
        return jsonify({
            "reply": "No message received."
        })

    message = data.get("message", "").strip()

    if message == "":
        return jsonify({
            "reply": "Please type a message."
        })

    customer_id = session["customer_id"]

    try:

        ai_reply = reply(
            message,
            customer_id
        )

        save_chat(
            customer_id,
            message,
            ai_reply
        )

        return jsonify({
            "reply": ai_reply
        })

    except Exception as e:

        print("AI ERROR:", e)

        return jsonify({
            "reply": f"System error: {e}"
        })


# ===============================
# CHAT HISTORY API
# ===============================

@app.route("/history")
def history():

    if "customer_id" not in session:
        return jsonify([])

    chats = get_recent_chats(
        session["customer_id"],
        limit=100
    )

    history = []

    for chat in chats:

        history.append({
            "user": chat["user_message"],
            "ai": chat["ai_reply"]
        })

    return jsonify(history)
    
# ===============================
# ADMIN LOGIN
# ===============================

@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():

    if request.method == "POST":

        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()

        if (
            username == ADMIN_USERNAME
            and
            password == ADMIN_PASSWORD
        ):

            session["admin"] = True

            return redirect("/admin")

        return render_template(
            "login.html",
            error="Invalid username or password."
        )

    return render_template("login.html")


# ===============================
# ADMIN DASHBOARD
# ===============================

@app.route("/admin")
def admin():

    if not session.get("admin"):
        return redirect("/admin/login")

    activity = get_recent_activity()

    return render_template(
        "admin.html",
        customers=count_customers(),
        chats=count_chats(),
        orders=count_orders(),
        revenue=revenue_today(),
        order_list=get_orders(),
        activity=activity
    )


# ===============================
# ADMIN LOGOUT
# ===============================

@app.route("/admin/logout")
def admin_logout():

    session.pop("admin", None)

    return redirect("/admin/login")


# ===============================
# SEARCH ORDERS
# ===============================

@app.route("/search")
def search():

    if not session.get("admin"):
        return redirect("/admin/login")

    keyword = request.args.get("q", "").strip()

    if keyword == "":
        orders = get_orders()
    else:
        orders = search_orders(keyword)

    return render_template(
        "admin.html",
        customers=count_customers(),
        chats=count_chats(),
        orders=count_orders(),
        revenue=revenue_today(),
        order_list=orders
    )
    
# ===============================
# COMPLETE ORDER
# ===============================

@app.route("/complete/<int:order_id>")
def complete_order(order_id):

    if not session.get("admin"):
        return redirect("/admin/login")

    update_order_status(
        order_id,
        "Completed"
    )

    return redirect("/admin")


# ===============================
# DELETE ORDER
# ===============================

@app.route("/delete/<int:order_id>")
def remove_order(order_id):

    if not session.get("admin"):
        return redirect("/admin/login")

    delete_order(order_id)

    return redirect("/admin")


# ===============================
# PAYMENT UPLOAD
# ===============================

@app.route("/payment/<int:order_id>", methods=["GET", "POST"])
def payment(order_id):

    if request.method == "POST":

        file = request.files.get("proof")

        if file:

            filename = file.filename

            file.save(
                "uploads/" + filename
            )

            save_payment_proof(
                order_id,
                filename
            )

            log_action(f"Payment proof uploaded for Order #{order_id}")

            return """
            <h2>✅ Payment proof uploaded</h2>
            <p>Waiting for approval.</p>
            """

    order = get_order(order_id)

    return render_template(
        "payment.html",
        order=order
    )


# ===============================
# APPROVE PAYMENT
# ===============================

@app.route("/approve/<int:order_id>")
def approve(order_id):

    if not session.get("admin"):
        return redirect("/admin/login")

    approve_payment(order_id)

    order = get_order(order_id)

    if order:

        create_notification(
            order["customer_id"],
            "✅ Your payment has been approved. Your order is now being processed."
        )

    log_action(f"Payment approved for Order #{order_id}")

    return redirect("/admin/payments")


# ===============================
# REJECT PAYMENT
# ===============================

@app.route("/reject/<int:order_id>")
def reject(order_id):

    if not session.get("admin"):
        return redirect("/admin/login")

    reject_payment(order_id)

    order = get_order(order_id)

    if order:

        create_notification(
            order["customer_id"],
            "❌ Your payment was rejected. Please contact support or upload a valid payment proof."
        )

    log_action(f"Payment rejected for Order #{order_id}")

    return redirect("/admin/payments")

@app.route("/admin/payments")
def admin_payments():

    if not session.get("admin"):
        return redirect("/admin/login")

    payments = get_all_payments()
    orders = get_orders()

    return render_template(
        "payments.html",
        payments=payments,
        orders=orders
    )

@app.route("/uploads/<filename>")
def uploaded_file(filename):

    return send_from_directory(
        "uploads",
        filename
    )
       
@app.route("/admin/customers")
def admin_customers():

    if not session.get("admin"):
        return redirect("/admin/login")

    return render_template(
        "customers.html",
        customers=get_customers()
    )                  
     
@app.route("/admin/customer/<int:customer_id>")
def customer_chat(customer_id):

    if not session.get("admin"):
        return redirect("/admin/login")

    chats = get_customer_chat(customer_id)

    return render_template(
        "customer_chat.html",
        chats=chats,
        customer_id=customer_id
    )                                        

                                                                                                                                                                                                                                                                                                                                                                                                          
# ===============================
# START SERVER
# ===============================

if __name__ == "__main__":

    app.run(
        debug=True,
        host="0.0.0.0",
        port=5000
    )                            
