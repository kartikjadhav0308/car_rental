(function () {
  var toggle = document.getElementById("navToggle");
  var nav = document.getElementById("mainNav");
  if (toggle && nav) {
    toggle.addEventListener("click", function () {
      nav.classList.toggle("open");
    });
    document.addEventListener("click", function (e) {
      if (!nav.contains(e.target) && e.target !== toggle) {
        nav.classList.remove("open");
      }
    });
  }

  var dot = document.getElementById("healthDot");
  if (!dot) return;

  fetch("/api/health")
    .then(function (r) {
      return r.json();
    })
    .then(function (data) {
      dot.classList.remove("ok", "bad");
      if (data && data.ok) {
        dot.classList.add("ok");
        dot.title = "DB OK · " + (data.database || "") + " · " + (data.server_time || "");
      } else {
        dot.classList.add("bad");
        dot.title = (data && data.error) || "Health check failed";
      }
    })
    .catch(function () {
      dot.classList.add("bad");
      dot.title = "Could not reach /api/health";
    });
})();
