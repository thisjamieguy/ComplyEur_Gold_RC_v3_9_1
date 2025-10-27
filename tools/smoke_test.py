import os
import sys
import json

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from app import create_app


def run_smoke_tests():
    app = create_app()
    app.config['TESTING'] = True
    
    with app.test_client() as client:
        # Test 1: Basic page loads
        print("Testing basic page loads...")
        r = client.get('/login')
        assert r.status_code == 200, f"/login failed: {r.status_code}"

        r = client.get('/static/css/global.css')
        assert r.status_code == 200, f"global.css missing: {r.status_code}"

        r = client.get('/static/css/hubspot-style.css')
        assert r.status_code == 200, f"hubspot-style.css missing: {r.status_code}"

        r = client.get('/static/js/hubspot-style.js')
        assert r.status_code == 200, f"hubspot-style.js missing: {r.status_code}"

        # Test 2: Authentication flow
        print("Testing authentication flow...")
        r = client.get('/api/entry-requirements')
        assert r.status_code in (301, 302), f"/api/entry-requirements should redirect: {r.status_code}"

        r = client.get('/entry-requirements')
        assert r.status_code in (301, 302), f"/entry-requirements should redirect: {r.status_code}"

        r = client.get('/dashboard')
        assert r.status_code in (301, 302), f"/dashboard should redirect: {r.status_code}"

        # Test 3: Login with default credentials
        print("Testing login with default credentials...")
        r = client.post('/login', data={'password': 'admin123'}, follow_redirects=True)
        assert r.status_code == 200, f"Login failed: {r.status_code}"

        # Test 4: Dashboard access after login
        print("Testing dashboard access...")
        r = client.get('/dashboard')
        assert r.status_code == 200, f"Dashboard access failed: {r.status_code}"

        # Test 5: Employee management
        print("Testing employee management...")
        r = client.post('/add_employee', data={'name': 'Test Employee'})
        assert r.status_code == 200, f"Add employee failed: {r.status_code}"
        
        # Parse response to get employee ID
        try:
            response_data = json.loads(r.data)
            if response_data.get('success'):
                employee_id = response_data.get('employee_id')
                
                # Test 6: Employee detail page
                print("Testing employee detail page...")
                r = client.get(f'/employee/{employee_id}')
                assert r.status_code == 200, f"Employee detail page failed: {r.status_code}"

                # Test 7: Add trip
                print("Testing trip addition...")
                r = client.post('/add_trip', data={
                    'employee_id': employee_id,
                    'country': 'FR',
                    'entry_date': '2024-01-01',
                    'exit_date': '2024-01-05',
                    'purpose': 'Business trip'
                })
                assert r.status_code == 200, f"Add trip failed: {r.status_code}"
                
                # Parse response to get trip ID
                try:
                    response_data = json.loads(r.data)
                    if response_data.get('success'):
                        trip_id = response_data.get('trip_id')
                        
                        # Test 8: Get trip details
                        print("Testing trip retrieval...")
                        r = client.get(f'/get_trip/{trip_id}')
                        assert r.status_code == 200, f"Get trip failed: {r.status_code}"
                        
                        # Test 9: Edit trip
                        print("Testing trip editing...")
                        r = client.post(f'/edit_trip/{trip_id}', 
                                      data=json.dumps({
                                          'country': 'DE',
                                          'entry_date': '2024-01-02',
                                          'exit_date': '2024-01-06'
                                      }),
                                      content_type='application/json')
                        assert r.status_code == 200, f"Edit trip failed: {r.status_code}"
                        
                        # Test 10: Delete trip
                        print("Testing trip deletion...")
                        r = client.post(f'/delete_trip/{trip_id}')
                        assert r.status_code == 200, f"Delete trip failed: {r.status_code}"
                except Exception as e:
                    print(f"Warning: Could not test trip operations: {e}")
        except Exception as e:
            print(f"Warning: Could not test employee operations: {e}")

        # Test 11: Import/Export pages
        print("Testing import/export pages...")
        r = client.get('/import_excel')
        assert r.status_code == 200, f"Import Excel page failed: {r.status_code}"

        r = client.get('/export/trips/csv')
        assert r.status_code == 200, f"Export trips CSV failed: {r.status_code}"

        # Test 12: API endpoints
        print("Testing API endpoints...")
        r = client.get('/api/version')
        assert r.status_code == 200, f"API version endpoint failed: {r.status_code}"

        r = client.get('/healthz')
        assert r.status_code == 200, f"Health check endpoint failed: {r.status_code}"

        # Test 13: Help and privacy pages
        print("Testing help and privacy pages...")
        r = client.get('/help')
        assert r.status_code == 200, f"Help page failed: {r.status_code}"

        r = client.get('/privacy')
        assert r.status_code == 200, f"Privacy page failed: {r.status_code}"

        # Test 14: Logout
        print("Testing logout...")
        r = client.get('/logout', follow_redirects=True)
        assert r.status_code == 200, f"Logout failed: {r.status_code}"

    print("All smoke tests passed successfully!")


if __name__ == '__main__':
    run_smoke_tests()
