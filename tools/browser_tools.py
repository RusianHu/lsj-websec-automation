"""
浏览器自动化工具函数
这些函数可以被 Autogen Agent 调用
"""
from typing import Dict, Any, Optional, List
from datetime import datetime
from pathlib import Path
from utils.browser import BrowserManager
from utils.logger import log
from config.settings import settings


# 全局浏览器管理器实例
_browser_manager: Optional[BrowserManager] = None


async def get_browser_manager() -> BrowserManager:
    """获取浏览器管理器实例"""
    global _browser_manager
    if _browser_manager is None:
        _browser_manager = BrowserManager()
        await _browser_manager.start()
    return _browser_manager


async def navigate_to_url(url: str, wait_until: str = "networkidle") -> Dict[str, Any]:
    """
    导航到指定 URL
    
    Args:
        url: 目标 URL
        wait_until: 等待条件 (load, domcontentloaded, networkidle)
        
    Returns:
        包含页面信息的字典
    """
    try:
        browser = await get_browser_manager()
        await browser.goto(url, wait_until=wait_until)
        
        title = await browser.get_title()
        current_url = await browser.get_url()
        
        log.info(f"成功导航到: {url}")
        
        return {
            "success": True,
            "url": current_url,
            "title": title,
            "message": f"成功导航到 {url}"
        }
    except Exception as e:
        log.error(f"导航失败: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "message": f"导航到 {url} 失败"
        }


async def take_screenshot(name: Optional[str] = None, full_page: bool = True) -> Dict[str, Any]:
    """
    截取当前页面截图
    
    Args:
        name: 截图文件名（不含扩展名）
        full_page: 是否截取整个页面
        
    Returns:
        包含截图路径的字典
    """
    try:
        browser = await get_browser_manager()
        
        if name is None:
            name = f"screenshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        screenshot_path = settings.app.screenshots_dir / f"{name}.png"
        await browser.screenshot(str(screenshot_path), full_page=full_page)
        
        log.info(f"截图已保存: {screenshot_path}")
        
        return {
            "success": True,
            "path": str(screenshot_path),
            "message": f"截图已保存到 {screenshot_path}"
        }
    except Exception as e:
        log.error(f"截图失败: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "message": "截图失败"
        }


async def fill_form(selector: str, value: str) -> Dict[str, Any]:
    """
    填充表单字段
    
    Args:
        selector: CSS 选择器
        value: 要填充的值
        
    Returns:
        操作结果
    """
    try:
        browser = await get_browser_manager()
        await browser.fill(selector, value)
        
        log.info(f"成功填充表单: {selector}")
        
        return {
            "success": True,
            "selector": selector,
            "message": f"成功填充表单字段 {selector}"
        }
    except Exception as e:
        log.error(f"填充表单失败: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "message": f"填充表单字段 {selector} 失败"
        }


async def click_element(selector: str) -> Dict[str, Any]:
    """
    点击页面元素
    
    Args:
        selector: CSS 选择器
        
    Returns:
        操作结果
    """
    try:
        browser = await get_browser_manager()
        await browser.click(selector)
        
        log.info(f"成功点击元素: {selector}")
        
        return {
            "success": True,
            "selector": selector,
            "message": f"成功点击元素 {selector}"
        }
    except Exception as e:
        log.error(f"点击元素失败: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "message": f"点击元素 {selector} 失败"
        }


async def get_page_content() -> Dict[str, Any]:
    """
    获取当前页面的 HTML 内容
    
    Returns:
        包含页面内容的字典
    """
    try:
        browser = await get_browser_manager()
        content = await browser.get_content()
        
        return {
            "success": True,
            "content": content,
            "length": len(content),
            "message": "成功获取页面内容"
        }
    except Exception as e:
        log.error(f"获取页面内容失败: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "message": "获取页面内容失败"
        }


async def execute_javascript(script: str) -> Dict[str, Any]:
    """
    在页面中执行 JavaScript 代码
    
    Args:
        script: JavaScript 代码
        
    Returns:
        执行结果
    """
    try:
        browser = await get_browser_manager()
        result = await browser.evaluate(script)
        
        log.info(f"成功执行 JavaScript")
        
        return {
            "success": True,
            "result": result,
            "message": "JavaScript 执行成功"
        }
    except Exception as e:
        log.error(f"执行 JavaScript 失败: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "message": "JavaScript 执行失败"
        }


async def wait_for_element(selector: str, timeout: int = 30000) -> Dict[str, Any]:
    """
    等待元素出现
    
    Args:
        selector: CSS 选择器
        timeout: 超时时间（毫秒）
        
    Returns:
        操作结果
    """
    try:
        browser = await get_browser_manager()
        await browser.wait_for_selector(selector, timeout=timeout)
        
        log.info(f"元素已出现: {selector}")
        
        return {
            "success": True,
            "selector": selector,
            "message": f"元素 {selector} 已出现"
        }
    except Exception as e:
        log.error(f"等待元素失败: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "message": f"等待元素 {selector} 超时"
        }


async def close_browser() -> Dict[str, Any]:
    """
    关闭浏览器
    
    Returns:
        操作结果
    """
    global _browser_manager
    try:
        if _browser_manager:
            await _browser_manager.close()
            _browser_manager = None
        
        log.info("浏览器已关闭")
        
        return {
            "success": True,
            "message": "浏览器已关闭"
        }
    except Exception as e:
        log.error(f"关闭浏览器失败: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "message": "关闭浏览器失败"
        }

