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

        # 限制返回内容长度,避免 LLM 调用负载过大
        max_length = 2000
        is_truncated = len(content) > max_length
        if is_truncated:
            truncated = content[:max_length]
            log.debug(f"页面内容超出 {max_length} 字符,已截断")
        else:
            truncated = content
        message = "成功获取页面内容 (已截断)" if is_truncated else "成功获取页面内容"

        return {
            "success": True,
            "content": truncated,
            "length": len(truncated),
            "truncated": is_truncated,
            "message": message
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


# ==================== 浏览器观测工具 ====================

async def get_console_logs(limit: int = 100, log_type: Optional[str] = None) -> Dict[str, Any]:
    """
    获取浏览器控制台日志

    Args:
        limit: 返回的日志数量限制 (默认 100)
        log_type: 日志类型过滤 (log, info, warning, error, debug)

    Returns:
        包含控制台日志的字典
    """
    try:
        browser = await get_browser_manager()
        logs = browser.get_console_logs(limit=limit, log_type=log_type)

        # 统计各类型日志数量
        type_counts = {}
        for log_entry in logs:
            log_type_key = log_entry.get("type", "unknown")
            type_counts[log_type_key] = type_counts.get(log_type_key, 0) + 1

        log.info(f"获取到 {len(logs)} 条控制台日志")

        return {
            "success": True,
            "count": len(logs),
            "type_counts": type_counts,
            "logs": logs,
            "message": f"成功获取 {len(logs)} 条控制台日志"
        }
    except Exception as e:
        log.error(f"获取控制台日志失败: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "message": "获取控制台日志失败"
        }


async def get_js_errors(limit: int = 50) -> Dict[str, Any]:
    """
    获取 JavaScript 错误

    Args:
        limit: 返回的错误数量限制 (默认 50)

    Returns:
        包含 JavaScript 错误的字典
    """
    try:
        browser = await get_browser_manager()
        errors = browser.get_js_errors(limit=limit)

        log.info(f"获取到 {len(errors)} 个 JavaScript 错误")

        return {
            "success": True,
            "count": len(errors),
            "errors": errors,
            "has_errors": len(errors) > 0,
            "message": f"发现 {len(errors)} 个 JavaScript 错误" if errors else "未发现 JavaScript 错误"
        }
    except Exception as e:
        log.error(f"获取 JavaScript 错误失败: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "message": "获取 JavaScript 错误失败"
        }


async def get_dialog_events(limit: int = 50) -> Dict[str, Any]:
    """
    获取浏览器对话框事件 (alert, confirm, prompt)

    Args:
        limit: 返回的事件数量限制 (默认 50)

    Returns:
        包含对话框事件的字典
    """
    try:
        browser = await get_browser_manager()
        dialogs = browser.get_dialog_events(limit=limit)

        # 统计各类型对话框数量
        type_counts = {}
        for dialog in dialogs:
            dialog_type = dialog.get("type", "unknown")
            type_counts[dialog_type] = type_counts.get(dialog_type, 0) + 1

        log.info(f"获取到 {len(dialogs)} 个对话框事件")

        return {
            "success": True,
            "count": len(dialogs),
            "type_counts": type_counts,
            "dialogs": dialogs,
            "has_dialogs": len(dialogs) > 0,
            "message": f"发现 {len(dialogs)} 个对话框事件 (可能是 XSS 触发)" if dialogs else "未发现对话框事件"
        }
    except Exception as e:
        log.error(f"获取对话框事件失败: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "message": "获取对话框事件失败"
        }


async def get_network_events(
    limit: int = 100,
    url_filter: Optional[str] = None,
    status_filter: Optional[int] = None
) -> Dict[str, Any]:
    """
    获取网络请求和响应事件

    Args:
        limit: 返回的事件数量限制 (默认 100)
        url_filter: URL 过滤字符串 (包含匹配)
        status_filter: HTTP 状态码过滤

    Returns:
        包含网络事件的字典
    """
    try:
        browser = await get_browser_manager()
        requests = browser.get_network_requests(limit=limit, url_filter=url_filter)
        responses = browser.get_network_responses(limit=limit, status_filter=status_filter)

        # 统计状态码分布
        status_counts = {}
        for resp in responses:
            status = resp.get("status", 0)
            status_counts[status] = status_counts.get(status, 0) + 1

        log.info(f"获取到 {len(requests)} 个请求, {len(responses)} 个响应")

        return {
            "success": True,
            "request_count": len(requests),
            "response_count": len(responses),
            "status_counts": status_counts,
            "requests": requests,
            "responses": responses,
            "message": f"成功获取 {len(requests)} 个请求和 {len(responses)} 个响应"
        }
    except Exception as e:
        log.error(f"获取网络事件失败: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "message": "获取网络事件失败"
        }


async def clear_event_caches() -> Dict[str, Any]:
    """
    清空所有事件缓存 (console, errors, dialogs, network)

    Returns:
        操作结果
    """
    try:
        browser = await get_browser_manager()
        browser.clear_event_caches()

        log.info("事件缓存已清空")

        return {
            "success": True,
            "message": "所有事件缓存已清空"
        }
    except Exception as e:
        log.error(f"清空事件缓存失败: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "message": "清空事件缓存失败"
        }


async def analyze_security_headers() -> Dict[str, Any]:
    """
    分析页面的安全响应头

    Returns:
        安全头分析结果
    """
    try:
        browser = await get_browser_manager()
        analysis = browser.get_security_headers_analysis()

        if not analysis.get("analyzed"):
            return {
                "success": False,
                "message": analysis.get("message", "无法分析安全头")
            }

        missing_headers = analysis.get("missing_headers", [])

        log.info(f"安全头分析完成, 缺失 {len(missing_headers)} 个安全头")

        return {
            "success": True,
            "url": analysis.get("url"),
            "security_headers": analysis.get("security_headers"),
            "missing_headers": missing_headers,
            "vulnerable": analysis.get("vulnerable", False),
            "severity": "中" if missing_headers else "无",
            "message": f"缺失安全头: {', '.join(missing_headers)}" if missing_headers else "所有关键安全头均已设置"
        }
    except Exception as e:
        log.error(f"分析安全头失败: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "message": "分析安全头失败"
        }


# ==================== 表单测试高层工具 ====================

async def fill_input_by_name(field_name: str, value: str, form_index: int = 0) -> Dict[str, Any]:
    """
    根据字段名称填充表单输入

    Args:
        field_name: 字段名称 (name 或 id 属性)
        value: 要填充的值
        form_index: 表单索引 (默认 0, 第一个表单)

    Returns:
        操作结果
    """
    try:
        browser = await get_browser_manager()

        # 尝试多种选择器策略
        selectors = [
            f'input[name="{field_name}"]',
            f'input[id="{field_name}"]',
            f'textarea[name="{field_name}"]',
            f'textarea[id="{field_name}"]',
            f'select[name="{field_name}"]',
            f'select[id="{field_name}"]'
        ]

        filled = False
        used_selector = None

        for selector in selectors:
            try:
                # 检查元素是否存在
                element_exists = await browser.evaluate(f'''
                    document.querySelector('{selector}') !== null
                ''')

                if element_exists:
                    await browser.fill(selector, value)
                    filled = True
                    used_selector = selector
                    log.info(f"成功填充字段 '{field_name}' 使用选择器: {selector}")
                    break
            except:
                continue

        if not filled:
            return {
                "success": False,
                "message": f"未找到字段: {field_name}"
            }

        return {
            "success": True,
            "field_name": field_name,
            "value": value,
            "selector": used_selector,
            "message": f"成功填充字段 '{field_name}'"
        }
    except Exception as e:
        log.error(f"填充字段失败: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "message": f"填充字段 '{field_name}' 失败"
        }


async def submit_form(form_selector: Optional[str] = None, submit_button_text: Optional[str] = None) -> Dict[str, Any]:
    """
    提交表单

    Args:
        form_selector: 表单选择器 (可选, 默认提交第一个表单)
        submit_button_text: 提交按钮文本 (可选, 如 "登录", "提交")

    Returns:
        操作结果
    """
    try:
        browser = await get_browser_manager()

        if submit_button_text:
            # 通过按钮文本提交
            button_selectors = [
                f'button:has-text("{submit_button_text}")',
                f'input[type="submit"][value="{submit_button_text}"]',
                f'input[type="button"][value="{submit_button_text}"]'
            ]

            for selector in button_selectors:
                try:
                    await browser.click(selector, timeout=2000)
                    log.info(f"通过按钮提交表单: {submit_button_text}")

                    # 等待导航或响应
                    await browser.page.wait_for_load_state("networkidle", timeout=5000)

                    return {
                        "success": True,
                        "method": "button_click",
                        "button_text": submit_button_text,
                        "message": f"成功通过按钮 '{submit_button_text}' 提交表单"
                    }
                except:
                    continue

        # 使用 JavaScript 提交表单
        if form_selector:
            submit_script = f'document.querySelector("{form_selector}").submit()'
        else:
            submit_script = 'document.querySelector("form").submit()'

        await browser.evaluate(submit_script)
        log.info("通过 JavaScript 提交表单")

        # 等待导航
        await browser.page.wait_for_load_state("networkidle", timeout=5000)

        return {
            "success": True,
            "method": "javascript",
            "message": "成功通过 JavaScript 提交表单"
        }
    except Exception as e:
        log.error(f"提交表单失败: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "message": "提交表单失败"
        }


async def test_form_with_payloads(
    form_fields: Dict[str, str],
    payloads: List[str],
    submit_button_text: Optional[str] = None,
    check_reflection: bool = True
) -> Dict[str, Any]:
    """
    使用多个 payload 测试表单 (用于 XSS, SQLi 等测试)

    Args:
        form_fields: 表单字段映射 {"field_name": "normal_value"}
        payloads: 要测试的 payload 列表
        submit_button_text: 提交按钮文本
        check_reflection: 是否检查 payload 反射

    Returns:
        测试结果
    """
    try:
        browser = await get_browser_manager()
        results = []

        log.info(f"开始表单 payload 测试, 共 {len(payloads)} 个 payload")

        for i, payload in enumerate(payloads):
            log.info(f"测试 payload {i+1}/{len(payloads)}: {payload[:50]}...")

            # 清空事件缓存
            browser.clear_event_caches()

            # 获取当前 URL (用于重新加载)
            current_url = await browser.get_url()

            # 填充表单 (将第一个字段替换为 payload)
            field_names = list(form_fields.keys())
            for j, (field_name, value) in enumerate(form_fields.items()):
                # 第一个字段使用 payload, 其他字段使用正常值
                fill_value = payload if j == 0 else value
                await fill_input_by_name(field_name, fill_value)

            # 提交表单
            submit_result = await submit_form(submit_button_text=submit_button_text)

            if not submit_result.get("success"):
                results.append({
                    "payload": payload,
                    "success": False,
                    "error": "提交失败"
                })
                continue

            # 等待页面稳定
            await browser.page.wait_for_timeout(1000)

            # 检查结果
            test_result = {
                "payload": payload,
                "success": True,
                "triggered_dialog": False,
                "has_js_errors": False,
                "reflected_in_page": False,
                "console_errors": []
            }

            # 检查是否触发了 dialog (XSS 证据)
            dialogs = browser.get_dialog_events(limit=10)
            if dialogs:
                test_result["triggered_dialog"] = True
                test_result["dialogs"] = dialogs
                log.warning(f"Payload 触发了 dialog: {payload}")

            # 检查 JavaScript 错误
            js_errors = browser.get_js_errors(limit=10)
            if js_errors:
                test_result["has_js_errors"] = True
                test_result["js_errors"] = js_errors

            # 检查 console 错误
            console_logs = browser.get_console_logs(limit=20, log_type="error")
            if console_logs:
                test_result["console_errors"] = console_logs

            # 检查 payload 是否反射到页面
            if check_reflection:
                page_content = await browser.get_content()
                if payload in page_content:
                    test_result["reflected_in_page"] = True
                    log.info(f"Payload 反射到页面: {payload}")

            results.append(test_result)

            # 重新加载页面准备下一次测试
            if i < len(payloads) - 1:
                await browser.goto(current_url, wait_until="networkidle")

        # 统计结果
        triggered_count = sum(1 for r in results if r.get("triggered_dialog"))
        reflected_count = sum(1 for r in results if r.get("reflected_in_page"))

        log.info(f"表单 payload 测试完成: {triggered_count} 个触发 dialog, {reflected_count} 个反射到页面")

        return {
            "success": True,
            "total_payloads": len(payloads),
            "triggered_dialog_count": triggered_count,
            "reflected_count": reflected_count,
            "vulnerable": triggered_count > 0 or reflected_count > 0,
            "severity": "高" if triggered_count > 0 else ("中" if reflected_count > 0 else "无"),
            "results": results,
            "message": f"测试完成: {triggered_count} 个 payload 触发执行, {reflected_count} 个反射到页面"
        }
    except Exception as e:
        log.error(f"表单 payload 测试失败: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "message": "表单 payload 测试失败"
        }
