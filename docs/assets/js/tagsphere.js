/* tagsphere.js - dependency-free rotating 3D sphere tag cloud.
   No external requests and no libraries, so nothing here can break if a
   remote source goes down. Math ported from the tagoSphere jQuery plugin.

   Usage: window.startTagSphere(containerEl, { radius, speed, idle, fontMultiplier })
   Reads .tag elements inside the container and animates them on a sphere.
   Returns { stop }. */
(function (global) {
  "use strict";

  function startTagSphere(container, opts) {
    opts = opts || {};
    var items = Array.prototype.slice.call(container.querySelectorAll(".tag"));
    var n = items.length;
    if (!n) return { stop: function () {} };

    var speed = opts.speed != null ? opts.speed : 3;
    var idle = opts.idle != null ? opts.idle : 0.5;
    var fontMultiplier = opts.fontMultiplier != null ? opts.fontMultiplier : 12;

    var initHalfW = container.clientWidth / 2 || 160;
    var initHalfH = container.clientHeight / 2 || 160;
    var radius = opts.radius != null
      ? opts.radius
      : Math.max(80, Math.min(initHalfW, initHalfH) - 28);
    var diameter = radius * 2;
    var dtr = Math.PI / 180;

    var mouseX = 0, mouseY = 0, mouseOver = false, paused = false;

    // Distribute the tags evenly over the sphere (Fibonacci spiral).
    var data = items.map(function (el, i) {
      var phi = Math.acos(-1 + (2 * (i + 1) - 1) / n);
      var theta = Math.sqrt(n * Math.PI) * phi;
      // Freeze rotation while a tag is hovered or focused so it stays clickable.
      el.addEventListener("mouseenter", function () { paused = true; });
      el.addEventListener("mouseleave", function () { paused = false; });
      el.addEventListener("focus", function () { paused = true; });
      el.addEventListener("blur", function () { paused = false; });
      return {
        el: el,
        cx: radius * Math.cos(theta) * Math.sin(phi),
        cy: radius * Math.sin(theta) * Math.sin(phi),
        cz: radius * Math.cos(phi)
      };
    });

    function onMove(e) {
      var r = container.getBoundingClientRect();
      mouseX = e.clientX - r.left;
      mouseY = e.clientY - r.top;
    }
    function onEnter() { mouseOver = true; }
    function onLeave() { mouseOver = false; }
    container.addEventListener("mousemove", onMove);
    container.addEventListener("mouseenter", onEnter);
    container.addEventListener("mouseleave", onLeave);

    var rafId = null;

    function frame() {
      var halfW = container.clientWidth / 2 || initHalfW;
      var halfH = container.clientHeight / 2 || initHalfH;

      var fx, fy;
      if (paused) {
        fx = 0; fy = 0;
      } else if (mouseOver) {
        fy = speed - (speed / halfH) * mouseY;
        fx = (speed / halfW) * mouseX - speed;
      } else {
        fx = idle;
        fy = idle * 0.5;
      }

      var sinY = Math.sin(fy * dtr), cosY = Math.cos(fy * dtr);
      var sinX = Math.sin(fx * dtr), cosX = Math.cos(fx * dtr);

      for (var i = 0; i < data.length; i++) {
        var t = data[i];
        var rx1 = t.cx;
        var ry1 = t.cy * cosY + t.cz * (-sinY);
        var rz1 = t.cy * sinY + t.cz * cosY;
        t.cx = rx1 * cosX + rz1 * sinX;
        t.cy = ry1;
        t.cz = rx1 * (-sinX) + rz1 * cosX;

        var per = diameter / (diameter + t.cz);
        var x = t.cx * per + halfW;
        var y = t.cy * per + halfH;

        var size = fontMultiplier * per;
        if (size < 11) size = 11;
        if (size > 26) size = 26;
        var alpha = per / 2;
        if (alpha < 0.35) alpha = 0.35;
        if (alpha > 1) alpha = 1;

        var s = t.el.style;
        s.left = x + "px";
        s.top = y + "px";
        s.fontSize = size.toFixed(1) + "px";
        s.opacity = alpha.toFixed(2);
        s.zIndex = Math.round(per * 100);
      }
      rafId = global.requestAnimationFrame(frame);
    }

    rafId = global.requestAnimationFrame(frame);

    return {
      stop: function () {
        if (rafId) global.cancelAnimationFrame(rafId);
        container.removeEventListener("mousemove", onMove);
        container.removeEventListener("mouseenter", onEnter);
        container.removeEventListener("mouseleave", onLeave);
      }
    };
  }

  global.startTagSphere = startTagSphere;
})(window);
