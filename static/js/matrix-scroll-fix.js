// =========================================
// FIX HORIZONTAL SCROLL ON iOS SAFARI
// =========================================

document.addEventListener("DOMContentLoaded", () => {
  const rows = document.querySelectorAll(".matrix-row");

  rows.forEach(row => {
    row.addEventListener("touchstart", () => {
      document.body.style.overflowY = "hidden";
    }, { passive: true });

    row.addEventListener("touchend", () => {
      document.body.style.overflowY = "";
    });

    row.addEventListener("touchcancel", () => {
      document.body.style.overflowY = "";
    });
  });
});