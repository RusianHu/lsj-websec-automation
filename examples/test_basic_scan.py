"""
基础扫描测试（不使用 Agent 工具调用）
直接使用扫描工具进行测试
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from tools.web_scanner import check_common_files
from tools.browser_tools import navigate_to_url, take_screenshot, close_browser
from utils.logger import log


async def basic_scan_test():
    """基础扫描测试"""
    
    target_url = "http://testphp.vulnweb.com"
    
    print("="*60)
    print(f"开始基础扫描测试: {target_url}")
    print("="*60)
    
    try:
        # 1. 检查常见敏感文件
        print("\n1. 检查常见敏感文件...")
        files_result = await check_common_files(target_url)
        
        if files_result['success']:
            print(f"   扫描完成，发现 {files_result['found']} 个敏感文件")
            for item in files_result['results']:
                print(f"     - {item['file']}: {item['status_code']}")
        else:
            print(f"   扫描失败")
        
        # 2. 使用浏览器访问网站
        print("\n2. 使用浏览器访问网站...")
        nav_result = await navigate_to_url(target_url)
        
        if nav_result['success']:
            print(f"   成功访问")
            print(f"     标题: {nav_result['title']}")
            print(f"     URL: {nav_result['url']}")
        else:
            print(f"   访问失败: {nav_result.get('error')}")
        
        # 3. 截取首页截图
        print("\n3. 截取首页截图...")
        screenshot_result = await take_screenshot("test_homepage")
        
        if screenshot_result['success']:
            print(f"   截图成功")
            print(f"     保存路径: {screenshot_result['path']}")
        else:
            print(f"   截图失败: {screenshot_result.get('error')}")
        
        print("\n" + "="*60)
        print("基础扫描测试完成")
        print("="*60)
        
        # 显示总结
        print("\n扫描总结:")
        print(f"  - 发现敏感文件: {files_result['found']} 个")
        print(f"  - 页面标题: {nav_result.get('title', 'N/A')}")
        print(f"  - 截图保存: {screenshot_result.get('path', 'N/A')}")
        
    except Exception as e:
        log.error(f"测试失败: {str(e)}")
        print(f"\n测试失败: {str(e)}")
        
    finally:
        # 关闭浏览器
        await close_browser()


if __name__ == "__main__":
    asyncio.run(basic_scan_test())
