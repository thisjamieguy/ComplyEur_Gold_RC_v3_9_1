# Prompt: Automated Heuristic Review (Nielsen’s 10)

You are a team of senior UX researchers performing a heuristic evaluation of this web app.

**App context:**  
IES EU 90/180 Employee Travel Tracker — a Flask + SQLite app used to log employee trips, calculate EU 90/180 compliance, and visualize risk levels.

**Goal:**  
Identify UX and usability issues according to **Nielsen’s 10 heuristics** across all key pages:
- Login
- Dashboard
- Employees
- Trips
- Import
- Forecast
- Admin

**Instructions:**
1. Crawl or read through all HTML templates under `/templates/`.
2. Review the structure, wording, labels, error handling, and visual hierarchy.
3. For each of Nielsen’s 10 heuristics:
   - Explain what the heuristic means.
   - Identify violations in this app’s templates or interactions.
   - Suggest **specific, low-effort improvements** (CSS, copy, layout, buttons).
4. Rate each page for each heuristic from 1–5:
   - 1 = Poor compliance
   - 5 = Excellent compliance
5. Produce a final summary table:
   - Page
   - Heuristic
   - Score
   - Recommended fixes
6. Output everything in clean Markdown for use in `/docs/UI_Heuristic_Review.md`.

**Special notes:**
- Assume Bootstrap 5 base.
- Keep suggestions practical and low-risk.
- Prioritize clarity, accessibility, and consistency over visual flair.

After completing the review, generate `/docs/UI_Heuristic_Review.md` with your findings.