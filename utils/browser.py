"""
Playwright 浏览器管理模块
"""
from typing import Optional, Dict, Any
from playwright.async_api import async_playwright, Browser, Page, BrowserContext
from config.settings import settings
from utils.logger import log


class BrowserManager:
    """浏览器管理器"""
    
    def __init__(self):
        self.playwright = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        
    async def start(self, **kwargs) -> Page:
        """启动浏览器并返回页面对象"""
        log.info("正在启动浏览器...")
        
        # 启动 Playwright
        self.playwright = await async_playwright().start()
        
        # 浏览器启动参数
        launch_options = {
            "headless": settings.playwright.headless,
            "slow_mo": settings.playwright.slow_mo,
            **kwargs
        }
        
        # 如果配置了代理
        if settings.proxy.http_proxy or settings.proxy.https_proxy:
            proxy_config = {}
            if settings.proxy.http_proxy:
                proxy_config["server"] = settings.proxy.http_proxy
            launch_options["proxy"] = proxy_config
        
        # 启动浏览器
        self.browser = await self.playwright.chromium.launch(**launch_options)
        
        # 创建浏览器上下文
        context_options = {
            "viewport": {
                "width": settings.playwright.viewport_width,
                "height": settings.playwright.viewport_height
            },
            "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        self.context = await self.browser.new_context(**context_options)
        
        # 设置默认超时
        self.context.set_default_timeout(settings.playwright.browser_timeout)
        
        # 创建新页面
        self.page = await self.context.new_page()
        
        log.info("浏览器启动成功")
        return self.page
    
    async def close(self):
        """关闭浏览器"""
        log.info("正在关闭浏览器...")
        
        if self.page:
            await self.page.close()
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
            
        log.info("浏览器已关闭")
    
    async def new_page(self) -> Page:
        """创建新页面"""
        if not self.context:
            raise RuntimeError("浏览器上下文未初始化，请先调用 start()")
        return await self.context.new_page()
    
    async def screenshot(self, path: str, full_page: bool = True) -> bytes:
        """截图"""
        if not self.page:
            raise RuntimeError("页面未初始化")
        return await self.page.screenshot(path=path, full_page=full_page)
    
    async def goto(self, url: str, **kwargs) -> None:
        """导航到指定 URL"""
        if not self.page:
            raise RuntimeError("页面未初始化")
        log.info(f"导航到: {url}")
        await self.page.goto(url, **kwargs)
    
    async def evaluate(self, script: str) -> Any:
        """执行 JavaScript"""
        if not self.page:
            raise RuntimeError("页面未初始化")
        return await self.page.evaluate(script)
    
    async def wait_for_selector(self, selector: str, **kwargs) -> None:
        """等待选择器"""
        if not self.page:
            raise RuntimeError("页面未初始化")
        await self.page.wait_for_selector(selector, **kwargs)
    
    async def click(self, selector: str, **kwargs) -> None:
        """点击元素"""
        if not self.page:
            raise RuntimeError("页面未初始化")
        await self.page.click(selector, **kwargs)
    
    async def fill(self, selector: str, value: str, **kwargs) -> None:
        """填充表单"""
        if not self.page:
            raise RuntimeError("页面未初始化")
        await self.page.fill(selector, value, **kwargs)
    
    async def get_content(self) -> str:
        """获取页面内容"""
        if not self.page:
            raise RuntimeError("页面未初始化")
        return await self.page.content()
    
    async def get_title(self) -> str:
        """获取页面标题"""
        if not self.page:
            raise RuntimeError("页面未初始化")
        return await self.page.title()
    
    async def get_url(self) -> str:
        """获取当前 URL"""
        if not self.page:
            raise RuntimeError("页面未初始化")
        return self.page.url

