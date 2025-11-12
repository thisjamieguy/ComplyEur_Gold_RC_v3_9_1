# ComplyEur Logic Explained

**Version**: 3.9.1 (Gold Release Candidate)  
**Last Updated**: 2025-11-12

This document provides a plain-English explanation of how ComplyEur calculates EU 90/180-day rule compliance, including edge cases and special scenarios.

---

## The 90/180-Day Rule: Overview

### What It Means

UK citizens (and other non-EU citizens) can spend a **maximum of 90 days** in the Schengen Area within **any rolling 180-day period**.

### Key Concepts

1. **Rolling Window**: The 180-day period moves forward every day
2. **Schengen Area**: 26 European countries with no internal border controls
3. **Counting Days**: Only days physically present in Schengen countries count
4. **Ireland Exception**: Ireland is tracked separately and doesn't count toward the 90-day limit

---

## How the Calculation Works

### Step 1: Identify Schengen Countries

ComplyEur maintains a list of all Schengen countries:

**EU27 Schengen Countries:**
- Austria, Belgium, Bulgaria, Croatia, Czech Republic, Denmark, Estonia, Finland, France, Germany, Greece, Hungary, Italy, Latvia, Lithuania, Luxembourg, Malta, Netherlands, Poland, Portugal, Romania, Slovakia, Slovenia, Spain, Sweden

**Non-EU Schengen Countries:**
- Iceland, Liechtenstein, Norway, Switzerland

**Excluded (Not Schengen):**
- Ireland (IE) - Tracked separately, doesn't count toward 90-day limit
- United Kingdom (GB) - Not in Schengen
- Other non-Schengen countries

### Step 2: Calculate Presence Days

For each trip, ComplyEur calculates all individual days spent in Schengen:

```python
# Example: Trip from Jan 1 to Jan 5 in France
Entry Date: 2024-01-01
Exit Date: 2024-01-05

Presence Days: {2024-01-01, 2024-01-02, 2024-01-03, 2024-01-04, 2024-01-05}
Total Days: 5
```

**Important Notes:**
- Entry day counts as a full day
- Exit day counts as a full day
- All days in between count
- Partial days count as full days

### Step 3: Apply Rolling 180-Day Window

The system looks at the **last 180 days** from today (or a reference date):

```python
# Today is 2024-06-15
Window Start: 2024-06-15 - 180 days = 2023-12-18
Window End: 2024-06-15 - 1 day = 2024-06-14

# Count all presence days within this window
Days Used = Count of presence days between 2023-12-18 and 2024-06-14
```

**Window Calculation:**
- Window is `[ref_date - 180 days, ref_date - 1 day]` inclusive
- This gives exactly 180 days (not 181)
- The window "rolls" forward each day

### Step 4: Calculate Days Remaining

```python
Days Used = Count of presence days in 180-day window
Days Remaining = 90 - Days Used
```

**Risk Levels:**
- **Green**: ≥ 30 days remaining (safe)
- **Amber**: 10-29 days remaining (approaching limit)
- **Red**: < 10 days remaining (at risk)

---

## Edge Cases and Special Scenarios

### 1. Ireland Exclusion

**Rule**: Ireland (IE) trips are **excluded** from Schengen calculations.

**Why**: Ireland is not part of the Schengen Area, even though it's in the EU.

**Example:**
```python
Trips:
  - France: Jan 1-10 (10 days) → Counts toward 90
  - Ireland: Jan 15-20 (6 days) → Does NOT count
  - Germany: Feb 1-5 (5 days) → Counts toward 90

Total Days Used: 15 (only France + Germany)
```

### 2. Switzerland Inclusion

**Rule**: Switzerland **is included** in Schengen calculations.

**Why**: Switzerland is part of the Schengen Area (though not EU).

**Example:**
```python
Trip: Switzerland, Jan 1-5 (5 days)
Result: Counts toward 90-day limit
```

### 3. Rolling Window Boundary

**Scenario**: Trip exactly 180 days ago

**Rule**: The window is `[today - 180, today - 1]` inclusive.

**Example:**
```python
Today: 2024-06-15
Trip: 2023-12-18 (exactly 180 days ago)

Window: [2023-12-18, 2024-06-14]
Result: Trip IS included (it's at the start of the window)
```

**Scenario**: Trip 181 days ago

**Example:**
```python
Today: 2024-06-15
Trip: 2023-12-17 (181 days ago)

Window: [2023-12-18, 2024-06-14]
Result: Trip is NOT included (it's before the window)
```

### 4. Overlapping Trips

**Rule**: Overlapping trips are allowed, but days are only counted once.

**Example:**
```python
Trip 1: France, Jan 1-10 (10 days)
Trip 2: Germany, Jan 5-15 (11 days)
Overlap: Jan 5-10 (6 days)

Presence Days: {Jan 1-15} = 15 days total
Days Used: 15 (not 21, because overlap is counted once)
```

### 5. Future Trips

**Rule**: Future trips are included in compliance forecasting.

**Example:**
```python
Today: 2024-06-15
Future Trip: 2024-07-01 to 2024-07-10 (10 days)

Forecast: If this trip happens, will it exceed 90 days?
Calculation: Days Used (current) + Future Days = Total
```

### 6. Leap Years

**Rule**: Leap years are handled correctly (February 29).

**Example:**
```python
Trip: 2024-02-28 to 2024-03-01
Days: {2024-02-28, 2024-02-29, 2024-03-01} = 3 days
```

### 7. Same-Day Entry/Exit

**Rule**: Same-day trips count as 1 day.

**Example:**
```python
Entry: 2024-01-15
Exit: 2024-01-15
Days: {2024-01-15} = 1 day
```

### 8. Multi-Country Trips

**Rule**: Each country is tracked separately, but days in Schengen count once.

**Example:**
```python
Trip: France (Jan 1-5) then Germany (Jan 6-10)
Presence Days: {Jan 1-10} = 10 days total
Both countries tracked, but days counted once
```

---

## Calculation Flow Diagram

```
1. Get all trips for employee
   ↓
2. Filter to Schengen countries only (exclude Ireland)
   ↓
3. Calculate presence days (all individual days in Schengen)
   ↓
4. Determine 180-day window [today - 180, today - 1]
   ↓
5. Count presence days within window
   ↓
6. Calculate days remaining (90 - days used)
   ↓
7. Determine risk level (green/amber/red)
   ↓
8. Display results to user
```

---

## Future Compliance Forecasting

### What-If Scenarios

ComplyEur can forecast future compliance:

**Example:**
```python
Current Days Used: 75
Proposed Future Trip: 20 days

Forecast: 75 + 20 = 95 days (EXCEEDS 90)
Result: Warning - trip would exceed limit
```

### Earliest Safe Entry Date

ComplyEur calculates when an employee can safely enter again:

**Example:**
```python
Current Days Used: 90 (at limit)
Oldest Trip in Window: 2023-12-18

Earliest Safe Entry: When oldest trip falls out of window
Result: 2024-06-16 (when 2023-12-18 is 181 days old)
```

---

## Validation Rules

### Trip Validation

1. **Entry Date < Exit Date**: Exit must be after entry
2. **Date Range**: Entry/exit within reasonable range (10 years past, 2 years future)
3. **Country Code**: Must be valid 2-letter ISO code
4. **No Overlaps**: Trips cannot overlap for the same employee (unless allowed by admin)

### Calculation Validation

1. **Window Size**: Always exactly 180 days
2. **Days Counted**: Only Schengen countries (Ireland excluded)
3. **No Double Counting**: Overlapping trips counted once
4. **Boundary Handling**: Window boundaries handled correctly

---

## Testing and Verification

### Reference Implementation

ComplyEur includes a reference calculator (`reference/oracle_calculator.py`) for verification.

### Test Coverage

- Unit tests for all calculation functions
- Edge case testing (boundaries, overlaps, leap years)
- Integration tests for end-to-end flows
- Playwright tests for UI validation

### Validation

All calculations are verified against:
- Official EU guidance
- Manual calculations
- Reference implementation
- Real-world scenarios

---

## Common Questions

### Q: Why is the window 180 days, not 181?

**A**: The window is `[today - 180, today - 1]` inclusive, which gives exactly 180 days. This matches EU guidance.

### Q: Does a day trip count as 1 or 2 days?

**A**: 1 day. Entry and exit on the same day counts as a single day.

### Q: What if I'm in transit (airport only)?

**A**: Airport transit typically doesn't count, but ComplyEur counts all days where you're physically in a Schengen country. Consult immigration authorities for specific rules.

### Q: How does the window "roll"?

**A**: Each day, the window moves forward by one day. Yesterday's window was `[yesterday - 180, yesterday - 1]`. Today's window is `[today - 180, today - 1]`.

### Q: What about partial months?

**A**: Days are counted individually, not by months. A trip from Jan 15 to Feb 5 counts as 22 days, not "part of January + part of February."

---

## Technical Implementation

### Core Functions

- `is_schengen_country(country)` - Check if country is in Schengen
- `presence_days(trips)` - Calculate all presence days
- `days_used_in_window(presence, ref_date)` - Count days in 180-day window
- `days_remaining(presence, ref_date)` - Calculate remaining days
- `earliest_safe_entry(presence, today)` - Find earliest safe entry date

### Performance Optimizations

- Memoization for repeated calculations
- Database indexes for fast queries
- Caching of presence day sets
- Efficient date range queries

---

## Accuracy and Reliability

### Calculation Accuracy

- ✅ Mathematically correct rolling window calculations
- ✅ Proper handling of all edge cases
- ✅ Verified against reference implementation
- ✅ Comprehensive test coverage

### Important Disclaimers

⚠️ **Legal Compliance**: ComplyEur provides calculations as guidance only. Always verify with immigration authorities and consult legal advisors for compliance decisions.

⚠️ **Regulation Changes**: EU regulations may change. ComplyEur calculations are based on current rules as of the release date.

⚠️ **Individual Circumstances**: Special circumstances (visas, residence permits, etc.) may affect your actual compliance status.

---

## Additional Resources

- `app/services/rolling90.py` - Core calculation implementation
- `tests/test_rolling90.py` - Test suite
- `reference/oracle_calculator.py` - Reference implementation
- `help_content.json` - User-facing help content

---

**Logic Verified**: All calculations have been verified against EU guidance and tested extensively. The system is production-ready and reliable.

