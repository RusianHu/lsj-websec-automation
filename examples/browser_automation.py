"""
浏览器自动化示例
演示如何使用 Playwright 进行浏览器自动化
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from tools.browser_tools import (
    navigate_to_url,
    take_screenshot,
    get_page_content,
    execute_javascript,
    close_browser
)
from utils.logger import log


async def browser_automation_example():
    """浏览器自动化示例"""
    
    target_url = "http://testphp.vulnweb.com"
    
    log.info(f"开始浏览器自动化测试: {target_url}")
    
    try:
        # 1. 导航到目标网站
        print("\n1. 导航到目标网站...")
        nav_result = await navigate_to_url(target_url)
        print(f"   页面标题: {nav_result.get('title')}")
        print(f"   当前 URL: {nav_result.get('url')}")
        
        # 2. 截取首页截图
        print("\n2. 截取首页截图...")
        screenshot_result = await take_screenshot("homepage")
        print(f"   截图保存到: {screenshot_result.get('path')}")
        
        # 3. 获取页面内容
        print("\n3. 获取页面内容...")
        content_result = await get_page_content()
        print(f"   页面内容长度: {content_result.get('length')} 字符")
        
        # 4. 执行 JavaScript 获取页面信息
        print("\n4. 执行 JavaScript 获取页面信息...")
        js_script = """
        ({
            title: document.title,
            url: window.location.href,
            forms: document.forms.length,
            links: document.links.length,
            images: document.images.length
        })
        """
        js_result = await execute_javascript(js_script)
        print(f"   页面信息: {js_result.get('result')}")
        
        print("\n" + "="*60)
        print("浏览器自动化测试完成")
        print("="*60)
        
    except Exception as e:
        log.error(f"测试失败: {str(e)}")
        print(f"测试失败: {str(e)}")
        
    finally:
        # 关闭浏览器
        await close_browser()


if __name__ == "__main__":
    asyncio.run(browser_automation_example())

