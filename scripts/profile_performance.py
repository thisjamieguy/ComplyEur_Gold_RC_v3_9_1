#!/usr/bin/env python3
"""
Performance profiling script for ComplyEur.

Measures and profiles database query performance, response times, and identifies bottlenecks.

Usage:
    python scripts/profile_performance.py
"""

import cProfile
import pstats
import time
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from app.models import get_db, Employee

def profile_dashboard():
    """Profile dashboard route performance."""
    app = create_app()
    
    with app.app_context():
        conn = get_db()
        c = conn.cursor()
        
        print("=" * 60)
        print("Dashboard Performance Profiling")
        print("=" * 60)
        
        # Measure employee query performance
        start = time.time()
        c.execute('SELECT id, name FROM employees ORDER BY name')
        employees = c.fetchall()
        employee_query_time = time.time() - start
        
        print(f"\n📊 Employee Query Performance:")
        print(f"   Query time: {employee_query_time*1000:.2f}ms")
        print(f"   Employees fetched: {len(employees)}")
        
        if not employees:
            print("\n⚠️  No employees found in database. Run with test data first.")
            return
        
        # Measure batch trip query performance
        employee_ids = [emp['id'] for emp in employees]
        placeholders = ','.join('?' * len(employee_ids))
        
        start = time.time()
        c.execute(f'''
            SELECT 
                employee_id,
                entry_date,
                exit_date,
                country,
                is_private
            FROM trips
            WHERE employee_id IN ({placeholders})
            ORDER BY employee_id, entry_date DESC
        ''', employee_ids)
        all_trips = c.fetchall()
        batch_query_time = time.time() - start
        
        print(f"\n📊 Batch Trip Query Performance:")
        print(f"   Query time: {batch_query_time*1000:.2f}ms")
        print(f"   Total trips fetched: {len(all_trips)}")
        print(f"   Average trips per employee: {len(all_trips)/len(employees):.1f}")
        
        # Group trips by employee
        trips_by_employee = {}
        for trip in all_trips:
            emp_id = trip['employee_id']
            if emp_id not in trips_by_employee:
                trips_by_employee[emp_id] = []
            trips_by_employee[emp_id].append(dict(trip))
        
        # Measure compliance calculation performance
        from app.services.rolling90 import presence_days, days_used_in_window, calculate_days_remaining
        from datetime import date
        today = date.today()
        
        calc_start = time.time()
        calculations_completed = 0
        for emp in employees:
            emp_id = emp['id']
            trips = trips_by_employee.get(emp_id, [])
            if trips:
                presence = presence_days(trips)
                days_used = days_used_in_window(presence, today)
                days_remaining = calculate_days_remaining(presence, today)
                calculations_completed += 1
        calc_time = time.time() - calc_start
        
        print(f"\n📊 Compliance Calculation Performance:")
        print(f"   Calculation time: {calc_time*1000:.2f}ms")
        print(f"   Employees processed: {calculations_completed}")
        print(f"   Average time per employee: {(calc_time/calculations_completed)*1000:.2f}ms")
        
        # Total performance
        total_time = employee_query_time + batch_query_time + calc_time
        print(f"\n📊 Total Dashboard Performance:")
        print(f"   Total time: {total_time*1000:.2f}ms")
        print(f"   Queries executed: 2 (employee query + batch trip query)")
        print(f"   Query efficiency: {len(employees)/2:.1f} employees per query")
        
        # Performance recommendations
        print(f"\n💡 Performance Recommendations:")
        if total_time > 0.5:
            print(f"   ⚠️  Dashboard load time > 500ms - consider caching")
        if len(employees) > 50 and total_time > 0.2:
            print(f"   ⚠️  Large employee count - consider pagination or lazy loading")
        if batch_query_time > 0.1:
            print(f"   ⚠️  Batch query > 100ms - check database indexes")
        
        print("=" * 60)

def profile_query_plans():
    """Analyze query execution plans."""
    app = create_app()
    
    with app.app_context():
        conn = get_db()
        c = conn.cursor()
        
        print("\n" + "=" * 60)
        print("Query Execution Plan Analysis")
        print("=" * 60)
        
        # Analyze employee query
        print("\n📋 Employee Query Plan:")
        c.execute('EXPLAIN QUERY PLAN SELECT id, name FROM employees ORDER BY name')
        plan = c.fetchall()
        for row in plan:
            print(f"   {dict(row)}")
        
        # Analyze trip query
        print("\n📋 Trip Query Plan (for employee_id = 1):")
        c.execute('EXPLAIN QUERY PLAN SELECT * FROM trips WHERE employee_id = 1 ORDER BY entry_date DESC')
        plan = c.fetchall()
        for row in plan:
            print(f"   {dict(row)}")
        
        # Check indexes
        print("\n📋 Database Indexes:")
        c.execute("SELECT name FROM sqlite_master WHERE type='index' AND name LIKE 'idx_%'")
        indexes = c.fetchall()
        for idx in indexes:
            print(f"   ✅ {idx['name']}")
        
        print("=" * 60)

if __name__ == '__main__':
    print("\n🚀 Starting Performance Profiling...\n")
    
    # Run profiling with cProfile
    profiler = cProfile.Profile()
    profiler.enable()
    
    try:
        profile_dashboard()
        profile_query_plans()
    except Exception as e:
        print(f"\n❌ Error during profiling: {e}")
        import traceback
        traceback.print_exc()
    
    profiler.disable()
    
    # Print profiling stats
    print("\n" + "=" * 60)
    print("Detailed Function Call Statistics")
    print("=" * 60)
    stats = pstats.Stats(profiler)
    stats.sort_stats('cumulative')
    stats.print_stats(20)
    
    print("\n✅ Profiling complete!")

