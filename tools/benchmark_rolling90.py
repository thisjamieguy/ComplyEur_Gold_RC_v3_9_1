import random
import time
from datetime import date, timedelta

# Local import of rolling90
from app.services.rolling90 import presence_days, days_used_in_window


def generate_trips(num_trips: int, max_span_days: int = 14, start_year: int = 2023):
    """Generate synthetic trips for benchmarking.

    - Trips are within ~2 years from start_year
    - Countries alternate (IE excluded half the time to simulate filtering)
    """
    trips = []
    base = date(start_year, 1, 1)
    for i in range(num_trips):
        offset = random.randint(0, 720)
        span = random.randint(1, max_span_days)
        entry = base + timedelta(days=offset)
        exit_d = entry + timedelta(days=span)
        # Alternate between Schengen and IE to simulate realistic mix
        country = "IE" if (i % 5 == 0) else "FR"
        trips.append({
            "entry_date": entry.isoformat(),
            "exit_date": exit_d.isoformat(),
            "country": country,
        })
    return trips


def time_call(fn, *args, repeat: int = 3, warmups: int = 1):
    # Warmups
    for _ in range(warmups):
        fn(*args)
    # Timed runs
    durations = []
    for _ in range(repeat):
        t0 = time.perf_counter()
        fn(*args)
        durations.append((time.perf_counter() - t0) * 1000.0)
    return sum(durations) / len(durations)


def main():
    random.seed(42)

    sizes = [50, 200, 1000]
    print("ComplyEur rolling90 benchmark (ms)")
    print("size\tpresence(cold)\tpresence(warm)\tdays_used(cold)\tdays_used(warm)")

    for n in sizes:
        trips = generate_trips(n)

        # presence_days: cold (first) and warm (cached) timings
        # Cold: use a fresh list copy to avoid hitting cache key equality by ref
        cold_ms = time_call(presence_days, list(trips), repeat=5, warmups=0)
        warm_ms = time_call(presence_days, trips, repeat=10, warmups=3)
        presence = presence_days(trips)

        # days_used_in_window timings
        today = date.today()
        cold_du = time_call(days_used_in_window, set(presence), today, repeat=20, warmups=0)
        warm_du = time_call(days_used_in_window, presence, today, repeat=50, warmups=10)

        print(f"{n}\t{cold_ms:.2f}\t\t{warm_ms:.2f}\t\t{cold_du:.2f}\t\t{warm_du:.2f}")


if __name__ == "__main__":
    main()



