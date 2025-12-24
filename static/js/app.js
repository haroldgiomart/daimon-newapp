function openVideo(url, title) {
  document.getElementById("videoFrame").src = url + "?autoplay=1";
  document.getElementById("videoTitle").innerText = title;
  document.getElementById("videoModal").classList.add("active");
}

function closeVideo() {
  document.getElementById("videoFrame").src = "";
  document.getElementById("videoModal").classList.remove("active");
}