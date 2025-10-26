"""
简单扫描示例
演示如何使用 LSJ WebSec Automation 进行基础的 Web 扫描
"""
import asyncio
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from agents.pentest_agent import WebScannerAgent
from tools.browser_tools import navigate_to_url, take_screenshot, close_browser
from tools.web_scanner import check_common_files
from utils.logger import log


async def simple_scan_example():
    """简单扫描示例"""
    
    # 目标 URL
    target_url = "http://testphp.vulnweb.com"
    
    log.info(f"开始扫描: {target_url}")
    
    # 创建扫描 Agent
    scanner_agent = WebScannerAgent(tools=[
        navigate_to_url,
        take_screenshot,
        check_common_files,
    ])
    
    # 定义扫描任务
    task = f"""
    请对目标网站 {target_url} 进行基础安全扫描：
    
    1. 访问目标网站
    2. 截取首页截图
    3. 检查常见的敏感文件（如 robots.txt, .git/config 等）
    4. 总结发现的问题
    
    请详细记录每一步的操作和发现。
    """
    
    try:
        # 执行扫描
        result = await scanner_agent.run(task)
        
        print("\n" + "="*60)
        print("扫描结果:")
        print("="*60)
        print(result)
        
    except Exception as e:
        log.error(f"扫描失败: {str(e)}")
        print(f"扫描失败: {str(e)}")
        
    finally:
        # 清理资源
        await scanner_agent.close()
        await close_browser()


if __name__ == "__main__":
    asyncio.run(simple_scan_example())

