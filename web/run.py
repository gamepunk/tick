"""
启动 Web UI
"""
import subprocess
import sys
from pathlib import Path

def main():
    """启动 Streamlit 应用"""
    app_path = Path(__file__).parent / "app.py"
    
    print("🚀 启动 tick Web UI...")
    print(f"📁 应用路径: {app_path}")
    print("🌐 访问: http://localhost:8501\n")
    
    subprocess.run([
        sys.executable, "-m", "streamlit", "run", str(app_path),
        "--server.headless", "true"
    ])

if __name__ == "__main__":
    main()
