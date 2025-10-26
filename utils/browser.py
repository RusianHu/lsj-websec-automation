"""
Playwright 浏览器管理模块
"""
from typing import Optional, Dict, Any, List
from datetime import datetime
from playwright.async_api import async_playwright, Browser, Page, BrowserContext, ConsoleMessage, Dialog, Request, Response
from config.settings import settings
from utils.logger import log


class BrowserManager:
    """浏览器管理器"""

    def __init__(self):
        self.playwright = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None

        # 事件缓存
        self.console_logs: List[Dict[str, Any]] = []
        self.js_errors: List[Dict[str, Any]] = []
        self.dialog_events: List[Dict[str, Any]] = []
        self.network_requests: List[Dict[str, Any]] = []
        self.network_responses: List[Dict[str, Any]] = []

        # 缓存限制(避免内存溢出)
        self.max_cache_size = 1000
        
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

        # 设置事件监听器
        self._setup_event_listeners()

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

    def _setup_event_listeners(self):
        """设置页面事件监听器"""
        if not self.page:
            return

        # Console 日志监听
        def on_console(msg: ConsoleMessage):
            try:
                log_entry = {
                    "type": msg.type,
                    "text": msg.text,
                    "location": msg.location,
                    "timestamp": datetime.now().isoformat()
                }
                self._add_to_cache(self.console_logs, log_entry)

                # 同时记录到日志系统
                if msg.type == "error":
                    log.debug(f"[Browser Console Error] {msg.text}")
                elif msg.type == "warning":
                    log.debug(f"[Browser Console Warning] {msg.text}")
            except Exception as e:
                log.error(f"处理 console 事件失败: {e}")

        # JavaScript 错误监听
        def on_pageerror(error: Exception):
            try:
                error_entry = {
                    "message": str(error),
                    "timestamp": datetime.now().isoformat()
                }
                self._add_to_cache(self.js_errors, error_entry)
                log.warning(f"[Browser JS Error] {str(error)}")
            except Exception as e:
                log.error(f"处理 pageerror 事件失败: {e}")

        # Dialog 事件监听 (alert, confirm, prompt)
        def on_dialog(dialog: Dialog):
            try:
                dialog_entry = {
                    "type": dialog.type,
                    "message": dialog.message,
                    "default_value": dialog.default_value,
                    "timestamp": datetime.now().isoformat()
                }
                self._add_to_cache(self.dialog_events, dialog_entry)
                log.info(f"[Browser Dialog] {dialog.type}: {dialog.message}")

                # 自动接受 dialog (避免阻塞)
                dialog.accept()
            except Exception as e:
                log.error(f"处理 dialog 事件失败: {e}")

        # 网络请求监听
        def on_request(request: Request):
            try:
                request_entry = {
                    "url": request.url,
                    "method": request.method,
                    "resource_type": request.resource_type,
                    "headers": dict(request.headers),
                    "timestamp": datetime.now().isoformat()
                }
                self._add_to_cache(self.network_requests, request_entry)
            except Exception as e:
                log.error(f"处理 request 事件失败: {e}")

        # 网络响应监听
        def on_response(response: Response):
            try:
                response_entry = {
                    "url": response.url,
                    "status": response.status,
                    "status_text": response.status_text,
                    "headers": dict(response.headers),
                    "timestamp": datetime.now().isoformat()
                }
                self._add_to_cache(self.network_responses, response_entry)

                # 记录安全相关的响应头缺失
                security_headers = [
                    "strict-transport-security",
                    "content-security-policy",
                    "x-frame-options",
                    "x-content-type-options"
                ]
                missing_headers = [h for h in security_headers if h not in response.headers]
                if missing_headers and response.url.startswith("http"):
                    log.debug(f"[Security] {response.url} 缺少安全头: {missing_headers}")
            except Exception as e:
                log.error(f"处理 response 事件失败: {e}")

        # 注册事件监听器
        self.page.on("console", on_console)
        self.page.on("pageerror", on_pageerror)
        self.page.on("dialog", on_dialog)
        self.page.on("request", on_request)
        self.page.on("response", on_response)

        log.info("事件监听器已设置")

    def _add_to_cache(self, cache_list: List, item: Any):
        """添加项到缓存,并限制缓存大小"""
        cache_list.append(item)
        if len(cache_list) > self.max_cache_size:
            # 移除最旧的项
            cache_list.pop(0)

    def clear_event_caches(self):
        """清空所有事件缓存"""
        self.console_logs.clear()
        self.js_errors.clear()
        self.dialog_events.clear()
        self.network_requests.clear()
        self.network_responses.clear()
        log.info("事件缓存已清空")

    def get_console_logs(self, limit: Optional[int] = None, log_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """获取 console 日志"""
        logs = self.console_logs

        # 按类型过滤
        if log_type:
            logs = [log for log in logs if log["type"] == log_type]

        # 限制数量
        if limit:
            logs = logs[-limit:]

        return logs

    def get_js_errors(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """获取 JavaScript 错误"""
        if limit:
            return self.js_errors[-limit:]
        return self.js_errors

    def get_dialog_events(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """获取 dialog 事件"""
        if limit:
            return self.dialog_events[-limit:]
        return self.dialog_events

    def get_network_requests(self, limit: Optional[int] = None, url_filter: Optional[str] = None) -> List[Dict[str, Any]]:
        """获取网络请求"""
        requests = self.network_requests

        # URL 过滤
        if url_filter:
            requests = [req for req in requests if url_filter in req["url"]]

        # 限制数量
        if limit:
            requests = requests[-limit:]

        return requests

    def get_network_responses(self, limit: Optional[int] = None, status_filter: Optional[int] = None) -> List[Dict[str, Any]]:
        """获取网络响应"""
        responses = self.network_responses

        # 状态码过滤
        if status_filter:
            responses = [resp for resp in responses if resp["status"] == status_filter]

        # 限制数量
        if limit:
            responses = responses[-limit:]

        return responses

    def get_security_headers_analysis(self) -> Dict[str, Any]:
        """分析安全响应头"""
        if not self.network_responses:
            return {"analyzed": False, "message": "无网络响应数据"}

        # 分析最近的 HTML 响应
        html_responses = [
            resp for resp in self.network_responses
            if resp.get("headers", {}).get("content-type", "").startswith("text/html")
        ]

        if not html_responses:
            return {"analyzed": False, "message": "无 HTML 响应"}

        latest_response = html_responses[-1]
        headers = latest_response.get("headers", {})

        security_checks = {
            "strict-transport-security": {
                "present": "strict-transport-security" in headers,
                "value": headers.get("strict-transport-security", ""),
                "severity": "中" if "strict-transport-security" not in headers else "无"
            },
            "content-security-policy": {
                "present": "content-security-policy" in headers,
                "value": headers.get("content-security-policy", ""),
                "severity": "中" if "content-security-policy" not in headers else "无"
            },
            "x-frame-options": {
                "present": "x-frame-options" in headers,
                "value": headers.get("x-frame-options", ""),
                "severity": "低" if "x-frame-options" not in headers else "无"
            },
            "x-content-type-options": {
                "present": "x-content-type-options" in headers,
                "value": headers.get("x-content-type-options", ""),
                "severity": "低" if "x-content-type-options" not in headers else "无"
            }
        }

        missing_headers = [name for name, check in security_checks.items() if not check["present"]]

        return {
            "analyzed": True,
            "url": latest_response["url"],
            "security_headers": security_checks,
            "missing_headers": missing_headers,
            "vulnerable": len(missing_headers) > 0
        }

