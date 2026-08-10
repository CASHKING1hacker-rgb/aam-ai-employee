const form = document.getElementById("chat-form");
const input = document.getElementById("message");
const chatBox = document.getElementById("chat-box");

function scrollBottom() {
    if (chatBox) {
        chatBox.scrollTop = chatBox.scrollHeight;
    }
}

scrollBottom();


// =====================================================
// CUSTOMER SEND MESSAGE
// =====================================================

if (form) {

    form.addEventListener("submit", async function (e) {

        e.preventDefault();

        const message = input.value.trim();

        if (message === "") return;

        // Show user's message immediately
        const user = document.createElement("div");

        user.className = "user-message";

        user.textContent = "👤 " + message;

        chatBox.appendChild(user);

        input.value = "";

        scrollBottom();


        // AI typing indicator
        const typing = document.createElement("div");

        typing.className = "ai-message";

        typing.id = "typing";

        typing.textContent = "🤖 AI is typing...";

        chatBox.appendChild(typing);

        scrollBottom();


        try {

            const response = await fetch("/send", {

                method: "POST",

                headers: {
                    "Content-Type": "application/json"
                },

                body: JSON.stringify({
                    message: message
                })

            });


            const data = await response.json();


            if (typing) {
                typing.remove();
            }


            const ai = document.createElement("div");

            ai.className = "ai-message";

            ai.innerHTML =
                "🤖 " +
                String(data.reply || "").replace(/\n/g, "<br>");

            chatBox.appendChild(ai);

            scrollBottom();


            // Refresh order/payment information if necessary
            if (
                data.reply &&
                data.reply.includes("/payment/")
            ) {

                window.location.reload();

            }


        } catch (err) {

            if (typing) {

                typing.textContent =
                    "❌ Failed to contact server.";

            }

            console.log("SEND ERROR:", err);

            scrollBottom();

        }

    });

}


// =====================================================
// ADMIN MESSAGE TRACKING
// =====================================================

// Messages already displayed on the customer screen.
//
// We use type + message + timestamp as a unique signature.
// This prevents the same admin message from appearing twice.

const displayedAdminMessages = new Set();


// =====================================================
// CHECK FOR ADMIN REPLIES
// =====================================================

async function checkAdminReplies() {

    if (!chatBox) return;

    try {

        const response = await fetch(
            "/history?_=" + Date.now(),
            {
                cache: "no-store"
            }
        );


        if (!response.ok) {
            return;
        }


        const history = await response.json();


        if (!Array.isArray(history)) {
            return;
        }


        for (const item of history) {

            // We only add administrator messages here.
            if (item.type !== "admin") {
                continue;
            }


            const signature =
                String(item.type) +
                "|" +
                String(item.message) +
                "|" +
                String(item.created_at);


            // Already displayed?
            if (displayedAdminMessages.has(signature)) {
                continue;
            }


            displayedAdminMessages.add(signature);


            // Create admin message
            const admin = document.createElement("div");

            admin.className = "admin-message";


            const title = document.createElement("strong");

            title.textContent = "👨‍💼 Admin";


            const message = document.createElement("div");

            message.style.marginTop = "6px";

            // textContent prevents HTML/code from being executed
            message.textContent = item.message;


            const time = document.createElement("small");

            time.style.display = "block";

            time.style.marginTop = "6px";

            time.textContent =
                item.created_at || "";


            admin.appendChild(title);

            admin.appendChild(message);

            admin.appendChild(time);


            chatBox.appendChild(admin);


            // Make the new admin reply visible
            scrollBottom();

        }


    } catch (error) {

        console.log(
            "ADMIN MESSAGE CHECK ERROR:",
            error
        );

    }

}


// =====================================================
// LOAD EXISTING ADMIN REPLIES WITHOUT DUPLICATING THEM
// =====================================================

async function initializeAdminMessages() {

    if (!chatBox) return;

    try {

        const response = await fetch(
            "/history?_=" + Date.now(),
            {
                cache: "no-store"
            }
        );


        if (!response.ok) {
            return;
        }


        const history = await response.json();


        if (!Array.isArray(history)) {
            return;
        }


        // Existing admin messages are probably already
        // visible after a page reload. Therefore we only
        // register their signatures here.
        for (const item of history) {

            if (item.type !== "admin") {
                continue;
            }


            const signature =
                String(item.type) +
                "|" +
                String(item.message) +
                "|" +
                String(item.created_at);


            displayedAdminMessages.add(signature);

        }


    } catch (error) {

        console.log(
            "ADMIN INITIALIZATION ERROR:",
            error
        );

    }

}


// =====================================================
// ORDER + NOTIFICATION REFRESH
// =====================================================

async function refreshPage() {

    try {

        const response = await fetch(
            "/?_=" + Date.now(),
            {
                cache: "no-store"
            }
        );


        const html = await response.text();


        const parser = new DOMParser();

        const doc =
            parser.parseFromString(
                html,
                "text/html"
            );


        const newOrders =
            doc.getElementById("orders");


        const newNotifications =
            doc.getElementById("notifications");


        const orders =
            document.getElementById("orders");


        const notifications =
            document.getElementById(
                "notifications"
            );


        if (newOrders && orders) {

            orders.innerHTML =
                newOrders.innerHTML;

        }


        if (
            newNotifications &&
            notifications
        ) {

            notifications.innerHTML =
                newNotifications.innerHTML;

        }


    } catch (e) {

        console.log(
            "PAGE REFRESH ERROR:",
            e
        );

    }

}


// =====================================================
// START LIVE ADMIN CHAT
// =====================================================

initializeAdminMessages()
    .then(function () {

        // Check for new administrator replies
        // every 3 seconds.
        setInterval(
            checkAdminReplies,
            3000
        );

    });


// =====================================================
// REFRESH ORDERS + NOTIFICATIONS
// =====================================================

// Keep your existing 10-second refresh.
setInterval(
    refreshPage,
    10000
);
