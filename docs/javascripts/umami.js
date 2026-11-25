// Umami pageviews for Material's instant navigation.
// The Umami tag is deferred, so wait for load — otherwise window.umami
// isn't defined yet and the initial pageview is dropped.
let last = null

function track() {
  if (!window.umami) return
  const url = location.pathname + location.search
  if (url === last) return
  last = url
  window.umami.track()
}

window.addEventListener("load", function () {
  track()
  document$.subscribe(track)
})
