document.addEventListener("DOMContentLoaded", function () {
  const toggle = document.getElementById("chatbot-toggle");
  const win = document.getElementById("chatbot-window");
  const close = document.getElementById("chatbot-close");
  const send = document.getElementById("chatbot-send");
  const input = document.getElementById("chatbot-input");
  const messages = document.getElementById("chatbot-messages");

  if (!toggle || !win) return;

  toggle.addEventListener("click", () => win.classList.toggle("hidden"));
  close.addEventListener("click", () => win.classList.add("hidden"));

  function addMessage(text, sender) {
    const msg = document.createElement("div");
    msg.className = "chatbot-message " + sender;
    msg.textContent = text;
    messages.appendChild(msg);
    messages.scrollTop = messages.scrollHeight;
  }

  async function sendMessage() {
    const text = input.value.trim();
    if (!text) return;

    addMessage(text, "user");
    input.value = "";

    // Show loading state
    const loadingMsg = document.createElement("div");
    loadingMsg.className = "chatbot-message bot";
    loadingMsg.textContent = "Typing...";
    messages.appendChild(loadingMsg);
    messages.scrollTop = messages.scrollHeight;

    try {
      const response = await fetch("/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: text }),
      });

      const data = await response.json();
      messages.removeChild(loadingMsg);

      if (response.ok) {
        addMessage(data.reply, "bot");
      } else {
        addMessage(data.reply || "An error occurred.", "bot");
      }
    } catch (err) {
      messages.removeChild(loadingMsg);
      addMessage("Unable to connect to server.", "bot");
    }
  }

  send.addEventListener("click", sendMessage);
  input.addEventListener("keydown", (e) => {
    if (e.key === "Enter") sendMessage();
  });
});