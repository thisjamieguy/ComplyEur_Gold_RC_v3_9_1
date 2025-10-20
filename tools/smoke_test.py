import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from app import create_app


def run_smoke_tests():
    app = create_app()
    app.config['TESTING'] = True
    with app.test_client() as client:
        r = client.get('/login')
        assert r.status_code == 200, f"/login failed: {r.status_code}"

        r = client.get('/static/css/global.css')
        assert r.status_code == 200, f"global.css missing: {r.status_code}"

        r = client.get('/api/entry-requirements')
        assert r.status_code in (301, 302), f"/api/entry-requirements should redirect: {r.status_code}"

        r = client.get('/entry-requirements')
        assert r.status_code in (301, 302), f"/entry-requirements should redirect: {r.status_code}"

        r = client.get('/dashboard')
        assert r.status_code in (301, 302), f"/dashboard should redirect: {r.status_code}"

    print("Smoke tests passed.")


if __name__ == '__main__':
    run_smoke_tests()
