"""
项目安装脚本
"""
import subprocess
import sys
from pathlib import Path


def run_command(command, description):
    """运行命令并显示进度"""
    print(f"\n{'='*60}")
    print(f"{description}")
    print(f"{'='*60}")
    
    try:
        result = subprocess.run(
            command,
            shell=True,
            check=True,
            capture_output=True,
            text=True
        )
        print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"错误: {e.stderr}")
        return False


def main():
    """主安装流程"""
    print("""
╔═══════════════════════════════════════════════════════════╗
║                                                           ║
║        LSJ WebSec Automation - 安装向导                   ║
║                                                           ║
╚═══════════════════════════════════════════════════════════╝
    """)
    
    # 检查 Python 版本
    if sys.version_info < (3, 8):
        print("错误: 需要 Python 3.8 或更高版本")
        sys.exit(1)
    
    print(f"[OK] Python 版本: {sys.version}")
    
    # 创建虚拟环境
    if not Path("venv").exists():
        if not run_command(
            f"{sys.executable} -m venv venv",
            "1. 创建虚拟环境"
        ):
            print("创建虚拟环境失败")
            sys.exit(1)
    else:
        print("\n虚拟环境已存在，跳过创建")
    
    # 确定 pip 路径
    if sys.platform == "win32":
        pip_path = "venv\\Scripts\\pip"
        python_path = "venv\\Scripts\\python"
    else:
        pip_path = "venv/bin/pip"
        python_path = "venv/bin/python"
    
    # 升级 pip
    run_command(
        f"{python_path} -m pip install --upgrade pip",
        "2. 升级 pip"
    )
    
    # 安装依赖（使用国内镜像源）
    if not run_command(
        f"{pip_path} install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple",
        "3. 安装 Python 依赖"
    ):
        print("安装依赖失败")
        sys.exit(1)
    
    # 安装 Playwright 浏览器
    if not run_command(
        f"{python_path} -m playwright install chromium",
        "4. 安装 Playwright 浏览器"
    ):
        print("安装浏览器失败")
        sys.exit(1)
    
    # 创建 .env 文件
    if not Path(".env").exists():
        print("\n5. 创建配置文件")
        Path(".env").write_text(Path(".env.example").read_text(encoding="utf-8"), encoding="utf-8")
        print("[OK] 已创建 .env 文件，请编辑此文件配置你的 API 密钥")
    else:
        print("\n.env 文件已存在，跳过创建")
    
    print(f"\n{'='*60}")
    print("安装完成！")
    print(f"{'='*60}")
    print("\n下一步:")
    print("1. 编辑 .env 文件，配置你的 OpenAI API 密钥")
    print("2. 激活虚拟环境:")
    if sys.platform == "win32":
        print("   venv\\Scripts\\activate")
    else:
        print("   source venv/bin/activate")
    print("3. 运行主程序:")
    print("   python main.py")
    print("\n或者运行示例:")
    print("   python examples/simple_scan.py")
    print("   python examples/vulnerability_test.py")
    print("   python examples/browser_automation.py")
    print()


if __name__ == "__main__":
    main()
