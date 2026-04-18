(function () {
  "use strict";

  /* =====================================================
     LOADER (Lissajous Drift)
     ===================================================== */
  var loaderOverlay = document.getElementById("loader-overlay");
  var appShell = document.getElementById("app-shell");

  if (loaderOverlay && appShell) {
    const SVG_NS = 'http://www.w3.org/2000/svg';
    const config = {
      name: "Lissajous Drift",
      tag: "x = sin(at), y = sin(bt)",
      rotate: false,
      particleCount: 140,
      trailSpan: 0.12,
      durationMs: 4900,
      rotationDurationMs: 36000,
      pulseDurationMs: 5400,
      strokeWidth: 2.9,
      lissajousAmp: 24,
      lissajousAmpBoost: 6,
      lissajousAX: 3,
      lissajousBY: 4,
      lissajousPhase: 1.57,
      lissajousYScale: 0.92,
      point(progress, detailScale, config) {
        const t = progress * Math.PI * 2;
        const amp = config.lissajousAmp + detailScale * config.lissajousAmpBoost;
        return {
          x: 50 + Math.sin(Math.round(config.lissajousAX) * t + config.lissajousPhase) * amp,
          y: 50 + Math.sin(Math.round(config.lissajousBY) * t) * (amp * config.lissajousYScale),
        };
      },
    };

    const group = document.querySelector('#loader-group');
    const path = document.querySelector('#loader-path');

    if (group && path) {
      path.setAttribute('stroke-width', String(config.strokeWidth));
      const particles = Array.from({ length: config.particleCount }, () => {
        const circle = document.createElementNS(SVG_NS, 'circle');
        circle.setAttribute('fill', 'currentColor');
        group.appendChild(circle);
        return circle;
      });
      function normalizeProgress(progress) { return ((progress % 1) + 1) % 1; }
      function getDetailScale(time) {
        const pulseProgress = (time % config.pulseDurationMs) / config.pulseDurationMs;
        const pulseAngle = pulseProgress * Math.PI * 2;
        return 0.52 + ((Math.sin(pulseAngle + 0.55) + 1) / 2) * 0.48;
      }
      function getRotation(time) {
        if (!config.rotate) return 0;
        return -((time % config.rotationDurationMs) / config.rotationDurationMs) * 360;
      }
      function buildPath(detailScale, steps = 480) {
        return Array.from({ length: steps + 1 }, (_, index) => {
          const point = config.point(index / steps, detailScale, config);
          return `${index === 0 ? 'M' : 'L'} ${point.x.toFixed(2)} ${point.y.toFixed(2)}`;
        }).join(' ');
      }
      function getParticle(index, progress, detailScale) {
        const tailOffset = index / (config.particleCount - 1);
        const point = config.point(normalizeProgress(progress - tailOffset * config.trailSpan), detailScale, config);
        const fade = Math.pow(1 - tailOffset, 0.56);
        return { x: point.x, y: point.y, radius: 0.9 + fade * 2.7, opacity: 0.04 + fade * 0.96 };
      }
      const startedAt = performance.now();
      let animFrameId;
      function render(now) {
        const time = now - startedAt;
        const progress = (time % config.durationMs) / config.durationMs;
        const detailScale = getDetailScale(time);
        group.setAttribute('transform', `rotate(${getRotation(time)} 50 50)`);
        path.setAttribute('d', buildPath(detailScale));
        particles.forEach((node, index) => {
          const particle = getParticle(index, progress, detailScale);
          node.setAttribute('cx', particle.x.toFixed(2));
          node.setAttribute('cy', particle.y.toFixed(2));
          node.setAttribute('r', particle.radius.toFixed(2));
          node.setAttribute('opacity', particle.opacity.toFixed(3));
        });
        animFrameId = requestAnimationFrame(render);
      }
      animFrameId = requestAnimationFrame(render);

      // Stop rendering after exactly 5000ms
      setTimeout(function () {
        cancelAnimationFrame(animFrameId);
        loaderOverlay.classList.add("fade-out");
        appShell.classList.add("fade-in");

        setTimeout(() => loaderOverlay.remove(), 600);
      }, 1000);
    }
  }  /* =====================================================
     SIDEBAR TOGGLE (mobile)
     ===================================================== */
  var toggle = document.getElementById("navToggle");
  var sidebar = document.getElementById("sidebar");
  var overlay = document.getElementById("sidebarOverlay");

  function openSidebar() {
    if (sidebar) sidebar.classList.add("open");
    if (overlay) overlay.classList.add("show");
  }

  function closeSidebar() {
    if (sidebar) sidebar.classList.remove("open");
    if (overlay) overlay.classList.remove("show");
  }

  if (toggle) toggle.addEventListener("click", function () {
    sidebar && sidebar.classList.contains("open") ? closeSidebar() : openSidebar();
  });

  if (overlay) overlay.addEventListener("click", closeSidebar);

  /* Close sidebar on Escape */
  document.addEventListener("keydown", function (e) {
    if (e.key === "Escape") closeSidebar();
  });

  /* =====================================================
     HEALTH CHECK DOT
     ===================================================== */
  var dots = [
    document.getElementById("healthDot"),
    document.getElementById("healthDotTop")
  ].filter(Boolean);

  if (dots.length) {
    fetch("/api/health")
      .then(function (r) { return r.json(); })
      .then(function (data) {
        dots.forEach(function (dot) {
          dot.classList.remove("ok", "bad");
          if (data && data.ok) {
            dot.classList.add("ok");
            dot.title = "DB OK · " + (data.database || "") + " · " + (data.server_time || "");
          } else {
            dot.classList.add("bad");
            dot.title = (data && data.error) || "Health check failed";
          }
        });
      })
      .catch(function () {
        dots.forEach(function (dot) {
          dot.classList.add("bad");
          dot.title = "Could not reach /api/health";
        });
      });
  }

  /* =====================================================
     ANIME.JS — Controlled page-load animations
     ===================================================== */
  if (typeof anime === "undefined") return;

  /* 1. Page-header fade-in */
  var fadeEls = document.querySelectorAll(".anim-fade-in");
  if (fadeEls.length) {
    anime({
      targets: fadeEls,
      opacity: [0, 1],
      translateY: [12, 0],
      duration: 350,
      easing: "easeOutQuad"
    });
  }

  /* 2. Card staggered appearance */
  var cards = document.querySelectorAll(".anim-card");
  if (cards.length) {
    anime({
      targets: cards,
      opacity: [0, 1],
      translateY: [16, 0],
      duration: 400,
      easing: "easeOutQuad",
      delay: anime.stagger(80, { start: 120 })
    });
  }

  /* 3. Flash messages — subtle slide-in */
  var flashes = document.querySelectorAll(".flash");
  if (flashes.length) {
    anime({
      targets: flashes,
      opacity: [0, 1],
      translateX: [-12, 0],
      duration: 300,
      easing: "easeOutQuad",
      delay: anime.stagger(60)
    });
  }

  /* 4. Table rows — sequential fade */
  var rows = document.querySelectorAll(".data tbody tr");
  if (rows.length && rows.length <= 50) {
    anime({
      targets: rows,
      opacity: [0, 1],
      duration: 250,
      easing: "easeOutQuad",
      delay: anime.stagger(30, { start: 300 })
    });
  }

})();
