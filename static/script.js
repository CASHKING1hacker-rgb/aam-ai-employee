const form = document.getElementById("chat-form");
const input = document.getElementById("message");
const chatBox = document.getElementById("chat-box");

function scrollBottom() {
    chatBox.scrollTop = chatBox.scrollHeight;
}

scrollBottom();

form.addEventListener("submit", async function (e) {

    e.preventDefault();

    const message = input.value.trim();

    if (message === "") return;

    // User message
    const user = document.createElement("div");
    user.className = "user-message";
    user.innerHTML = "👤 " + message;
    chatBox.appendChild(user);

    input.value = "";
    scrollBottom();

    // Typing indicator
    const typing = document.createElement("div");
    typing.className = "ai-message";
    typing.id = "typing";
    typing.innerHTML = "🤖 AI is typing...";
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

        typing.remove();

        const ai = document.createElement("div");
        ai.className = "ai-message";
        ai.innerHTML = "🤖 " + data.reply.replace(/\n/g, "<br>");
        chatBox.appendChild(ai);

        scrollBottom();

    } catch (err) {

        typing.innerHTML = "❌ Failed to contact server.";

        scrollBottom();

    }

});

async function refreshPage() {

    try {

        const response = await fetch("/");

        const html = await response.text();

        const parser = new DOMParser();
        const doc = parser.parseFromString(html, "text/html");

        const newOrders = doc.getElementById("orders");
        const newNotifications = doc.getElementById("notifications");

        if (newOrders) {
            document.getElementById("orders").innerHTML = newOrders.innerHTML;
        }

        if (newNotifications) {
            document.getElementById("notifications").innerHTML = newNotifications.innerHTML;
        }

    } catch (e) {
        console.log(e);
    }

}

setInterval(refreshPage, 10000);