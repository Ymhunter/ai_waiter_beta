const chat = document.getElementById("chat");
const input = document.getElementById("userInput");
const suggestions = document.getElementById("suggestions");
const conversation = [];

function scrollToBottom() {
  chat.scrollTop = chat.scrollHeight;
}

function appendMessage(text, sender = "bot") {
  const div = document.createElement("div");
  div.className = "msg " + sender;
  div.textContent = text;
  chat.appendChild(div);
  scrollToBottom();

  if (sender === "bot") conversation.push({ role: "assistant", content: text });
  if (sender === "user") conversation.push({ role: "user", content: text });
  if (conversation.length > 16) conversation.shift();
}

function quickAsk(text) {
  suggestions.style.display = "none";
  input.value = text;
  sendMessage();
}

async function sendMessage() {
  const text = input.value.trim();
  if (!text) return;
  appendMessage(text, "user");
  input.value = "";
  suggestions.style.display = "none";

  try {
    // intent check
    const intentRes = await fetch("/intent", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message: text }),
    });
    const intentData = await intentRes.json();
    if (intentData.intent === "book") {
      showCalendar();
      return;
    }
  } catch (err) {
    console.warn("Intent check failed", err);
  }

  // loading indicator
  const loading = document.createElement("span");
  loading.className = "loading";
  loading.innerText = "⏳...";
  chat.appendChild(loading);
  scrollToBottom();

  try {
    const res = await fetch("/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message: text, history: conversation }),
    });
    const data = await res.json();
    loading.remove();
    appendMessage(data.reply, "bot");

    if (data.status === "reserved") {
      appendMessage("✅ Your booking is confirmed! Check your email for details.", "bot");
    }
  } catch (err) {
    loading.remove();
    appendMessage("⚠️ Error: " + err.message, "bot");
  }
}

async function showCalendar() {
  try {
    const res = await fetch("/api/slots");
    const slots = await res.json();
    const cal = buildCalendar(slots);
    chat.appendChild(cal);
    scrollToBottom();
  } catch (err) {
    appendMessage("⚠️ Error loading slots", "bot");
  }
}

function buildCalendar(slots) {
  const cal = document.createElement("div");
  cal.className = "calendar";
  let monthOffset = 0;

  function render(offset) {
    cal.innerHTML = "";
    monthOffset = offset;
    const today = new Date();
    const displayDate = new Date(today.getFullYear(), today.getMonth() + monthOffset, 1);
    const year = displayDate.getFullYear();
    const month = displayDate.getMonth();
    const monthStart = new Date(year, month, 1);
    const monthEnd = new Date(year, month + 1, 0);
    const firstDay = monthStart.getDay();
    const daysInMonth = monthEnd.getDate();

    const header = document.createElement("header");
    const prevBtn = document.createElement("button");
    prevBtn.textContent = "<";
    prevBtn.onclick = () => render(monthOffset - 1);
    const nextBtn = document.createElement("button");
    nextBtn.textContent = ">";
    nextBtn.onclick = () => render(monthOffset + 1);
    const title = document.createElement("span");
    title.textContent = displayDate.toLocaleString("default", { month: "long", year: "numeric" });
    header.appendChild(prevBtn);
    header.appendChild(title);
    header.appendChild(nextBtn);
    cal.appendChild(header);

    const table = document.createElement("table");
    const days = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];
    const thead = document.createElement("thead");
    const headRow = document.createElement("tr");
    days.forEach((d) => {
      const th = document.createElement("th");
      th.textContent = d;
      headRow.appendChild(th);
    });
    thead.appendChild(headRow);
    table.appendChild(thead);

    const tbody = document.createElement("tbody");
    let row = document.createElement("tr");
    for (let i = 0; i < firstDay; i++) row.appendChild(document.createElement("td"));

    for (let d = 1; d <= daysInMonth; d++) {
      const dateStr = year + "-" + String(month + 1).padStart(2, "0") + "-" + String(d).padStart(2, "0");
      const td = document.createElement("td");
      td.textContent = d;

      if (slots[dateStr]) {
        td.classList.add("has-slot");
        td.onclick = () => showTimes(dateStr, slots[dateStr], cal);
      }
      if (
        d === new Date().getDate() &&
        month === new Date().getMonth() &&
        year === new Date().getFullYear()
      ) {
        td.classList.add("today");
      }

      row.appendChild(td);
      if ((firstDay + d) % 7 === 0 || d === daysInMonth) {
        tbody.appendChild(row);
        row = document.createElement("tr");
      }
    }
    table.appendChild(tbody);
    cal.appendChild(table);
  }

  render(0);
  return cal;
}

function showTimes(date, times, cal) {
  let timeBox = cal.querySelector(".times");
  if (timeBox) timeBox.remove();
  timeBox = document.createElement("div");
  timeBox.className = "times";
  times.forEach((t) => {
    if (t.length === 8) t = t.slice(0, 5);
    const btn = document.createElement("button");
    btn.className = "time-btn";
    btn.textContent = t;
    btn.onclick = () => sendBooking(date, t);
    timeBox.appendChild(btn);
  });
  cal.appendChild(timeBox);
}

async function sendBooking(date, time) {
  if (time.length === 8) time = time.slice(0, 5);
  appendMessage(`I want ${date} at ${time}`, "user");
  const loading = document.createElement("span");
  loading.className = "loading";
  loading.innerText = "⏳...";
  chat.appendChild(loading);
  scrollToBottom();

  try {
    const res = await fetch("/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message: `I want ${date} at ${time}`, history: conversation }),
    });
    const data = await res.json();
    loading.remove();
    appendMessage(data.reply, "bot");
    if (data.status === "reserved") {
      appendMessage("✅ Your booking is confirmed! Check your email for details.", "bot");
    }
  } catch (err) {
    loading.remove();
    appendMessage("⚠️ Error: " + err.message, "bot");
  }
}

// ------------------------------
// WebSocket real-time updates
// ------------------------------
const protocol = window.location.protocol === "https:" ? "wss" : "ws";
const ws = new WebSocket(`${protocol}://${window.location.host}/ws`);

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  if (data.slots) {
    console.log("🔄 Slots updated", data.slots);
  }
  if (data.bookings) {
    console.log("🔄 Bookings updated", data.bookings);
  }
};

input.addEventListener("keypress", (e) => {
  if (e.key === "Enter") sendMessage();
});
