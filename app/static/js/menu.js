function changeQty(btn, delta) {
  const input = btn.parentElement.querySelector(".qty-input");
  let val = parseInt(input.value || "0", 10) + delta;
  if (val < 0) val = 0;
  input.value = val;
  updateTotal();
}

function updateTotal() {
  const inputs = document.querySelectorAll(".qty-input");
  let total = 0;
  inputs.forEach((input) => {
    const qty = parseInt(input.value || "0", 10);
    const price = parseFloat(input.dataset.price || "0");
    total += qty * price;
  });
  const display = document.getElementById("total-display");
  if (display) display.textContent = "RM " + total.toFixed(2);
}

function toggleMeeting() {
  const checked = document.getElementById("is_meeting").checked;
  document.getElementById("meeting-fields").hidden = !checked;
  document.getElementById("order_type").value = checked ? "MeetingRoom" : "Counter";
}

document.addEventListener("DOMContentLoaded", updateTotal);
