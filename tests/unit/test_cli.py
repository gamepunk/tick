"""
测试 CLI 入口
"""
from click.testing import CliRunner

import web.run as web_run
from tick.main import cli


class TestCli:
    """测试 CLI 命令"""

    def test_no_args_shows_help(self):
        """测试不带参数时显示帮助信息"""
        result = CliRunner().invoke(cli, [])

        assert result.exit_code == 0
        assert "Usage:" in result.output
        assert "Commands:" in result.output

    def test_web_command_invokes_web_runner(self, monkeypatch):
        """测试 web 子命令调用 Web 启动器"""
        called = {"count": 0}

        def fake_run_web():
            called["count"] += 1
            return 0

        monkeypatch.setattr(web_run, "run_web", fake_run_web)

        result = CliRunner().invoke(cli, ["web"])

        assert result.exit_code == 0
        assert called["count"] == 1

    def test_help_lists_web_command(self):
        """测试帮助信息包含 web 子命令"""
        result = CliRunner().invoke(cli, ["--help"])

        assert result.exit_code == 0
        assert "web" in result.output
