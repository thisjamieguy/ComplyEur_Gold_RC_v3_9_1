### UI Heuristic Review — ComplyEur (EU 90/180 Employee Travel Tracker)

- **Review date**: 04 Nov 2025
- **Reviewers**: Senior UX Research Team
- **Scope**: Login, Dashboard, Employees, Trips, Import, Forecast, Admin
- **Method**: Heuristic evaluation using Nielsen’s 10 principles; reviewed `app/templates/` and key interactions in JS loaded by `base.html`.
- **Assumptions**: Bootstrap 5 base, privacy-first, local-only app.

---

### How to read this
- Each heuristic includes: meaning, notable issues found in ComplyEur, low-effort fixes, and per‑page scores (1–5).
- Pages: Login, Dashboard, Employees (employee detail), Trips (calendar/timeline), Import, Forecast (What‑If + alerts), Admin (settings, privacy tools).

---

### 1) Visibility of system status
- **Meaning**: Keep users informed with timely, clear feedback (loading, success, errors, progress).
- **Findings**:
  - Import: Good progress and validation feedback; could add determinate progress during parse.
  - Login: Has inline loading state; add visible error region with aria-live.
  - Dashboard/Employees: Actions succeed silently (e.g., add employee/trip); toast confirmations would help.
  - Trips: Loading spinners exist; add inline skeletons for calendar grid and employee list.
- **Low-effort fixes**:
  - Add Bootstrap toasts with aria-live="polite" for create/update/delete.
  - Add skeletons/spinners to `.table-container`, calendar rows, search dropdowns.
  - Add success banners after form posts that disappear after 3–5s.
- **Scores**: Login 4, Dashboard 4, Employees 4, Trips 3, Import 4, Forecast 4, Admin 3

### 2) Match between system and the real world
- **Meaning**: Use users’ language; align with compliance domain concepts.
- **Findings**:
  - Terms are mostly clear but some instances need refinement (e.g., “Days Remaining” vs “Days Available”).
  - Calendar splash copy is informal with typos; should be professional in an HR compliance tool.
    Code reference (Trips):
```392:405:/Users/jameswalsh/Desktop/Dev/Web Projects/ComplyEur/ComplyEur v1.0.0/app/templates/calendar.html
Hello Friend,

Thank you for choosing my app as a possible solution to your EES headache,

I hope you enjoy the app and feel free to look arounf around and let me know if you find anything that looks wierd or buggy.

This calander wil be a masterpice IMO when finished, however, right now tho its not finished. but it will be soon. 

Your friend 



Walshy
```
- **Low-effort fixes**:
  - Replace splash text with concise, professional message and correct spelling.
  - Standardise wording: “Days available in last 180 days”, “Compliant from”, “Non‑Schengen (IE)”.
  - Add short tooltips for “90/180” on key pages.
- **Scores**: Login 4, Dashboard 3, Employees 3, Trips 2, Import 4, Forecast 4, Admin 4

### 3) User control and freedom
- **Meaning**: Provide safe exits (cancel/undo), avoid traps.
- **Findings**:
  - Employees: Trip add form has Cancel and unsaved changes warning — good.
  - Import: Has Cancel in preview — good; could allow “Undo last import” link after success.
  - Admin tools: Destructive actions use confirm() or alerts; standardise to modal with secondary style and keyboard support.
- **Low-effort fixes**:
  - Use consistent Bootstrap modals with clear primary/secondary.
  - Provide “Undo” toast after bulk or destructive actions when feasible.
  - Support ESC and focus trapping in all custom modals.
- **Scores**: Login 4, Dashboard 4, Employees 4, Trips 3, Import 4, Forecast 4, Admin 3

### 4) Consistency and standards
- **Meaning**: Consistent patterns, labels, colours, and components.
- **Findings**:
  - Inline styles used widely; prefer Bootstrap utility classes.
  - Badges and button colours vary slightly across pages.
  - Date format appears as DD‑MM‑YYYY; ensure single format across all pages and CSV.
- **Low-effort fixes**:
  - Move repeated inline styles to CSS, reuse `.badge-*`, `.btn-*`, `.alert-*`.
  - Create a Mini Design Tokens section in `components.css` for status colours (green/amber/red) and apply globally.
  - Enforce `DD/MM/YYYY` (UK), with helper filter and input placeholders.
- **Scores**: Login 4, Dashboard 3, Employees 3, Trips 3, Import 4, Forecast 4, Admin 3

### 5) Error prevention
- **Meaning**: Prevent problems before they occur.
- **Findings**:
  - Employees: Strong date range checks; duplicate trip prevention not evident.
  - Import: Good file/type checks; consider pre-flight duplicate detection and row-level preview warnings.
  - Admin DSAR: Guard irreversible actions with typed confirmation; already used in settings modal, but not everywhere.
- **Low-effort fixes**:
  - Add duplicate detection on trip create (same employee, country, overlapping dates).
  - Add inline “Are you sure?” with typed phrase for purge/delete everywhere destructive.
  - Disable submit until required fields valid; add `required` + pattern on country selectors.
- **Scores**: Login 4, Dashboard 3, Employees 3, Trips 3, Import 4, Forecast 4, Admin 3

### 6) Recognition rather than recall
- **Meaning**: Show options; reduce memory load.
- **Findings**:
  - Dashboard has search + filters; good. Employees shows key metrics; good.
  - Calendar needs inline legends near rows; already present, but can pin legend.
  - Settings modal is discoverable via top-right — good; add breadcrumb hints on pages.
- **Low-effort fixes**:
  - Keep critical stats in table view headers; pin the legend on scroll.
  - Show “Safe entry” hint consistently in both table and card views.
  - Add helper text under date pickers (DD/MM/YYYY) and country dropdowns.
- **Scores**: Login 5, Dashboard 4, Employees 3, Trips 3, Import 4, Forecast 4, Admin 3

### 7) Flexibility and efficiency of use
- **Meaning**: Shortcuts and accelerators for expert users while staying simple for novices.
- **Findings**:
  - Keyboard support present for search; add more (modal close, focus cycling).
  - Bulk add trip helps efficiency; add saved presets for common countries/durations.
  - Calendar/timeline could add keyboard navigation across days/weeks.
- **Low-effort fixes**:
  - Add accesskeys and arrow-key support in calendar navigation.
  - Save last used country/dates per session; prefill.
  - Provide “duplicate last trip” or “clone” action from detail.
- **Scores**: Login 3, Dashboard 4, Employees 3, Trips 3, Import 4, Forecast 4, Admin 3

### 8) Aesthetic and minimalist design
- **Meaning**: Minimal clutter; clear hierarchy; purposeful colour use.
- **Findings**:
  - Overall clean; occasional verbose banners and inline styles.
  - Calendar splash is wordy and informal; reduces perceived quality.
  - Some cards border/shadow combinations are heavy.
- **Low-effort fixes**:
  - Replace splash with one-paragraph professional note or remove entirely.
  - Use Bootstrap spacing utilities; reduce inline gradients and shadows.
  - Standardise headers (H1/H2) scale and spacing.
- **Scores**: Login 5, Dashboard 3, Employees 3, Trips 2, Import 4, Forecast 4, Admin 4

### 9) Help users recognise, diagnose, and recover from errors
- **Meaning**: Clear, human error messages and how to fix them.
- **Findings**:
  - Import and Employees provide decent messages; unify style.
  - Admin uses alert() in places; replace with inline alerts.
  - Calendar error state is present; add retry + diagnostics consistently.
- **Low-effort fixes**:
  - Use a shared alert component with titles, causes, fixes, and links.
  - Add field-level errors below inputs with `.invalid-feedback` and `aria-describedby`.
  - Replace `alert()` with Bootstrap alerts/toasts.
- **Scores**: Login 3, Dashboard 3, Employees 4, Trips 3, Import 4, Forecast 4, Admin 3

### 10) Help and documentation
- **Meaning**: Provide help where needed (contextual, concise).
- **Findings**:
  - Help link exists in menu; add page-specific “?” helpers.
  - Short glossary for Schengen/Non‑Schengen, 90/180 would aid new admins.
  - Calendar/Forecast need brief inline explanations of badges and thresholds.
- **Low-effort fixes**:
  - Add inline “i” tooltips to key labels (Days Used, Days Remaining, Risk).
  - Add a single Help drawer linking to `ENTRY_REQUIREMENTS_*` docs.
  - Add onboarding checklist on first dashboard load.
- **Scores**: Login 2, Dashboard 3, Employees 2, Trips 2, Import 3, Forecast 3, Admin 3

---

### Final summary table (scores and fixes)

| Page | Heuristic | Score | Recommended fixes (low-effort) |
|---|---|---:|---|
| Login | 1. Visibility | 4 | Add aria-live success/error; spinner on submit; “Show password” toggle |
| Login | 2. Match | 4 | Clarify “Admin password”; keep copy concise |
| Login | 3. Control | 4 | Allow ESC to clear field; keep focus on errors |
| Login | 4. Consistency | 4 | Use `.btn-primary` only; standardise title/subtitle spacing |
| Login | 5. Prevention | 4 | Enforce min length 8; password strength hint text |
| Login | 6. Recognition | 5 | Keep hints visible; placeholder shows expectations |
| Login | 7. Efficiency | 3 | Support Enter submit; add keyboard focus outline |
| Login | 8. Minimalist | 5 | Keep clean layout; remove inline styles |
| Login | 9. Error recovery | 3 | Inline `.invalid-feedback` under field |
| Login | 10. Help | 2 | Add “Forgot/reset password” link and help tip |
| Dashboard | 1. Visibility | 4 | Toast on add employee; loading states in table |
| Dashboard | 2. Match | 3 | Use “Days available” wording; clarify badges |
| Dashboard | 3. Control | 4 | Add undo toast for quick actions |
| Dashboard | 4. Consistency | 3 | Unify badge colours; replace inline styles with classes |
| Dashboard | 5. Prevention | 3 | Prevent duplicate employees; validate min length |
| Dashboard | 6. Recognition | 4 | Pin legend; maintain column tooltips |
| Dashboard | 7. Efficiency | 4 | Keyboard sorting; remember view preference |
| Dashboard | 8. Minimalist | 3 | Reduce gradient cards; simplify stat tiles |
| Dashboard | 9. Error recovery | 3 | Use consistent alert/toast component |
| Dashboard | 10. Help | 3 | Add “i” tooltips on metrics and badges |
| Employees | 1. Visibility | 4 | Success toast on add/edit/delete trip |
| Employees | 2. Match | 3 | Clarify “Personal Trip (dates only)” label |
| Employees | 3. Control | 4 | Keep Cancel + unsaved warnings (good) |
| Employees | 4. Consistency | 3 | Use consistent badge text and colours |
| Employees | 5. Prevention | 3 | Detect overlapping/duplicate trips before submit |
| Employees | 6. Recognition | 3 | Show safe re-entry consistently (table/card) |
| Employees | 7. Efficiency | 3 | Quick-fill last country/dates; clone trip |
| Employees | 8. Minimalist | 3 | Move inline CSS to classes; simplify dropdown |
| Employees | 9. Error recovery | 4 | Improve field-level feedback; keep override rationale |
| Employees | 10. Help | 2 | Add tooltip for 90/180 and Non‑Schengen |
| Trips | 1. Visibility | 3 | Add skeletons; loading markers in grid |
| Trips | 2. Match | 2 | Replace informal splash with professional copy |
| Trips | 3. Control | 3 | ESC closes panels; clear selection button |
| Trips | 4. Consistency | 3 | Standardise control labels; reuse buttons |
| Trips | 5. Prevention | 3 | Confirm on destructive actions; typed confirm |
| Trips | 6. Recognition | 3 | Pin legend; show employee summary on hover |
| Trips | 7. Efficiency | 3 | Arrow key navigation; “Today” focus hotkey |
| Trips | 8. Minimalist | 2 | Remove verbose splash; reduce visual noise |
| Trips | 9. Error recovery | 3 | Inline retry for calendar load failure |
| Trips | 10. Help | 2 | “?” tooltips for badges, thresholds |
| Import | 1. Visibility | 4 | Determinate progress during parse if possible |
| Import | 2. Match | 4 | Keep domain language; short hints ok |
| Import | 3. Control | 4 | Keep Cancel/Back; link to template |
| Import | 4. Consistency | 4 | Reuse table and alert styles |
| Import | 5. Prevention | 4 | Preview duplicates and invalid rows |
| Import | 6. Recognition | 4 | Show column expectations inline |
| Import | 7. Efficiency | 4 | Remember last chosen file dir; keyboard submit |
| Import | 8. Minimalist | 4 | Keep concise; remove inline sizing |
| Import | 9. Error recovery | 4 | Row-level error list with fixes |
| Import | 10. Help | 3 | Link to CSV template and sample |
| Forecast | 1. Visibility | 4 | Keep risk badges; timestamp updates |
| Forecast | 2. Match | 4 | Explain thresholds in subtitle |
| Forecast | 3. Control | 4 | Filters with clear; Back to employee |
| Forecast | 4. Consistency | 4 | Align badges with dashboard |
| Forecast | 5. Prevention | 4 | Warn when job exceeds 90 days |
| Forecast | 6. Recognition | 4 | Inline legend and glossary link |
| Forecast | 7. Efficiency | 4 | Sort/filters persist in URL |
| Forecast | 8. Minimalist | 4 | Light table; readable spacing |
| Forecast | 9. Error recovery | 4 | Empty state guidance |
| Forecast | 10. Help | 3 | Add “How forecasting works” link |
| Admin | 1. Visibility | 3 | Success toasts after DSAR actions |
| Admin | 2. Match | 4 | Clear GDPR wording; concise |
| Admin | 3. Control | 3 | Replace alert() with modals; ESC, focus trap |
| Admin | 4. Consistency | 3 | Standardise all destructive buttons |
| Admin | 5. Prevention | 3 | Typed confirm + danger styling everywhere |
| Admin | 6. Recognition | 3 | Label form controls with hints |
| Admin | 7. Efficiency | 3 | Quick search employee; keyboard nav |
| Admin | 8. Minimalist | 4 | Keep modal tidy; remove inline widths |
| Admin | 9. Error recovery | 3 | Inline errors under fields; no alert() |
| Admin | 10. Help | 3 | Link to privacy policy and DSAR guide |

---

### Quick, low-risk implementation checklist (1–2 hours total)
- Replace calendar splash text with professional, concise copy; fix typos.
- Add a shared Bootstrap toast utility and call it on success/failure across forms and bulk actions.
- Standardise status colours in `components.css` and remove inline colour styles; apply to badges and progress bars.
- Add `.invalid-feedback` blocks and `aria-describedby` for all form fields with validation.
- Pin legends on calendar/timeline; add keyboard support (ESC closes panels, arrow keys navigate).
- Add duplicate trip detection before submission (same employee + overlapping dates) with inline warning and “Add anyway with reason”.

### Notable code references informing recommendations
- Calendar splash copy requires professionalisation:
```388:405:/Users/jameswalsh/Desktop/Dev/Web Projects/ComplyEur/ComplyEur v1.0.0/app/templates/calendar.html
<div style="width:100%;white-space:pre-wrap;line-height:1.5">
Hello Friend,
...
Walshy
</div>
```
- Strong existing patterns to reuse:
  - Import progress and validation: `import_excel.html` (deterministic progress container and file checks)
  - Employee trip form safety: `employee_detail.html` (date range validation, cancel, unsaved warning)

---

### Overall appraisal
- **Average compliance** (approx): Login 3.8, Dashboard 3.5, Employees 3.4, Trips 2.8, Import 3.9, Forecast 3.9, Admin 3.3.
- **Top wins**: Add toasts, unify colours/components, professionalise copy in Calendar, small accessibility boosts (aria-live, invalid-feedback, keyboard support).
- These changes are low-risk, align with Bootstrap 5, and improve clarity and trust for HR compliance use.



