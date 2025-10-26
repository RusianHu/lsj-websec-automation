"""
浏览器自动化工具函数
这些函数可以被 Autogen Agent 调用
"""
from typing import Dict, Any, Optional, List
from datetime import datetime
from pathlib import Path
from utils.browser import BrowserManager
from utils.logger import log
from utils.url_helper import normalize_url
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
        # 规范化 URL
        url = normalize_url(url)

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


async def find_forms() -> Dict[str, Any]:
    """
    查找页面中的所有表单元素

    Returns:
        包含表单信息的字典
    """
    try:
        browser = await get_browser_manager()

        # 使用 JavaScript 查找所有表单
        script = """
        () => {
            const forms = Array.from(document.querySelectorAll('form'));
            return forms.map((form, index) => {
                const inputs = Array.from(form.querySelectorAll('input, textarea, select'));
                return {
                    index: index,
                    id: form.id || null,
                    action: form.action || null,
                    method: form.method || 'get',
                    inputs: inputs.map(input => ({
                        type: input.type || input.tagName.toLowerCase(),
                        name: input.name || null,
                        id: input.id || null,
                        placeholder: input.placeholder || null,
                        required: input.required || false
                    }))
                };
            });
        }
        """

        forms = await browser.evaluate(script)

        log.info(f"找到 {len(forms)} 个表单")

        return {
            "success": True,
            "forms": forms,
            "count": len(forms),
            "message": f"找到 {len(forms)} 个表单"
        }
    except Exception as e:
        log.error(f"查找表单失败: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "message": "查找表单失败"
        }


async def find_links() -> Dict[str, Any]:
    """
    查找页面中的所有链接

    Returns:
        包含链接信息的字典
    """
    try:
        browser = await get_browser_manager()

        script = """
        () => {
            const links = Array.from(document.querySelectorAll('a[href]'));
            return links.map(link => ({
                text: link.textContent.trim(),
                href: link.href,
                target: link.target || null
            })).slice(0, 50);  // 限制返回前 50 个链接
        }
        """

        links = await browser.evaluate(script)

        log.info(f"找到 {len(links)} 个链接")

        return {
            "success": True,
            "links": links,
            "count": len(links),
            "message": f"找到 {len(links)} 个链接（最多显示 50 个）"
        }
    except Exception as e:
        log.error(f"查找链接失败: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "message": "查找链接失败"
        }


async def analyze_page_structure() -> Dict[str, Any]:
    """
    分析页面结构

    Returns:
        包含页面结构信息的字典
    """
    try:
        browser = await get_browser_manager()

        script = """
        () => {
            return {
                title: document.title,
                url: window.location.href,
                forms: document.querySelectorAll('form').length,
                inputs: document.querySelectorAll('input').length,
                buttons: document.querySelectorAll('button').length,
                links: document.querySelectorAll('a').length,
                images: document.querySelectorAll('img').length,
                scripts: document.querySelectorAll('script').length,
                iframes: document.querySelectorAll('iframe').length,
                hasLogin: !!(
                    document.querySelector('input[type="password"]') ||
                    document.querySelector('input[name*="password"]') ||
                    document.querySelector('input[name*="login"]') ||
                    document.querySelector('input[name*="user"]')
                ),
                cookies: document.cookie ? document.cookie.split(';').length : 0
            };
        }
        """

        structure = await browser.evaluate(script)

        log.info(f"页面结构分析完成")

        return {
            "success": True,
            "structure": structure,
            "message": "页面结构分析完成"
        }
    except Exception as e:
        log.error(f"分析页面结构失败: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "message": "分析页面结构失败"
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

