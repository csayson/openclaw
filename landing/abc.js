/* ============================================================
   A/B/C test harness — assignment, persistence, analytics
   ------------------------------------------------------------
   - index.html uses assignVariant() then redirects.
   - a/b/c pages call trackPage() + wireCtas() on load.
   Sticky per visitor via localStorage (+ cookie mirror so a
   server / analytics tool can read it too). Honors ?v=a|b|c
   override for QA and direct links.
   ============================================================ */
(function (global) {
  "use strict";

  var KEY = "abc_variant";
  var VARIANTS = ["a", "b", "c", "d"];
  // 25 / 25 / 25 / 25 cumulative thresholds
  var SPLIT = [
    { v: "a", max: 0.25 },
    { v: "b", max: 0.5 },
    { v: "c", max: 0.75 },
    { v: "d", max: 1.0 },
  ];

  function readOverride() {
    var m = /[?&](?:v|variant)=([abcd])/i.exec(global.location.search);
    return m ? m[1].toLowerCase() : null;
  }

  function getStored() {
    try {
      var v = global.localStorage.getItem(KEY);
      return VARIANTS.indexOf(v) !== -1 ? v : null;
    } catch (e) {
      return readCookie();
    }
  }

  function readCookie() {
    var m = new RegExp("(?:^|; )" + KEY + "=([abcd])").exec(document.cookie);
    return m ? m[1] : null;
  }

  function persist(v) {
    try {
      global.localStorage.setItem(KEY, v);
    } catch (e) {
      /* ignore */
    }
    // 90-day sticky cookie mirror
    var exp = new Date(Date.now() + 90 * 864e5).toUTCString();
    document.cookie = KEY + "=" + v + "; expires=" + exp + "; path=/; SameSite=Lax";
  }

  function roll() {
    var r = Math.random();
    for (var i = 0; i < SPLIT.length; i++) {
      if (r < SPLIT[i].max) return SPLIT[i].v;
    }
    return "d";
  }

  /* Resolve the visitor's variant: override > stored > new roll. */
  function resolveVariant() {
    var override = readOverride();
    if (override) {
      persist(override);
      return override;
    }
    var stored = getStored();
    if (stored) return stored;
    var fresh = roll();
    persist(fresh);
    return fresh;
  }

  /* Router entry point (index.html). Redirects to the variant page. */
  function assignVariant() {
    var v = resolveVariant();
    global.location.replace(v + ".html" + global.location.search);
  }

  /* --- Analytics ---------------------------------------------------
     Vendor-agnostic. Plausible/PostHog are loaded in the page <head>
     when configured; this just forwards events to whatever exists.   */
  function emit(event, props) {
    props = props || {};
    props.variant = currentVariant();
    // Plausible
    if (typeof global.plausible === "function") {
      global.plausible(event, { props: props });
    }
    // PostHog
    if (global.posthog && typeof global.posthog.capture === "function") {
      global.posthog.capture(event, props);
    }
    // Always leave a breadcrumb in the console for local QA
    if (global.__ABC_DEBUG__) {
      console.log("[abc]", event, props);
    }
  }

  function currentVariant() {
    return (
      document.body && document.body.getAttribute("data-variant")
    ) || getStored() || "?";
  }

  function trackPage() {
    emit("pageview_variant", { page: currentVariant() });
  }

  /* Wire any element with [data-cta] to fire a click goal, and tag
     checkout links with the variant so revenue traces back here. */
  function wireCtas() {
    var v = currentVariant();
    var els = document.querySelectorAll("[data-cta]");
    Array.prototype.forEach.call(els, function (el) {
      // Tag Stripe / checkout links with variant for revenue attribution
      if (el.tagName === "A" && el.href && /checkout|buy|stripe/i.test(el.href)) {
        try {
          var u = new URL(el.href);
          u.searchParams.set("client_reference_id", "variant_" + v);
          u.searchParams.set("utm_content", "variant_" + v);
          el.href = u.toString();
        } catch (e) {
          /* leave href untouched on parse failure */
        }
      }
      el.addEventListener("click", function () {
        emit("cta_click", {
          cta: el.getAttribute("data-cta"),
          location: el.getAttribute("data-cta-loc") || "body",
        });
      });
    });

    // Diagnostic: scroll depth past the pain section
    var pain = document.getElementById("pain");
    if (pain && "IntersectionObserver" in global) {
      var seen = false;
      var io = new IntersectionObserver(
        function (entries) {
          if (!seen && entries[0].isIntersecting) {
            seen = true;
            emit("scroll_past_pain");
            io.disconnect();
          }
        },
        { threshold: 0.6 }
      );
      io.observe(pain);
    }
  }

  global.ABC = {
    assignVariant: assignVariant,
    resolveVariant: resolveVariant,
    trackPage: trackPage,
    wireCtas: wireCtas,
    emit: emit,
    currentVariant: currentVariant,
  };
})(window);
