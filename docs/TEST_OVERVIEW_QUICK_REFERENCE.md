# 🧪 Test Overview - Quick Reference Card

## 🚀 START USING

```bash
# 1. Start the app
python3 app.py

# 2. Visit in browser
http://localhost:5000/test-overview
```

Or click **🧪 Test Overview** in sidebar (yellow highlight)

---

## 📊 WHAT YOU'LL SEE

| Column               | Shows                                    |
|---------------------|------------------------------------------|
| Employee Name       | Full name                                |
| Current/Recent      | Last visited country                     |
| Total Trips         | Number of EU trips                       |
| Days Used           | Days in Schengen (last 180 days)         |
| Days Left           | 90 - days used                           |
| Status              | 🟢 Safe / 🟠 Warning / 🔴 Exceeded       |
| Next Eligible Entry | Date when can re-enter (if over 90)      |
| Last Exit           | Most recent exit date                    |

---

## 🎨 STATUS COLORS

| Color | Emoji | Days Used | Meaning              |
|-------|-------|-----------|----------------------|
| Green | 🟢    | < 85      | Safe - plenty of room |
| Orange| 🟠    | 85-89     | Warning - close to limit |
| Red   | 🔴    | 90+       | Exceeded - cannot enter |

---

## 🔄 RELOAD DATA

Click **🔄 Reload Excel Data** button to:
1. Find latest `.xlsx` file in `uploads/` folder
2. Reimport all trip data
3. Refresh calculations
4. Auto-refresh page

Success: `✅ Success! Added X trips, skipped Y duplicates`

---

## ⚠️ REMEMBER

- **Ireland (IE) is excluded** from 90-day calculations
- Calculations use **rolling 180-day window** ending today
- **Warning threshold** is 85 days (not 90)
- Status shows **current compliance**, not forecast

---

## 🗑️ REMOVE (3 Steps)

```bash
# 1. Delete files
rm test_overview.py templates/test_overview.html TEST_OVERVIEW_*.md

# 2. Edit app.py - Remove lines 33-40:
# ════════════════════════════════════════
# TEMPORARY TEST ROUTE - DELETE THESE LINES
# from test_overview import test_bp
# app.register_blueprint(test_bp)
# ════════════════════════════════════════

# 3. Edit templates/base.html - Remove lines 84-92:
# <!-- TEMPORARY TEST LINK - DELETE THIS SECTION -->
# <a href="...">🧪 Test Overview</a>
# <!-- END TEMPORARY TEST LINK -->
```

Done! ✅

---

## 🐛 TROUBLESHOOTING

| Problem                | Solution                              |
|------------------------|---------------------------------------|
| "No data found"        | Import Excel via Import Data page     |
| Reload fails           | Check `uploads/` folder has .xlsx file|
| Wrong calculations     | Remember: Ireland doesn't count       |
| Can't access page      | Check Flask app is running            |

---

## 📖 MORE INFO

- **Full Guide:** `TEST_OVERVIEW_QUICK_START.md`
- **Removal:** `TEST_OVERVIEW_README.md`
- **Design:** `TEST_OVERVIEW_VISUAL_GUIDE.md`
- **Summary:** `TEST_OVERVIEW_IMPLEMENTATION_SUMMARY.md`

---

## ✅ VERIFICATION CHECKLIST

Use this page to verify:
- [ ] Employee names correct
- [ ] Country codes accurate (FR, DE, ES, BE, etc.)
- [ ] Trip counts reasonable
- [ ] Days used calculations make sense
- [ ] Ireland trips NOT in 90-day total
- [ ] Status colors match thresholds
- [ ] Reload button works
- [ ] Table looks clean and professional

---

## 🎯 EXAMPLE ROW

```
John Smith | France (FR) | 12 | 45 / 90 | 45 | 🟢 Safe | N/A | 15-03-2024
```

**Means:**
- Name: John Smith
- Last visited: France
- Total trips: 12
- Used 45 days in last 180 days
- Has 45 days remaining
- Status: Safe (under 85)
- Can enter anytime (no waiting)
- Last exited on 15 March 2024

---

**Quick Access:** `http://localhost:5000/test-overview`  
**Sidebar Link:** 🧪 Test Overview (yellow highlighted)  
**Purpose:** Verify Excel imports and 90/180-day calculations  
**Remove:** 3 simple steps - fully isolated code







