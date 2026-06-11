# A/B/C/D Landing Test — ClaudeWorks

Four complete landing-page variants behind a randomizing router. Same offer,
same pricing — different **story**. We're testing which *pain* converts, not
button colors.

## Files

| File         | Purpose                                                        |
| ------------ | ------------------------------------------------------------- |
| `index.html` | Randomizing router. Assigns a sticky variant, then redirects. |
| `a.html`     | **Direction A — "The Busywork Killer."** Pain-first / time recovery. |
| `b.html`     | **Direction B — "The Power Tool."** Metaphor-led / identity.  |
| `c.html`     | **Direction C — "The Redemption Story."** Validates the failed first AI attempt. |
| `d.html`     | **Direction D — "The Cape."** You're the superhero; the product is the cape that amplifies you. |
| `styles.css` | Shared stylesheet. Each variant sets one `--accent`; the rest follows. |
| `abc.js`     | Assignment, persistence (localStorage + cookie), and analytics. |

## How the split works

- **25 / 25 / 25 / 25**, randomized, **sticky per visitor** via `localStorage`
  (mirrored to a 90-day cookie so an analytics tool or server can read it too).
- `index.html` → rolls once, stores `abc_variant`, redirects to `a|b|c|d.html`.
- Returning visitors always land on the same variant.
- **QA override:** append `?v=a`, `?v=b`, `?v=c`, or `?v=d` to any URL to force a
  variant (also pins it for that browser). The footer of each page has quick
  Preview links.

## Wiring analytics (before you launch)

The pages are vendor-agnostic. Drop your snippet into the `<head>` of
`index.html` + `a/b/c.html` (look for the `Analytics snippet goes here`
comment). `abc.js` already forwards events to **Plausible** (`window.plausible`)
and **PostHog** (`window.posthog`) if either is present:

| Event               | When it fires                                  |
| ------------------- | ---------------------------------------------- |
| `pageview_variant`  | On every variant page load.                    |
| `cta_click`         | Any `[data-cta]` element clicked (props: `cta`, `location`). |
| `scroll_past_pain`  | Visitor scrolls 60% through the pain section (diagnostic). |

Every event carries a `variant` prop automatically.

**Revenue attribution:** checkout links (anything matching `checkout|buy|stripe`)
are auto-tagged with `client_reference_id=variant_<x>` and
`utm_content=variant_<x>` so Stripe revenue traces back to the page that earned
it. Replace the `https://checkout.example.com/...` placeholders with your real
Stripe Payment Links / Checkout URLs.

## Deploy

It's fully static — host the `landing/` folder on any static host (Netlify,
Vercel, Cloudflare Pages, S3, GitHub Pages). Point your domain root at
`index.html`. Done.

```
landing/
  index.html   ← domain root goes here
  a.html  b.html  c.html
  styles.css  abc.js
```

## Test plan (from the brief)

- **Primary metric:** paid conversion rate. *Only this locks the decision.*
- **Secondary (diagnostic):** email capture rate, scroll depth past pain, CTA
  click vs. checkout completion, 30-day retention by variant.
- **Sample / duration:** no winner before ~100 total conversions or 4 weeks,
  whichever is later. Thin traffic → $300–500 of evenly split ads buys a clean
  read in 2–3 weeks.

### Decision rules (set now)

1. **Clear winner** (≥40% better, adequate sample): lock it in.
2. **Two close, one trailing:** kill the trailer, go 50/50 for 2 more weeks.
3. **All within noise:** story isn't the constraint — test pricing/headlines
   next, not full rewrites.
4. **Winner converts but churns worse at 30 days:** runner-up wins. Retention
   beats acquisition for a subscription.

### Priors

- **A** — stat-driven headline ("40% of your week"); favorite on cold traffic.
- **C** — redemption angle; should dominate warm traffic / anyone who's already
  tried AI.
- **B** — strongest brand voice; best for trades-heavy ad audiences (watch on
  Meta ads targeting contractors).
- **D** — "The Cape" superhero framing: identity-affirming like B, but
  emotional rather than utilitarian (you're the hero, the product just amplifies
  you). Strong brand/recall play; watch its share-through and warm-traffic
  conversion against B.
- **Likely endgame:** A's stat headline + C's redemption logic + B's/D's
  metaphor as brand voice. Let data confirm before blending.

> **Note on a 4-way split:** four variants means each gets ~25% of traffic, so
> reaching the ~100-conversions-per-arm bar takes more traffic/time than the
> original 3-way. If traffic is thin, consider running B vs. D head-to-head
> first (both are the "metaphor" slot) and racing the winner against A and C.

## Copy hygiene

- The only verbatim line is the owner quote in A's pain header ("We don't own a
  small business. It owns us."). Everything else is paraphrased from research.
- Stats used: ~40% of week on admin; 51% admin-over-family; 62% monthly burnout;
  22% zero days off (2024); ~7x speed-to-lead within one hour; 66% hiring
  difficulty; 18% skip hiring and do it themselves. **Re-verify annually** —
  stale stats erode trust fast.

## Porting to SwipePages

These pages are the implementation the test plan calls for (static pages +
randomizing router). To run the same test inside **SwipePages** instead, the
SwipePages MCP server must be attached to the Claude Code session — see
`../.mcp.json` and the note in the PR/commit. Once connected, the copy blocks
above map 1:1 to SwipePages sections.

**Intended deployment:** publish the A/B/C/D test to the custom domain
**`onomachat.com`** via SwipePages (SwipePages hosts the pages and provides
native traffic-splitting, so its built-in split replaces `index.html` + `abc.js`
once live). Map the variants to SwipePages A/B/C/D test slots in this order:
A = Busywork Killer, B = Power Tool, C = Redemption Story, D = The Cape.
