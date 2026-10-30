# tests/test_cli.py
from click.testing import CliRunner
from aero_code.cli import cli


def test_cli_help():
    runner = CliRunner()
    result = runner.invoke(cli, ["--help"])
    assert result.exit_code == 0
    assert "run" in result.output
    assert "evaluate" in result.output
    assert "cases" in result.output
    assert "web" in result.output


def test_cli_list_cases():
    runner = CliRunner()
    result = runner.invoke(cli, ["cases"])
    assert result.exit_code == 0
    assert "pydantic_v2_migration" in result.output


def test_cli_run_case_demo():
    runner = CliRunner()
    result = runner.invoke(cli, ["run", "--case", "pydantic_v2_migration", "--mode", "demo"])
    assert result.exit_code == 0
    assert "ProofLoop Execution Finished" in result.output
