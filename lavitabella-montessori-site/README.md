# La Vita è Bella Montessori — Website

A complete, mobile-first, StoryBrand-structured website for **La Vita è Bella
Montessori**, a hybrid Montessori micro-school in Liberty Hill, TX (ages 3–10).

> **Why static HTML and not SwipePages?**
> This build was produced in an environment where **no SwipePages MCP/API was
> connected** (only Google Drive, Gmail, and GitHub were available). Rather than
> stop, the full site was built as clean, portable static HTML/CSS so every word
> of the approved copy, the SEO, the schema markup, and the form structure exist
> and are ready to use. It can be (a) pasted section-by-section into SwipePages,
> (b) hosted as-is on Netlify / GitHub Pages / any static host, or (c) handed to
> a developer. **The only thing that cannot be done here is clicking “publish”
> inside SwipePages and getting a SwipePages preview URL** — see
> [Publishing](#publishing) below.

## Pages

| File | Page | H1 |
|------|------|----|
| `index.html` | Home | Give Your Child the Gift of Loving to Learn |
| `programs.html` | Programs | Programs Built Around the Child — and Around Your Family |
| `about.html` | About | Why “Life Is Beautiful” |
| `contact.html` | Contact / Schedule a Free Tour | Come See It for Yourself |
| `thank-you.html` | Tour-request thank-you state | Thank You! |

One `<h1>` per page; H2/H3 hierarchy throughout. Sticky header + full footer on
every page. Primary CTA **“Schedule a Free Tour”** appears in the header, hero,
after the 3-step plan, and in the final banner on every page.

## Preview locally

```bash
cd lavitabella-montessori-site
python3 -m http.server 8080
# open http://localhost:8080
```

Resize the browser narrow (or use device emulation) to check the mobile-first
stacking — the primary CTA sits at the top of the hero on mobile.

## Publishing

**Option A — static host (fastest live URL):**
Push this folder to Netlify drop, GitHub Pages, or Cloudflare Pages. You get a
live preview URL in minutes with no code changes.

**Option B — SwipePages (the original target platform):**
1. Recreate the 4 pages in SwipePages using its section blocks.
2. Copy the finalized text from these files (copy is final — do not paraphrase).
3. Rebuild the two forms with SwipePages’ native form widget:
   - **Tour form** (contact page): Parent Name, Email, Phone (simple US text
     field — **no** multi-country dropdown), Child’s Age(s), interest dropdown,
     optional “Tell us about your child”. Submit → `thank-you.html` equivalent.
     **Tag leads: “Tour Request.”**
   - **Lead-magnet form** (home, contact, thank-you): First Name + Email →
     deliver the PDF guide. **Tag leads: “Lead Magnet.”**
4. Paste the `School`/LocalBusiness JSON-LD (in each file’s `<head>`) into
   SwipePages’ custom code block.
5. Carry over the per-page `<title>` and `<meta name="description">`.

## Forms — current state

The two forms are real, accessible HTML forms with the exact required fields.
They are wired with a small demo handler (`assets/js/main.js`) so the tour form
redirects to the thank-you page and the lead-magnet form shows a success state.
**They are not yet posting to a lead database** — connect them to SwipePages
(or any form backend / email service) to actually capture leads. Search the code
for `data-lead-tag` to see where each tag (“Tour Request” / “Lead Magnet”)
applies.

## Placeholders the owner MUST replace before publishing

All are marked in-page with an orange dashed **OWNER:** note and/or a photo
caption ribbon.

1. **Photos** — every `<figure class="img-ph">` uses a labeled placeholder with
   descriptive `alt` text. Replace with warm lifestyle photos:
   - Hero: child concentrating on a Montessori material
   - The guide working one-on-one with a child
   - Children gardening / baking (Friday Enrichment)
   - The prepared environment (wood, plants, light)
   - A child doing a practical-life task independently
   - Guide portrait (round) — appears on Home and About
2. **Guide name + bio + AMI credential** — Home (Section 3) and About.
3. **Testimonials** — 3 cards on Home; replace with real parent quotes (even two
   genuine quotes is enough).
4. **“Families helped” claim** — Home Section 3 (“across the Hill Country”).
   Verify/adjust before publishing.
5. **School year** — Home final banner says “2026–2027.” Confirm.
6. **Tuition** — Programs page; insert real numbers or keep the
   “Request Tuition Info” flow.
7. **Daily rhythm / exact street address** — Programs FAQ (optional detail).

## Design tokens

- Background cream `#FAF6EF` · sage primary `#5B7553` · terracotta CTA `#C96F4A`
  · charcoal text `#33312E`
- Headlines: Fraunces (serif) · Body: Nunito Sans (sans) — loaded from Google
  Fonts
- Buttons: terracotta, rounded, high-contrast. No exclamation-mark urgency
  anywhere; scarcity stated calmly (“limited to 10 students”).

## SEO / technical

- Unique `<title>` + meta description per page targeting “Montessori school
  Liberty Hill TX,” “hybrid Montessori,” “homeschool Montessori Liberty Hill,”
  and “Montessori preschool near Leander/Georgetown.”
- `School`/LocalBusiness JSON-LD with name, address (Liberty Hill, TX 78642),
  phone, email, and URL on every page.
- `robots.txt` + `sitemap.xml` included.
- Descriptive `alt` text on every image placeholder.
- SVG placeholder is tiny; replacement photos should be compressed and the
  below-the-fold images use `loading="lazy"` by default (hero image is eager).
