import os
import sys
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from app.routes import task_routes


def test_check_status_db_fallback(monkeypatch):
    def fake_async_result(task_id):
        raise Exception("not found")

    def fake_get_task_status(task_id):
        return {"state": "SUCCESS", "meta": {"foo": "bar"}}

    monkeypatch.setattr(task_routes.celery_app, "AsyncResult", lambda tid: fake_async_result(tid))
    monkeypatch.setattr(task_routes.db, "get_task_status", fake_get_task_status)

    result = task_routes.check_status("dummy")
    assert result["state"] == "SUCCESS"
    assert result["result"] == {"foo": "bar"}
