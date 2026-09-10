// UC5: Receive Order Notification - polls the server every 3s to simulate a push notification.
let lastStatus = null;

function paintStatus(status) {
  document.querySelectorAll(".status-step").forEach((el) => {
    el.classList.toggle("active", el.dataset.status === status);
  });
}

async function poll() {
  try {
    const res = await fetch(`/api/order/${ORDER_ID}`);
    if (!res.ok) return;
    const data = await res.json();
    paintStatus(data.status);

    if (data.status !== lastStatus) {
      lastStatus = data.status;
      if (data.status === "Ready" && data.notification) {
        const banner = document.getElementById("notif-banner");
        banner.textContent = "🔔 " + data.notification;
        banner.hidden = false;
      }
    }
  } catch (e) {
    // network hiccup - ignore, will retry on next tick
  }
}

poll();
setInterval(poll, 3000);
