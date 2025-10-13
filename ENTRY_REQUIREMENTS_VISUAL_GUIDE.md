# EU Entry Requirements - Visual Design Guide

## 🎨 Page Layout Overview

```
┌─────────────────────────────────────────────────────────────┐
│  🇪🇺 EU Entry Requirements (UK Citizens)                    │
│  Current Schengen and EU entry rules...                     │
│  [Blue gradient header with white text]                     │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│  🛂 Schengen Area  │  📋 ETIAS  │  ✋ EES                   │
│  [Info boxes explaining key concepts]                       │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ 🔍 Search... [Filter ▼] Showing X of Y [Refresh]           │
└─────────────────────────────────────────────────────────────┘

┌───────────────────────┐  ┌───────────────────────┐
│ 🇦🇹 Austria           │  │ 🇧🇪 Belgium           │
│ ▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒ │  │ ▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒ │
│ [City photo header]   │  │ [City photo header]   │
│ ───────────────────── │  │ ───────────────────── │
│ SHORT STAY RULE       │  │ SHORT STAY RULE       │
│ 90 days in 180...     │  │ 90 days in 180...     │
│                       │  │                       │
│ ETIAS STATUS          │  │ ETIAS STATUS          │
│ [Badge: Mandatory]    │  │ [Badge: Required]     │
│                       │  │                       │
│ EES STATUS            │  │ EES STATUS            │
│ Active from Oct 12... │  │ Active from Oct 12... │
│                       │  │                       │
│ NOTES FOR HR          │  │ NOTES FOR HR          │
│ Standard rules app... │  │ Standard rules app... │
│                       │  │                       │
│ [More Info Button]    │  │ [More Info Button]    │
└───────────────────────┘  └───────────────────────┘

┌───────────────────────┐  ┌───────────────────────┐
│ 🇫🇷 France            │  │ 🇩🇪 Germany           │
│ [Cards continue...]   │  │ [Cards continue...]   │
└───────────────────────┘  └───────────────────────┘
```

---

## 🃏 Country Card Design

### Card Structure (220px height approx)

```
┌─────────────────────────────────────────────────┐
│ ╔═══════════════════════════════════════════╗   │
│ ║ [City Photo Background with Blue Overlay]║   │
│ ║                                           ║   │
│ ║  🇫🇷  France              [SCHENGEN]     ║   │
│ ║                                           ║   │
│ ╚═══════════════════════════════════════════╝   │
│                                                 │
│  SHORT STAY RULE                                │
│  90 days in any 180-day period across...       │
│  ─────────────────────────────────────────────  │
│  ETIAS STATUS                                   │
│  Mandatory from Q4 2026                         │
│  ─────────────────────────────────────────────  │
│  EES STATUS                                     │
│  Active from October 12, 2025                   │
│  ─────────────────────────────────────────────  │
│  NOTES FOR HR                                   │
│  Standard Schengen rules apply for...          │
│                                                 │
│  ┌───────────────────────────────────────┐     │
│  │         ℹ️  More Info                │     │
│  └───────────────────────────────────────┘     │
└─────────────────────────────────────────────────┘
```

### Card Hover Effect
- Lifts up by 4px
- Shadow increases (soft elevation)
- Smooth 0.3s transition

---

## 🔲 Modal Overlay Design

### When "More Info" is clicked:

```
                  [Blurred Background]

        ┌─────────────────────────────────────┐
        │ ╔═══════════════════════════════╗ X │
        │ ║ [City Photo - Full Width]     ║   │
        │ ║                               ║   │
        │ ║  🇫🇷  France                  ║   │
        │ ║  🛂 Schengen Area Member      ║   │
        │ ╚═══════════════════════════════╝   │
        │ ─────────────────────────────────── │
        │                                     │
        │ 📅 SHORT STAY RULE                  │
        │ 90 days in any 180-day period       │
        │ across all Schengen states...       │
        │                                     │
        │ 🛂 PASSPORT VALIDITY REQUIREMENTS   │
        │ Must be valid for at least 3        │
        │ months beyond your intended...      │
        │                                     │
        │ 📋 ETIAS STATUS                     │
        │ Mandatory from Q4 2026              │
        │ [Explanation text...]               │
        │                                     │
        │ ✋ EES STATUS                        │
        │ Active from October 12, 2025        │
        │ [Explanation text...]               │
        │                                     │
        │ 💼 BUSINESS TRAVEL CONSIDERATIONS   │
        │ [Full details...]                   │
        │                                     │
        │ ┌─────────────────────────────┐     │
        │ │ 📌 Important Notes for HR   │     │
        │ │ [Yellow highlighted box]    │     │
        │ └─────────────────────────────┘     │
        │                                     │
        │ 🔗 OFFICIAL SOURCES & REFERENCES    │
        │ 1. https://...                      │
        │ 2. https://...                      │
        │ 3. https://...                      │
        │                                     │
        │ Last verified: 2025-10-10           │
        │ ─────────────────────────────────── │
        └─────────────────────────────────────┘
```

### Modal Features:
- **Width**: 800px max (responsive on mobile)
- **Height**: Up to 90vh with scroll
- **Animation**: Scale from 0.9 to 1.0, fade in
- **Close options**:
  - X button (top right, rotates on hover)
  - Click outside modal
  - Press ESC key
- **Background**: Dark overlay with blur effect

---

## 🎨 Color System

### Primary Colors
```css
Background:     #f5f6f8  ░░░░░ Light grey
Card BG:        #ffffff  █████ Pure white
Primary Blue:   #4C8BC0  ████▓ Accent color
Dark Blue:      #2d5a7b  ███▓░ Hover states
```

### Status Badges
```css
Active/Green:   #dcfce7  [Not Required ✓]
Soon/Blue:      #dbeafe  [Mandatory 2026 ⓘ]
Required/Amber: #fef3c7  [Required Soon ⚠]
```

### Text Colors
```css
Headings:       #1f2937  Dark grey
Body text:      #4b5563  Medium grey
Muted text:     #6b7280  Light grey
Labels:         #9ca3af  Very light grey
```

---

## 📐 Typography Scale

```
Page Title (h1):     28px / Bold / White
Card Country:        24px / SemiBold / White
Modal Country:       32px / SemiBold / White

Section Headers:     14px / SemiBold / Blue (uppercase)
Body Text:          14-15px / Regular / Dark Grey
Labels:             11px / SemiBold / Grey (uppercase)
Small Text:         12-13px / Regular / Light Grey
```

---

## 📱 Responsive Breakpoints

### Desktop (> 768px)
```
┌────────┐  ┌────────┐
│ Card 1 │  │ Card 2 │
└────────┘  └────────┘
┌────────┐  ┌────────┐
│ Card 3 │  │ Card 4 │
└────────┘  └────────┘
```

### Mobile (≤ 768px)
```
┌──────────────┐
│   Card 1     │
└──────────────┘
┌──────────────┐
│   Card 2     │
└──────────────┘
┌──────────────┐
│   Card 3     │
└──────────────┘
```

---

## 🖼️ City Photo System

### Image Paths
```
/static/cities/austria.jpg
/static/cities/belgium.jpg
/static/cities/france.jpg
/static/cities/germany.jpg
... etc
```

### Fallback Gradient
If image missing, shows:
```css
background: linear-gradient(135deg, 
    #4C8BC0 0%,    /* Light blue */
    #2d5a7b 100%   /* Dark blue */
);
```

### Photo Overlay
```css
Semi-transparent gradient overlay:
- Top: rgba(0, 0, 0, 0.2) - Lighter
- Bottom: rgba(0, 0, 0, 0.6) - Darker
Purpose: Ensures white text is always readable
```

---

## ✨ Animation Timeline

### Card Hover
```
0ms   → Start: translateY(0), shadow: small
300ms → End:   translateY(-4px), shadow: large
```

### Modal Open
```
0ms   → display: flex, opacity: 0, scale: 0.9
10ms  → Trigger animation
300ms → opacity: 1, scale: 1.0
```

### Modal Close
```
0ms   → opacity: 1, scale: 1.0
300ms → opacity: 0, scale: 0.9
300ms → display: none
```

### Button States
```
Normal → Hover: 200ms transition
Background color shift
```

---

## 🎯 Interactive Elements

### Buttons

**More Info Button:**
```
┌─────────────────────────┐
│   ℹ️  More Info         │  ← Blue #4C8BC0
└─────────────────────────┘
         ↓ Hover
┌─────────────────────────┐
│   ℹ️  More Info         │  ← Darker blue #3a6d96
└─────────────────────────┘
```

**Close Button (Modal):**
```
   ( X )  ← Semi-transparent white circle
     ↓ Hover
   ( ⟲ )  ← Rotates 90° + brighter
```

### Status Badges

```
┌──────────────────┐
│ Not Required ✓   │  ← Green background
└──────────────────┘

┌──────────────────┐
│ Mandatory 2026 ⓘ │  ← Blue background
└──────────────────┘

┌──────────────────┐
│ Required Soon ⚠  │  ← Amber background
└──────────────────┘
```

---

## 🔍 Search & Filter Bar

```
┌────────────────────────────────────────────────────────────┐
│ 🔍 [Search countries...        ]  [Filter ▼]  [Showing]  │
│                                                            │
│  Showing 35 of 35 countries | Last data update: 2025-10-10│
└────────────────────────────────────────────────────────────┘
```

**Filter Options:**
- All Countries (default)
- Schengen Only
- Non-Schengen
- ETIAS Soon

---

## 💡 UX Patterns

### Progressive Disclosure
```
Summary Card (Scannable)
        ↓ Click "More Info"
Modal (Comprehensive Details)
```

### Visual Hierarchy
```
1. City Photo (draws attention)
2. Country Name (large, bold)
3. Key Info (scannable sections)
4. Action Button (clear CTA)
```

### Feedback Loops
```
Hover → Lift animation (feedback)
Click → Modal opens (action confirmed)
ESC → Modal closes (escape route)
```

---

## 📊 Grid System

### Card Grid
```css
Display: CSS Grid
Columns: repeat(2, 1fr)  /* 2 equal columns */
Gap: 24px                /* Space between cards */

Mobile: grid-template-columns: 1fr  /* Single column */
```

### Info Boxes (Top Section)
```css
Display: CSS Grid
Columns: repeat(auto-fit, minmax(280px, 1fr))
Gap: 16px
```

---

## 🎪 Special Components

### Notes for HR Box (Yellow Alert)
```
┌─────────────────────────────────────┐
│ ║ 📌 Important Notes for HR         │
│ ║                                   │
│ ║ Work permits may be required...  │
└─────────────────────────────────────┘
   │
   └─ Yellow background (#fef3c7)
      Orange left border (#f59e0b)
```

### Source Links
```
🔗 Official Sources & References
├─ 1. https://www.gov.uk/...
├─ 2. https://europa.eu/...
└─ 3. https://www.schengenvisainfo.com/...
```

---

## ✅ Visual Quality Checklist

- [ ] Cards align in perfect grid
- [ ] City photos load (or show gradient)
- [ ] Text is always readable over photos
- [ ] Hover effects are smooth
- [ ] Modal animation is fluid
- [ ] Close button is visible
- [ ] Status badges use correct colors
- [ ] Typography hierarchy is clear
- [ ] White space feels balanced
- [ ] Mobile layout stacks properly
- [ ] No horizontal scrolling on mobile
- [ ] All interactive elements have cursor: pointer

---

*This visual guide helps designers and developers understand the expected appearance and behavior of the redesigned EU Entry Requirements page.*






