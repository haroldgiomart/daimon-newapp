// ==========================================
// VIDEO MODAL
// ==========================================

function openVideo(url, title, description = "") {
  const modal = document.getElementById("videoModal");
  const frame = document.getElementById("videoFrame");
  const titleEl = document.getElementById("videoTitle");
  const descEl = document.getElementById("videoDescription");

  if (!modal || !frame) {
    console.error("Video modal not found in DOM");
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


// ==========================================
// INTENT SCROLL ACTIVE EFFECT
// ==========================================

document.addEventListener("DOMContentLoaded", () => {

  const track = document.querySelector(".intent-track");
  const items = document.querySelectorAll(".intent-item");

  if (track && items.length > 0) {

    track.addEventListener("scroll", () => {

      let closestItem = null;
      let closestDistance = Infinity;

      const trackCenter =
        track.scrollLeft + track.offsetWidth / 2;

      items.forEach(item => {

        const itemCenter =
          item.offsetLeft + item.offsetWidth / 2;

        const distance =
          Math.abs(trackCenter - itemCenter);

        if (distance < closestDistance) {
          closestDistance = distance;
          closestItem = item;
        }
      });

      items.forEach(item =>
        item.classList.remove("is-active")
      );

      if (closestItem) {
        closestItem.classList.add("is-active");
      }

    });
  }
});


// ==========================================
// INTENT CARD HOVER
// ==========================================

document.addEventListener("DOMContentLoaded", () => {

  const cards = document.querySelectorAll(".intent-card");

  if (!cards.length) return;

  cards.forEach(card => {

    card.addEventListener("mouseenter", () => {
      setActive(card);
    });

    card.addEventListener("focus", () => {
      setActive(card);
    });

  });

  function setActive(activeCard) {
    cards.forEach(c => c.classList.remove("active"));
    activeCard.classList.add("active");
  }

});


// ==========================================
// FAVORITE BUTTON TOGGLE (VISUAL)
// ==========================================

document.addEventListener("DOMContentLoaded", () => {

  const favoriteButtons =
    document.querySelectorAll(".exercise-favorite");

  if (!favoriteButtons.length) return;

  favoriteButtons.forEach(btn => {

    btn.addEventListener("click", e => {
      e.stopPropagation();
      btn.classList.toggle("active");
    });

  });

});
// ==========================================
// USER DROPDOWN (Animated)
// ==========================================

document.addEventListener("DOMContentLoaded", function () {
  const avatar = document.getElementById("userAvatar");
  const dropdown = document.getElementById("userDropdown");

  if (avatar && dropdown) {
    avatar.addEventListener("click", function (e) {
      e.stopPropagation();
      dropdown.classList.toggle("show");
    });

    document.addEventListener("click", function (e) {
      if (!dropdown.contains(e.target)) {
        dropdown.classList.remove("show");
      }
    });
  }
});