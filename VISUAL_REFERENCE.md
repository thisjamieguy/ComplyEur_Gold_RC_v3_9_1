# 📸 EU Entry Requirements - Visual Reference

## Page Preview

```
╔════════════════════════════════════════════════════════════════════╗
║  SIDEBAR          │  MAIN CONTENT                                  ║
╠════════════════════╪════════════════════════════════════════════════╣
║                    │                                                ║
║  🇪🇺 EU Tracker    │  ╔═══════════════════════════════════════════╗║
║                    │  ║  🇪🇺 EU Entry Requirements (UK Citizens)  ║║
║  📊 Dashboard      │  ║  Current Schengen and EU entry rules for  ║║
║  ✈️  Add Trips     │  ║  short business stays and work visits     ║║
║  📄 Import Data    │  ╚═══════════════════════════════════════════╝║
║  📅 Calendar       │                                                ║
║                    │  ┌─────────┬─────────┬─────────┐             ║
║  ADMINISTRATION    │  │🛂 Sch..│📋 ETIAS │✋ EES   │             ║
║  🛡️  Privacy Tools │  │27 count│Q4 2026  │Oct 2025 │             ║
║  ⚙️  Settings      │  └─────────┴─────────┴─────────┘             ║
║                    │                                                ║
║  SUPPORT           │  ┌───────────────────────────────────────┐   ║
║  🏛️  EU Entry Req. │  │ 🔍 Search countries...  [Filter ▼]    │   ║
║  ❓ Help Tutorial  │  │ Showing 6 of 6 | Last update: Oct 8   │   ║
║                    │  └───────────────────────────────────────┘   ║
║  🔒 Change Pass    │                                                ║
║  🚪 Logout         │  ┌─────────────────┐  ┌─────────────────┐   ║
║                    │  │🇦🇹 Austria      │  │🇧🇪 Belgium      │   ║
║                    │  │ Schengen        │  │ Schengen        │   ║
║                    │  │                 │  │                 │   ║
║                    │  │📅 90/180 rule   │  │📅 90/180 rule   │   ║
║                    │  │🛂 3 months min  │  │🛂 3 months min  │   ║
║                    │  │📋 ETIAS Q4 2026 │  │📋 ETIAS Q4 2026 │   ║
║                    │  │✋ EES Oct 12/25  │  │✋ EES Oct 12/25  │   ║
║                    │  │                 │  │                 │   ║
║                    │  │⚠️  Notes for HR │  │⚠️  Notes for HR │   ║
║                    │  │Travel for meet..│  │Short meetings..│   ║
║                    │  │                 │  │                 │   ║
║                    │  │🔗 Sources...    │  │🔗 Sources...    │   ║
║                    │  │Last: 2025-10-08 │  │Last: 2025-10-08 │   ║
║                    │  └─────────────────┘  └─────────────────┘   ║
╚════════════════════╧════════════════════════════════════════════════╝
```

---

## Color Scheme

### Header Gradient
```
┌─────────────────────────────────────────────────┐
│ Gradient: #4C739F → #5B6C8F (IES Blue to Dark) │
│ Text: White (#FFFFFF)                           │
│ Font: Helvetica Neue, 28px, Bold                │
└─────────────────────────────────────────────────┘
```

### Card Colors

#### Green Card (Safe)
```
┌───────────────────────┐
│ ┃ 🇮🇪 Ireland        │  ← Green left border (#10b981)
│ ┃ Non-Schengen       │
│ ┃                    │
│ ┃ No time limit      │
│ ┃ (CTA member)       │
└───────────────────────┘
```

#### Amber Card (Check Required)
```
┌───────────────────────┐
│ ┃ 🇦🇹 Austria        │  ← Amber left border (#f59e0b)
│ ┃ Schengen           │
│ ┃                    │
│ ┃ ETIAS from 2026    │
│ ┃ Work permit needed │
└───────────────────────┘
```

#### Red Card (Restricted)
```
┌───────────────────────┐
│ ┃ 🇫🇷 France         │  ← Red left border (#ef4444)
│ ┃ Schengen           │
│ ┃                    │
│ ┃ Paid work          │
│ ┃ prohibited         │
└───────────────────────┘
```

---

## Interactive Elements

### Search Bar (Active State)
```
┌──────────────────────────────────────┐
│ 🔍  belgium_                         │  ← Blue border when focused
└──────────────────────────────────────┘
     ↑ Icon stays grey
```

### Filter Dropdown (Expanded)
```
┌─────────────────────┐
│ All Countries    ▼  │
├─────────────────────┤
│ All Countries       │  ← Selected (blue bg)
│ Schengen Only       │
│ Non-Schengen        │
│ ETIAS Soon          │
└─────────────────────┘
```

### Tooltip (Hover State)
```
        Hover over ?
             ↓
    ┌────────────────────────────────┐
    │ European Travel Information &  │  ← Dark grey (#1f2937)
    │ Authorisation System - required│    White text
    │ from Q4 2026                   │
    └────────────────────────────────┘
           ▼                            ← Arrow pointer
          ETIAS ? 
```

### Card Hover Effect
```
Before Hover:
┌─────────────────┐
│ 🇦🇹 Austria     │  Box shadow: light (0 1px 3px)
│ ...             │  Transform: none
└─────────────────┘

On Hover:
  ┌─────────────────┐
  │ 🇦🇹 Austria     │  Box shadow: stronger (0 4px 12px)
  │ ...             │  Transform: translateY(-2px)
  └─────────────────┘
      ↑ Lifts slightly
```

---

## Typography

### Font Hierarchy
```
H1 (Page Title):
  Font: Helvetica Neue, 28px, Bold (600)
  Color: White (#FFFFFF)
  
H2 (Country Names):
  Font: Helvetica Neue, 20px, SemiBold (600)
  Color: Dark Grey (#1f2937)

H3 (Info Box Titles):
  Font: Helvetica Neue, 14px, SemiBold (600)
  Color: Dark Grey (#1f2937)

Labels (Detail Labels):
  Font: Helvetica Neue, 13px, SemiBold (600)
  Color: Medium Grey (#4b5563)

Body Text (Detail Values):
  Font: Helvetica Neue, 14px, Regular (400)
  Color: Dark Grey (#1f2937)

Small Text (Sources, Last Checked):
  Font: Helvetica Neue, 12px/11px, Regular (400)
  Color: Light Grey (#9ca3af)
```

---

## Badge Styles

### Schengen Badge (Blue)
```
┌──────────┐
│ Schengen │  Background: Light Blue (#dbeafe)
└──────────┘  Text: Dark Blue (#1e40af)
              Border Radius: 6px
              Padding: 4px 12px
```

### Non-Schengen Badge (Red)
```
┌──────────────┐
│ Non-Schengen │  Background: Light Red (#fee2e2)
└──────────────┘  Text: Dark Red (#991b1b)
                  Border Radius: 6px
                  Padding: 4px 12px
```

---

## Notes Box (Amber Warning)

```
┌─────────────────────────────────────────┐
│ ┃ 📌 Notes for HR                       │  ← Yellow left border
│ ┃                                        │    (#f59e0b, 3px)
│ ┃ Travel for meetings/events OK visa-   │
│ ┃ free; paid work needs permit. Check   │    Background: #fef3c7
│ ┃ passport validity and insurance.      │    Text: #78350f
│ ┃ Watch for EES/ETIAS launch dates.     │
└─────────────────────────────────────────┘
```

---

## Info Boxes (Top Section)

### Schengen Info Box
```
┌─────────────────────────────────────┐
│ ┃ 🛂 Schengen Area                  │  ← Blue border (#3b82f6)
│ ┃                                    │
│ ┃ 27 European countries with no      │
│ ┃ internal borders. UK visitors can  │
│ ┃ spend 90 days in any 180-day...    │
└─────────────────────────────────────┘
```

### ETIAS Info Box
```
┌─────────────────────────────────────┐
│ ┃ 📋 ETIAS                           │  ← Purple border (#8b5cf6)
│ ┃                                    │
│ ┃ European Travel Information and    │
│ ┃ Authorisation System. Required...  │
└─────────────────────────────────────┘
```

### EES Info Box
```
┌─────────────────────────────────────┐
│ ┃ ✋ EES                             │  ← Pink border (#ec4899)
│ ┃                                    │
│ ┃ Entry/Exit System. In effect from  │
│ ┃ Oct 12, 2025. Biometric...         │
└─────────────────────────────────────┘
```

---

## Source Links Display

```
🔗 Sources:
1. home-affairs.ec.europa.eu/policie...  ← Truncated to 40 chars
2. etias.com/etias-requirements/etias...
3. gov.uk/foreign-travel-advice/austr...

Colors:
  Normal: IES Blue (#4C739F)
  Hover: IES Dark Blue (#5B6C8F) + underline
```

---

## No Results State

```
┌──────────────────────────────────────┐
│                                      │
│              ╭─────╮                 │
│              │  🔍 │  ← Large search │
│              ╰─────╯      icon (64px)│
│                                      │
│       No countries found             │  ← Medium grey text
│                                      │
│   Try adjusting your search or       │  ← Light grey text
│   filter criteria                    │
│                                      │
└──────────────────────────────────────┘
```

---

## Mobile Layout (≤768px)

```
┌──────────────────────────────────────┐
│  🇪🇺 EU Entry Requirements           │
│  Current Schengen and EU entry...    │
└──────────────────────────────────────┘

┌──────────────────────────────────────┐
│🛂 Schengen | 📋 ETIAS | ✋ EES       │  ← Stacked on very
└──────────────────────────────────────┘    small screens

┌──────────────────────────────────────┐
│ 🔍 Search countries...               │
├──────────────────────────────────────┤
│ [All Countries ▼]                    │  ← Full width
├──────────────────────────────────────┤
│ Showing 6 of 6 | Last update: Oct 8  │
├──────────────────────────────────────┤
│ [🔄 Refresh]                          │
└──────────────────────────────────────┘

┌──────────────────────────────────────┐
│ 🇦🇹 Austria              Schengen    │
│                                      │
│ 📅 90/180 rule                       │
│ 🛂 3 months beyond departure         │
│ ...                                  │  ← Single column
└──────────────────────────────────────┘

┌──────────────────────────────────────┐
│ 🇧🇪 Belgium              Schengen    │
│ ...                                  │
└──────────────────────────────────────┘
```

---

## Button States

### Refresh Button
```
Normal:
┌─────────────┐
│ 🔄 Refresh  │  Background: IES Blue (#4C739F)
└─────────────┘  Text: White

Hover:
┌─────────────┐
│ 🔄 Refresh  │  Background: IES Dark Blue (#5B6C8F)
└─────────────┘  Cursor: pointer
```

---

## Scrollbar (Country Grid)

```
┌─────────────────────┐
│ Cards...            ║  ← Custom scrollbar
│                     ║    Width: 8px
│                     ║    Track: Light grey (#f9fafb)
│                     ║    Thumb: Medium grey (#d1d5db)
│                     ║    Thumb hover: Dark grey (#9ca3af)
└─────────────────────┘
```

---

## Animation Effects

### Card Entry
```
Opacity: 0 → 1 (fade in)
Transform: translateY(-8px) → translateY(0)
Duration: 150ms ease-out
```

### Dropdown Appear
```
Opacity: 0 → 1
Transform: translateY(-8px) → translateY(0)
Duration: 150ms ease-out
Animation: dropdownFadeIn
```

### Card Hover
```
Transform: translateY(0) → translateY(-2px)
Box-shadow: Light → Strong
Duration: 200ms ease
```

---

## Spacing & Layout

### Grid Spacing
```
Desktop (>768px):
  Columns: auto-fill, minmax(500px, 1fr)
  Gap: 20px
  
Mobile (≤768px):
  Columns: 1fr (single column)
  Gap: 20px
```

### Card Internal Spacing
```
┌─────────────────────────────────┐
│ ← 24px                  24px → │
│ ↑                              ↑│
│ 24px  Country Header      24px │
│       (16px margin-bottom)     │
│                                 │
│       Detail (12px margin)     │
│       Detail (12px margin)     │
│       ...                       │
│                                 │
│ ↓                              ↓│
│ ← 24px                  24px → │
└─────────────────────────────────┘
```

---

## Real Data Example

### Austria Card (Full Detail)
```
┌─────────────────────────────────────────┐  ← Green border (4px)
│ 🇦🇹 Austria              [Schengen]     │
│                                          │
│ 📅 Short Stay Rule                       │
│ Up to 90 days in any 180-day period     │
│ across the Schengen Area.               │
│                                          │
│ 🛂 Passport Validity                     │
│ Must be valid for at least 3 months     │
│ after the intended departure from        │
│ Schengen, issued within the last 10     │
│ years.                                  │
│                                          │
│ ETIAS Status ?                           │  ← Tooltip on ?
│ ETIAS mandatory for British citizens    │
│ from Q4 2026.                           │
│                                          │
│ EES Status ?                             │  ← Tooltip on ?
│ EES in effect from 12 Oct 2025; all     │
│ non-EU arrivals biometric registration  │
│ required at airports, seaports, land... │
│                                          │
│ ┌────────────────────────────────────┐  │
│ │ ⚠️  📌 Notes for HR                 │  │  ← Amber box
│ │                                    │  │
│ │ Travel for meetings/events OK      │  │
│ │ visa-free; paid work needs permit. │  │
│ │ Check passport validity and        │  │
│ │ insurance. Watch for EES/ETIAS...  │  │
│ └────────────────────────────────────┘  │
│                                          │
│ ─────────────────────────────────────── │  ← Divider line
│                                          │
│ 🔗 Sources:                              │
│ 1. home-affairs.ec.europa.eu/policie... │  ← Blue links
│ 2. etias.com/etias-requirements/eti... │
│ 3. gov.uk/foreign-travel-advice/aus... │
│                                          │
│ Last checked: 2025-10-08                │  ← Light grey, 11px
└─────────────────────────────────────────┘
```

---

## Browser Compatibility

✅ Chrome 90+ (fully tested)  
✅ Firefox 88+ (CSS Grid, Flexbox)  
✅ Safari 14+ (iOS Safari too)  
✅ Edge 90+ (Chromium-based)  
⚠️ IE11 (not supported - no CSS Grid)

---

## Accessibility

- ✅ Semantic HTML structure
- ✅ ARIA labels on interactive elements
- ✅ Keyboard navigation (Tab, Enter, Escape)
- ✅ Focus indicators on inputs/dropdowns
- ✅ Sufficient color contrast (WCAG AA)
- ✅ Tooltips work with keyboard focus

---

## Print Preview

When printing (or PDF export in future):
- Remove blue gradient header background
- Convert to greyscale borders
- Expand all cards (no grid, stacked)
- Show full source URLs (no truncation)
- Page breaks between countries

---

**Visual design complete!** All elements follow IES brand guidelines and provide an intuitive, professional user experience.



