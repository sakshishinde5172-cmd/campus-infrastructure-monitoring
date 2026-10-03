const API = "";

async function checkAdmin() {
  try {
    const response = await fetch(`${API}/api/me`);
    if (!response.ok) return;
    const data = await response.json();
    if (data.is_admin) {
      document.querySelectorAll(".admin-link, .admin-quick-btn, .admin-only").forEach(el => el.classList.remove("hidden"));
    }
  } catch (err) {
    console.error("Failed to check admin status:", err);
  }
}

async function logout() {
  try {
    await fetch(`${API}/api/logout`, { method: "POST" });
  } catch (err) {
    console.error("Logout request failed:", err);
  }
  window.location.href = "/login";
}

function showToast(message, isError = false) {
  const toast = document.getElementById("toast");
  if (!toast) return;
  toast.textContent = message;
  toast.className = "toast show" + (isError ? " error" : "");
  setTimeout(() => { toast.className = "toast"; }, 3000);
}

function escapeHtml(str) {
  const div = document.createElement("div");
  div.textContent = str ?? "";
  return div.innerHTML;
}

function timeAgo(dateStr) {
  if (!dateStr) return "";
  const diffMs = Date.now() - new Date(dateStr).getTime();
  const diffMin = Math.floor(diffMs / 60000);
  if (diffMin < 1) return "just now";
  if (diffMin < 60) return diffMin + " min ago";
  const diffHr = Math.floor(diffMin / 60);
  if (diffHr < 24) return diffHr + " hr ago";
  const diffDay = Math.floor(diffHr / 24);
  return diffDay + (diffDay === 1 ? " day ago" : " days ago");
}

function isResolvedStatus(status) {
  return /resolved|closed|done/i.test(status || "");
}

function statusColor(status) {
  const s = (status || "").toLowerCase();
  if (isResolvedStatus(s)) return "var(--green)";
  if (s.includes("progress")) return "var(--teal)";
  if (s.includes("pending")) return "var(--amber)";
  return "var(--muted)";
}

function countUp(el, target, duration = 900) {
  if (!el) return;
  const start = performance.now();
  function step(now) {
    const progress = Math.min((now - start) / duration, 1);
    el.textContent = Math.floor(progress * target);
    if (progress < 1) requestAnimationFrame(step);
    else el.textContent = target;
  }
  requestAnimationFrame(step);
}

function openLightbox(url) {
  const img = document.getElementById("lightboxImg");
  const box = document.getElementById("lightbox");
  if (!img || !box) return;
  img.src = url;
  box.classList.add("show");
}

function closeLightbox() {
  const box = document.getElementById("lightbox");
  if (box) box.classList.remove("show");
}

(function highlightActiveNav() {
  document.addEventListener("DOMContentLoaded", () => {
    const page = document.body.dataset.page;
    if (!page) return;
    document.querySelectorAll(`.topnav a[data-page="${page}"], .mobilenav a[data-page="${page}"]`)
      .forEach(el => el.classList.add("active"));
  });
})();

checkAdmin();