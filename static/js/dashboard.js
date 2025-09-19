const slotsTable = document.querySelector("#slotsTable tbody");
const bookingsTable = document.querySelector("#bookingsTable tbody");
const lastUpdated = document.getElementById("lastUpdated");

//
// ---------- RENDERING ----------
//
function renderSlots(slots) {
  slotsTable.innerHTML = "";
  for (const [date, times] of Object.entries(slots)) {
    times.forEach((time) => {
      const tr = document.createElement("tr");
      tr.innerHTML = `
        <td>${date}</td>
        <td>${time}</td>
        <td><button onclick="deleteSlot('${date}','${time}')">❌ Delete</button></td>
      `;
      slotsTable.appendChild(tr);
    });
  }
}

function renderBookings(bookings) {
  bookingsTable.innerHTML = "";
  bookings.forEach((b) => {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td>${b.customer_name}</td>
      <td>${b.service}</td>
      <td>${b.date}</td>
      <td>${b.time}</td>
      <td class="status-${b.status}">${b.status}</td>
      <td>
        ${b.status !== "cancelled" ? `<button onclick="cancelBooking('${b.id}')">❌ Cancel</button>` : ""}
        ${b.status === "pending" ? `<button onclick="markPaid('${b.id}')">✅ Mark Paid</button>` : ""}
      </td>
    `;
    bookingsTable.appendChild(tr);
  });
}

//
// ---------- SLOT FORM ----------
//
document.getElementById("slotForm").addEventListener("submit", async (e) => {
  e.preventDefault();
  const date = document.getElementById("slotDate").value;
  let time = document.getElementById("slotTime").value;

  // Normalize to HH:MM
  if (time && time.length >= 5) {
    time = time.slice(0, 5);
  }

  const res = await fetch("/api/slots", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ date, time }),
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    alert("⚠️ Could not add slot: " + (err.detail || res.statusText));
  } else {
    document.getElementById("slotForm").reset();
  }
});

//
// ---------- ACTIONS ----------
//
async function deleteSlot(date, time) {
  const res = await fetch(`/api/slots?date=${date}&time=${time}`, {
    method: "DELETE",
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    alert("⚠️ Could not delete slot: " + (err.detail || res.statusText));
  }
}

async function cancelBooking(id) {
  const res = await fetch(`/api/bookings/${id}/cancel`, { method: "POST" });
  if (!res.ok) {
    alert("⚠️ Could not cancel booking");
  }
}

async function markPaid(id) {
  const res = await fetch(`/api/bookings/${id}/paid`, { method: "POST" });
  if (!res.ok) {
    alert("⚠️ Could not mark booking paid");
  }
}

//
// ---------- TIMESTAMP ----------
//
function updateTimestamp() {
  lastUpdated.innerText = "Last updated: " + new Date().toLocaleTimeString();
}

//
// ---------- WEBSOCKET ----------
//
const protocol = window.location.protocol === "https:" ? "wss" : "ws";
const ws = new WebSocket(`${protocol}://${window.location.host}/ws/dashboard`);
ws.onmessage = (event) => {
  console.log("📩 WS message:", event.data);  // 👈 log raw message
  const data = JSON.parse(event.data);
  if (data.type === "ping") return;

  if (data.slots) renderSlots(data.slots);
  if (data.bookings) renderBookings(data.bookings);
  updateTimestamp();
};



ws.onopen = () => console.log("✅ Connected to live updates");
ws.onclose = () => console.log("❌ Disconnected from live updates");

//
// ---------- INITIAL LOAD ----------
//
async function initialLoad() {
  try {
    const slotsRes = await fetch("/api/slots?ts=" + Date.now(), {
      cache: "no-store",
    });
    renderSlots(await slotsRes.json());

    const bookingsRes = await fetch("/api/bookings?ts=" + Date.now(), {
      cache: "no-store",
    });
    renderBookings(await bookingsRes.json());

    updateTimestamp();
  } catch (err) {
    console.error("⚠️ Failed to load initial data", err);
  }
}
initialLoad();
