/* La Vita è Bella Montessori — light interactions only (no framework). */
(function () {
  "use strict";

  // Mobile nav toggle
  var toggle = document.querySelector(".nav-toggle");
  var nav = document.getElementById("primary-nav");
  if (toggle && nav) {
    toggle.addEventListener("click", function () {
      var open = nav.classList.toggle("open");
      toggle.setAttribute("aria-expanded", open ? "true" : "false");
    });
    // Close menu when a link is tapped (mobile)
    nav.addEventListener("click", function (e) {
      if (e.target.closest("a") && window.innerWidth <= 860) {
        nav.classList.remove("open");
        toggle.setAttribute("aria-expanded", "false");
      }
    });
  }

  /* Demo-only form handling.
     In SwipePages (or any host), replace these <form> elements with the
     platform's native form widget so submissions are captured as leads.
     Until a backend is connected, we intercept submit to show the
     thank-you behavior without losing the visitor. */
  document.querySelectorAll("form[data-demo]").forEach(function (form) {
    form.addEventListener("submit", function (e) {
      e.preventDefault();
      var redirect = form.getAttribute("data-redirect");
      if (redirect) {
        window.location.href = redirect;
        return;
      }
      var note = form.querySelector(".form-success");
      if (note) {
        note.hidden = false;
        form.querySelector("button[type=submit]").disabled = true;
      }
    });
  });
})();
