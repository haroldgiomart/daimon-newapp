self.addEventListener("install", e => {
  e.waitUntil(
    caches.open("daimon-v1").then(cache =>
      cache.addAll(["/", "/static/css/app.css"])
    )
  )
})