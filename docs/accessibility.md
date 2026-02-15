# WCAG 2.1 AA Accessibility Checklist — Clew Directive

This document maps every WCAG 2.1 AA requirement to the specific CD component it affects, with implementation guidance. Social impact tools that exclude people with disabilities contradict their own mission.

## Target: WCAG 2.1 Level AA Conformance

---

## 1. Color & Contrast (Perceivable — 1.4.3, 1.4.11)

| Element | Colors | Ratio | Requirement | Status |
|---------|--------|-------|-------------|--------|
| Primary text (gold on navy) | #FDC500 on #0A233F | ~9.5:1 | 4.5:1 normal | ✅ Exceeds AAA |
| Dim/secondary text | #A0B4C8 on #0A233F | ~5.2:1 | 4.5:1 normal | ✅ Passes AA |
| Large headings (gold on navy) | #FDC500 on #0A233F | ~9.5:1 | 3:1 large | ✅ Exceeds AAA |
| Paper mode body text | #1a1a1a on #fdfdfd | ~17:1 | 4.5:1 normal | ✅ Exceeds AAA |
| Interactive borders | Gold 30% opacity on navy | TBD | 3:1 non-text | ⚠ Verify |
| Focus indicators | #FDC500 outline | ~9.5:1 | 3:1 | ✅ Passes |
| Badge text (dim on navy) | #A0B4C8 on #0A233F | ~5.2:1 | 4.5:1 | ✅ Passes AA |
| Free badge (green on navy) | #81c784 on #0A233F | ~4.7:1 | 4.5:1 | ✅ Passes AA |
| PDF body text | #1a1a1a on #fdfdfd | ~17:1 | 4.5:1 | ✅ Exceeds AAA |

**Action items:**
- [ ] Verify all interactive element borders at 3:1 against adjacent colors
- [ ] Test with WebAIM Contrast Checker before launch
- [ ] Never use color alone to convey information (always pair with text/icons)

---

## 2. Motion & Animation (2.3.1, 2.3.3)

| Animation | Component | Reduced Motion Behavior |
|-----------|-----------|------------------------|
| Blinking cursor | Terminal UI | Static cursor (no blink) |
| Typing text effect | Vibe Check questions | Text appears instantly |
| "Processing..." animation | Between questions | Text appears instantly |
| "Compiling your profile..." | Post-Vibe Check | Text appears instantly |
| Boot sequence (if any) | Welcome screen | Skip entirely |

**Implementation:**
```css
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
  }
}
```

**Rules:**
- [ ] No content flashes more than 3 times per second
- [ ] All animations wrapped in prefers-reduced-motion media query
- [ ] CSS in globals.css already implements this

---

## 3. Keyboard Navigation (2.1.1, 2.1.2, 2.4.3, 2.4.7)

| Component | Keyboard Behavior |
|-----------|-------------------|
| Welcome screen | Tab to "Begin Vibe Check" button, Enter to activate |
| Vibe Check options | Tab through options, Enter/Space to select |
| "That's me" / "Not quite" | Tab between buttons, Enter to activate |
| Correction text input | Tab to focus, type correction |
| Resource links | Tab to each link, Enter to follow |
| Download PDF button | Tab to focus, Enter to download |
| Email stub button | Tab to focus (disabled state announced) |
| Coming Soon modal | Focus trapped inside, Escape to close |

**Rules:**
- [ ] No keyboard traps — user can always Tab away
- [ ] Logical tab order (top to bottom, left to right)
- [ ] Visible focus ring on ALL interactive elements (gold outline, 2px)
- [ ] Skip navigation link at top of page
- [ ] Focus management: when new content appears, move focus appropriately

---

## 4. Screen Reader Support (1.3.1, 4.1.2)

| Component | Semantic HTML | ARIA |
|-----------|---------------|------|
| Terminal container | `<main role="main">` | `aria-label="Clew Directive"` |
| Vibe Check questions | `<fieldset>` + `<legend>` | — |
| Options | `<input type="radio">` + `<label>` | — |
| Profile summary | `<div>` | `aria-live="polite"` |
| "Processing..." state | `<div>` | `aria-live="polite"`, `aria-busy="true"` |
| Results section | `<section>` | `aria-label="Your learning path"` |
| Resource list | `<ol>` (ordered = sequenced) | — |
| Session warning | `<div role="alert">` | `aria-live="polite"` |
| Download button | `<button>` or `<a>` | `aria-label="Download Command Briefing PDF"` |
| Email stub | `<button disabled>` | `aria-label="Email briefing — coming soon"` |

**Rules:**
- [ ] Use semantic HTML first, ARIA only when semantic HTML is insufficient
- [ ] All images have alt text (or aria-hidden if decorative)
- [ ] Form inputs have associated labels
- [ ] Dynamic content changes announced via aria-live regions
- [ ] Error messages associated with inputs via aria-describedby

---

## 5. Responsive & Reflow (1.4.10, 1.4.4)

- [ ] Content reflows at 320px CSS width without horizontal scrolling
- [ ] Terminal aesthetic works on mobile — options don't clip or truncate
- [ ] Text resizable up to 200% without loss of content
- [ ] Touch targets minimum 44x44px on mobile
- [ ] No content hidden behind overflow on small screens

---

## 6. Testing Tools

| Tool | Purpose | When |
|------|---------|------|
| axe-core | Automated WCAG testing in CI | Every build |
| @axe-core/react | Runtime accessibility checking in dev | During development |
| WebAIM Contrast Checker | Verify color contrast ratios | Design phase |
| Keyboard-only navigation | Manual testing | Before each release |
| VoiceOver (macOS) / NVDA (Windows) | Screen reader testing | Before launch |
| Firefox Accessibility Inspector | DOM inspection | Development |

**npm packages included in frontend/package.json:**
- `axe-core` — automated scanning
- `@axe-core/react` — React integration for dev mode

---

## 7. PDF Accessibility

The Command Briefing PDF (generated via WeasyPrint) should:
- [ ] Have a document title set
- [ ] Use semantic HTML in the source template (headings, lists, links)
- [ ] Include clickable hyperlinks (WeasyPrint preserves `<a href>` tags)
- [ ] Use sufficient contrast (verified in template CSS)
- [ ] Be machine-readable (not an image of text)

---

## Article Quote
> "Clew Directive targets WCAG 2.1 AA compliance because a social impact tool that excludes people with disabilities contradicts its own mission."
