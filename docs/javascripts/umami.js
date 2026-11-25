// Umami pageviews for Material's instant navigation.
// The script tag has data-auto-track="false", so every pageview comes from here.
document$.subscribe(function () {
  if (window.umami) {
    window.umami.track()
  }
})
