from click.testing import CliRunner
from odrive_can.cli import cli


def test_cli():
    runner = CliRunner()
    result = runner.invoke(cli, ["--help"])
    assert result.exit_code == 0
    assert "Usage: cli [OPTIONS]" in result.output
    assert "Options:" in result.output
    assert "--help  Show this message and exit." in result.output


def test_cli_info():
    runner = CliRunner()
    result = runner.invoke(cli, ["info"])
    assert result.exit_code == 0
