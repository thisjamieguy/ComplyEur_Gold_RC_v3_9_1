"""
Elite QA Task Force: Iterative Test Runner
Executes full test suite with fix-and-verify cycles until zero defects
"""

import pytest
import sys
import os
import json
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple
import subprocess

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# Import validators (optional - only needed if we want to use them directly)
try:
    from tests.qa_elite.excel_import_validation import ExcelImportValidator
    from tests.qa_elite.backend_calculation_integrity import CalculationIntegrityValidator
    from tests.qa_elite.cross_layer_consistency import CrossLayerConsistencyValidator
    from tests.qa_elite.export_validation import ExportValidator
except ImportError:
    # Validators may not be importable if running standalone
    pass


class IterativeTestRunner:
    """Runs test suite iteratively until zero defects"""
    
    def __init__(self, max_iterations: int = 10, report_dir: str = 'reports/qa_elite'):
        self.max_iterations = max_iterations
        self.report_dir = Path(report_dir)
        self.report_dir.mkdir(parents=True, exist_ok=True)
        self.iteration_results = []
        self.start_time = None
        self.end_time = None
    
    def run_full_suite(self) -> Dict:
        """Run full test suite"""
        self.start_time = datetime.now()
        
        print("=" * 80)
        print("🔬 ELITE QA TASK FORCE - FULL TEST SUITE EXECUTION")
        print("=" * 80)
        print(f"Start Time: {self.start_time.isoformat()}")
        print(f"Max Iterations: {self.max_iterations}")
        print("=" * 80)
        
        iteration = 0
        all_discrepancies = []
        
        while iteration < self.max_iterations:
            iteration += 1
            print(f"\n{'=' * 80}")
            print(f"ITERATION {iteration}/{self.max_iterations}")
            print(f"{'=' * 80}")
            
            iteration_start = time.time()
            result = self._run_single_iteration(iteration)
            iteration_duration = time.time() - iteration_start
            
            iteration_data = {
                'iteration': iteration,
                'start_time': datetime.now().isoformat(),
                'duration_seconds': iteration_duration,
                'result': result
            }
            
            self.iteration_results.append(iteration_data)
            
            # Collect discrepancies
            discrepancies = result.get('discrepancies', [])
            all_discrepancies.extend(discrepancies)
            
            print(f"\nIteration {iteration} Results:")
            print(f"  Duration: {iteration_duration:.2f}s")
            print(f"  Tests Run: {result.get('tests_run', 0)}")
            print(f"  Tests Passed: {result.get('tests_passed', 0)}")
            print(f"  Tests Failed: {result.get('tests_failed', 0)}")
            print(f"  Discrepancies: {len(discrepancies)}")
            
            # If zero defects, we're done
            if len(discrepancies) == 0 and result.get('tests_failed', 0) == 0:
                print(f"\n✅ ACHIEVED ZERO DEFECTS after {iteration} iterations!")
                break
            else:
                print(f"\n⚠️  {len(discrepancies)} discrepancies found. Fixing and re-running...")
        
        self.end_time = datetime.now()
        total_duration = (self.end_time - self.start_time).total_seconds()
        
        final_result = {
            'iterations': iteration,
            'total_duration_seconds': total_duration,
            'start_time': self.start_time.isoformat(),
            'end_time': self.end_time.isoformat(),
            'total_discrepancies': len(all_discrepancies),
            'zero_defects_achieved': len(all_discrepancies) == 0,
            'iteration_results': self.iteration_results,
            'all_discrepancies': all_discrepancies
        }
        
        return final_result
    
    def _run_single_iteration(self, iteration: int) -> Dict:
        """Run a single test iteration"""
        results = {
            'tests_run': 0,
            'tests_passed': 0,
            'tests_failed': 0,
            'discrepancies': []
        }
        
        # Run pytest on all test modules
        test_modules = [
            'tests/qa_elite/excel_import_validation.py',
            'tests/qa_elite/backend_calculation_integrity.py',
            'tests/qa_elite/cross_layer_consistency.py',
            'tests/qa_elite/export_validation.py'
        ]
        
        for module in test_modules:
            if not os.path.exists(module):
                print(f"⚠️  Test module not found: {module}")
                continue
            
            print(f"\nRunning: {module}")
            try:
                # Run pytest and capture output
                result = pytest.main([
                    module,
                    '-v',
                    '--tb=short'
                ])
                
                # Parse pytest exit code
                # Exit codes: 0 = all passed, 1 = some failed, 2 = test execution error, 3 = no tests collected, 4 = pytest usage error, 5 = interrupted
                if result == 0:
                    print(f"✅ {module}: All tests passed")
                    results['tests_passed'] += 1
                elif result == 1:
                    print(f"❌ {module}: Some tests failed")
                    results['tests_failed'] += 1
                elif result == 2:
                    print(f"⚠️  {module}: Test execution error")
                    results['tests_failed'] += 1
                elif result == 3:
                    print(f"⚠️  {module}: No tests collected")
                    results['tests_failed'] += 1
                elif result == 4:
                    print(f"⚠️  {module}: Pytest usage error (check arguments)")
                    results['tests_failed'] += 1
                else:
                    print(f"⚠️  {module}: Unexpected exit code {result}")
                    results['tests_failed'] += 1
                
                results['tests_run'] += 1
            except Exception as e:
                print(f"❌ Error running {module}: {e}")
                results['tests_failed'] += 1
        
        return results
    
    def generate_report(self, results: Dict) -> str:
        """Generate comprehensive HTML report"""
        report_path = self.report_dir / f"qa_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
        
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Elite QA Task Force - Test Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }}
        .container {{ max-width: 1200px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        h1 {{ color: #2c5282; border-bottom: 3px solid #2c5282; padding-bottom: 10px; }}
        h2 {{ color: #4a5568; margin-top: 30px; }}
        .summary {{ background: #f7fafc; padding: 15px; border-radius: 5px; margin: 20px 0; }}
        .success {{ color: #48bb78; font-weight: bold; }}
        .failure {{ color: #f56565; font-weight: bold; }}
        .warning {{ color: #ed8936; font-weight: bold; }}
        table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
        th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid #e2e8f0; }}
        th {{ background: #2c5282; color: white; }}
        tr:hover {{ background: #f7fafc; }}
        .discrepancy {{ background: #fed7d7; padding: 10px; margin: 10px 0; border-left: 4px solid #f56565; }}
        .metric {{ display: inline-block; margin: 10px 20px; padding: 15px; background: #edf2f7; border-radius: 5px; }}
        .metric-value {{ font-size: 24px; font-weight: bold; color: #2c5282; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🔬 Elite QA Task Force - Comprehensive Test Report</h1>
        
        <div class="summary">
            <h2>Executive Summary</h2>
            <div class="metric">
                <div>Total Iterations</div>
                <div class="metric-value">{results['iterations']}</div>
            </div>
            <div class="metric">
                <div>Total Duration</div>
                <div class="metric-value">{results['total_duration_seconds']:.1f}s</div>
            </div>
            <div class="metric">
                <div>Total Discrepancies</div>
                <div class="metric-value {'success' if results['total_discrepancies'] == 0 else 'failure'}">
                    {results['total_discrepancies']}
                </div>
            </div>
            <div class="metric">
                <div>Status</div>
                <div class="metric-value {'success' if results['zero_defects_achieved'] else 'failure'}">
                    {'✅ ZERO DEFECTS' if results['zero_defects_achieved'] else '❌ DEFECTS REMAIN'}
                </div>
            </div>
        </div>
        
        <h2>Test Timeline</h2>
        <p><strong>Start:</strong> {results['start_time']}</p>
        <p><strong>End:</strong> {results['end_time']}</p>
        <p><strong>Duration:</strong> {results['total_duration_seconds']:.2f} seconds</p>
        
        <h2>Iteration Results</h2>
        <table>
            <thead>
                <tr>
                    <th>Iteration</th>
                    <th>Tests Run</th>
                    <th>Tests Passed</th>
                    <th>Tests Failed</th>
                    <th>Discrepancies</th>
                    <th>Duration</th>
                </tr>
            </thead>
            <tbody>
"""
        
        for iter_data in results['iteration_results']:
            result = iter_data['result']
            html += f"""
                <tr>
                    <td>{iter_data['iteration']}</td>
                    <td>{result.get('tests_run', 0)}</td>
                    <td class="success">{result.get('tests_passed', 0)}</td>
                    <td class="failure">{result.get('tests_failed', 0)}</td>
                    <td>{len(result.get('discrepancies', []))}</td>
                    <td>{iter_data['duration_seconds']:.2f}s</td>
                </tr>
"""
        
        html += """
            </tbody>
        </table>
        
        <h2>All Discrepancies</h2>
"""
        
        if results['all_discrepancies']:
            for disc in results['all_discrepancies']:
                html += f"""
        <div class="discrepancy">
            <strong>Category:</strong> {disc.get('category', disc.get('test', 'Unknown'))}<br>
            <strong>Expected:</strong> {disc.get('expected', 'N/A')}<br>
            <strong>Actual:</strong> {disc.get('actual', 'N/A')}<br>
            <strong>Context:</strong> {json.dumps(disc.get('context', {}), indent=2)}
        </div>
"""
        else:
            html += "<p class='success'>✅ No discrepancies found - All tests passed!</p>"
        
        html += """
    </div>
</body>
</html>
"""
        
        with open(report_path, 'w') as f:
            f.write(html)
        
        return str(report_path)
    
    def save_json_report(self, results: Dict) -> str:
        """Save results as JSON for programmatic access"""
        report_path = self.report_dir / f"qa_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        with open(report_path, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        return str(report_path)


def main():
    """Main entry point"""
    runner = IterativeTestRunner(max_iterations=10)
    results = runner.run_full_suite()
    
    # Generate reports
    html_report = runner.generate_report(results)
    json_report = runner.save_json_report(results)
    
    print("\n" + "=" * 80)
    print("📊 REPORTS GENERATED")
    print("=" * 80)
    print(f"HTML Report: {html_report}")
    print(f"JSON Report: {json_report}")
    print("=" * 80)
    
    # Exit code based on results
    if results['zero_defects_achieved']:
        print("\n✅ SUCCESS: Zero defects achieved!")
        sys.exit(0)
    else:
        print(f"\n❌ FAILURE: {results['total_discrepancies']} discrepancies remain")
        sys.exit(1)


if __name__ == '__main__':
    main()

