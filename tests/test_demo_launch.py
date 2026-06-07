from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[1]


def test_vite_dev_server_starts_web_while_api_boots_in_background():
    vite_config = (ROOT / "web" / "vite.config.ts").read_text(encoding="utf-8")

    assert "void ensureApiReady(server)" in vite_config
    assert not re.search(r"^\s*await ensureApiReady\(server\);\s*$", vite_config, flags=re.MULTILINE)


def test_vite_health_check_confirms_reazon_api_response():
    vite_config = (ROOT / "web" / "vite.config.ts").read_text(encoding="utf-8")

    assert 'data?.status === "healthy"' in vite_config
    assert 'fetch(`${apiTarget}/health`' in vite_config


def test_start_demo_bootstraps_dependencies_and_cleans_up_owned_api_process():
    script = (ROOT / "scripts" / "start_demo.ps1").read_text(encoding="utf-8")

    assert "python -m venv .venv" in script
    assert "pip install -r" in script
    assert "requirements.txt" in script
    assert "npm install" in script
    assert "-PassThru" in script
    assert "Stop-Process -Id $StartedApiProcess.Id" in script
