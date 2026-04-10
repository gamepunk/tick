"""
启动 Web UI
"""
import subprocess
import sys
from pathlib import Path

def build_streamlit_command(app_path: Path) -> list[str]:
    """构建 Streamlit 启动命令"""
    return [
        sys.executable,
        "-m",
        "streamlit",
        "run",
        str(app_path),
        "--server.headless",
        "true",
    ]


def run_web() -> int:
    """启动 Streamlit 应用并返回退出码"""
    app_path = Path(__file__).parent / "app.py"

    print("🚀 启动 tick Web UI...")
    print(f"📁 应用路径: {app_path}")
    print("🌐 访问: http://localhost:8501\n")

    result = subprocess.run(build_streamlit_command(app_path), check=False)
    return result.returncode


def main():
    """控制台脚本入口"""
    raise SystemExit(run_web())

if __name__ == "__main__":
    main()
