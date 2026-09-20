import asyncio
import ast
from pathlib import Path
from scripts.run_nexus_simulated import run

def test_simulated_runtime_crosses_core_lifecycle() -> None:
    result = asyncio.run(run())
    assert result["startup_reconciliation"] == "MATCHED"
    assert result["portfolio_risk"] == "APPROVED"
    assert result["order_status"] == "ACCEPTED"
    assert result["post_execution_reconciliation"] == "MATCHED"
    assert result["real_exchange_writes"] == 0
    assert result["production_authority"] is False
    assert result["status"] == "RUNNING"

def test_simulated_runtime_has_no_external_or_secret_access() -> None:
    path = Path("scripts/run_nexus_simulated.py")
    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source)
    roots = {node.names[0].name.split(".")[0] for node in ast.walk(tree) if isinstance(node, ast.Import)} | {node.module.split(".")[0] for node in ast.walk(tree) if isinstance(node, ast.ImportFrom) and node.module}
    assert not ({"requests", "httpx", "urllib", "socket", "subprocess", "sqlalchemy"} & roots)
    lowered = source.lower()
    assert "api_key" not in lowered
    assert "secret_key" not in lowered
    assert "database_url" not in lowered
