function openVideo(url, title, description = "") {
  const modal = document.getElementById("videoModal");
  const frame = document.getElementById("videoFrame");
  const titleEl = document.getElementById("videoTitle");
  const descEl = document.getElementById("videoDescription");

  if (!modal || !frame) {
    console.error("❌ Video modal not found in DOM");
    return;
  }

  frame.src = url;

  if (titleEl) titleEl.innerText = title;
  if (descEl) descEl.innerText = description;

  modal.classList.add("active");
}

function closeVideo() {
  const modal = document.getElementById("videoModal");
  const frame = document.getElementById("videoFrame");

  if (frame) frame.src = "";
  if (modal) modal.classList.remove("active");
}