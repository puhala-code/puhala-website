# puhala.com — Squarespace Install Guide

Design: **B1 Bone Archive** (Direction B, palette 1)
Built for Squarespace 7.1 · Business plan

---

## Why a Code Block, not a new template

Creating a new template requires migrating all existing content (blog posts, galleries, store, etc.) and rebuilds the entire site. Instead this design uses **Squarespace's Code Block** feature (Business plan) to take over just the homepage while keeping the rest of the site untouched. No template migration needed.

---

## Install (two steps, ~5 minutes)

### Step 1 — Hide Squarespace's header/footer on the homepage only

1. In Squarespace, go to **Pages → Home → Settings (gear icon) → Advanced**
2. Paste the contents of `squarespace-header-inject.css` into the **Page Header Code Injection** box
3. Save

This hides Squarespace's native nav and footer *on this page only*. Every other page on your site is unaffected.

### Step 2 — Add the page content

1. Edit your homepage
2. Remove (or hide) any existing content sections
3. Add a **Code Block** — set it to full width
4. Paste the entire contents of `squarespace-bundle.html` into the Code Block
5. Save and preview

---

## After install

**Swapping in real photos**

Each photo placeholder is a `<figure>` or `<div>` with a `data-photo-id` attribute (p01–p07). To replace a placeholder with a real image, find the `.pmvp-plate__inner` div inside that element and replace it with:

```html
<img src="https://your-squarespace-image-url.jpg" alt="Description" class="pmvp-plate__img">
```

Squarespace hosts images at `static1.squarespace.com/…` — upload images in the Squarespace Media Library, right-click → Copy Image URL.

**Light / Darkroom toggle**

The toggle pill is fixed to the bottom-right corner of the page. It persists per visitor via `localStorage` — no server needed.

**If Squarespace nav still shows after Step 1**

Inspect the nav element in your browser's DevTools and note its actual class name. Then add an additional selector to the Step 1 CSS to match it.

---

## Files in this repo

| File | Purpose |
|------|---------|
| `squarespace-bundle.html` | Paste into the Code Block (Step 2) |
| `squarespace-header-inject.css` | Paste into Page Header Code Injection (Step 1) |
| `squarespace-install-instructions.html` | Original install notes from the design session |
