from threading import Thread

import pytest
from werkzeug.serving import make_server

import app as app_module


@pytest.fixture
def isolated_db(tmp_path, monkeypatch):
    monkeypatch.setattr(app_module, "DB_PATH", str(tmp_path / "expenses.db"))
    app_module.init_db()


@pytest.fixture
def live_server(isolated_db):
    server = make_server("127.0.0.1", 0, app_module.app)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_port}"
    finally:
        server.shutdown()
        thread.join()
        server.server_close()
