import sqlite3
from pathlib import Path

from app.runtime_env import build_runtime_state


def test_import_route_happy_path(auth_client):
    app = auth_client.application
    upload_dir = Path(app.config['UPLOAD_FOLDER'])
    runtime_state = build_runtime_state()
    log_file = runtime_state.log_file
    log_before = log_file.stat().st_size if log_file.exists() else 0

    sample_file = Path(__file__).parent / "sample_files" / "basic_valid.xlsx"
    with sample_file.open("rb") as fh:
        response = auth_client.post(
            "/import_excel",
            data={"excel_file": (fh, "basic_valid.xlsx")},
            follow_redirects=True,
            content_type="multipart/form-data",
        )

    assert response.status_code == 200
    assert b"Import Summary" in response.data or b"Excel file imported successfully" in response.data

    db_path = Path(app.config["DATABASE"])
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM trips")
    trip_count = c.fetchone()[0]
    conn.close()
    assert trip_count > 0

    uploaded_file = upload_dir / "basic_valid.xlsx"
    assert not uploaded_file.exists()
    assert log_file.stat().st_size >= log_before

