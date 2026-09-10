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

  function sendMessage() {
    const text = input.value.trim();
    if (!text) return;
    addMessage(text, "user");
    input.value = "";
    // Placeholder bot reply - replace with a real backend call if needed
    setTimeout(() => addMessage("Thanks for your message! Our team will get back to you soon.", "bot"), 400);
  }

  send.addEventListener("click", sendMessage);
  input.addEventListener("keydown", (e) => {
    if (e.key === "Enter") sendMessage();
  });
});
