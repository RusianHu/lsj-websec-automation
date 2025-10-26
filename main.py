"""
LSJ WebSec Automation - 主程序入口
基于 Autogen + Playwright 的自动化渗透测试工具
"""
import asyncio
from typing import Optional
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from utils.logger import log
from utils.url_helper import normalize_url
from config.settings import settings

# 根据配置决定是否应用 Autogen 兼容性补丁
if settings.app.enable_autogen_patch:
    from utils.patch_autogen import apply_patch
    apply_patch()
    log.info("Autogen 兼容性补丁已启用(用于修复某些 OpenAI 兼容服务器的 additionalProperties 字段问题)")
else:
    log.info("Autogen 兼容性补丁未启用(使用标准 OpenAI API 模式)")
from agents.pentest_agent import (
    WebScannerAgent,
    VulnerabilityAnalystAgent,
    BrowserAutomationAgent,
    ReportGeneratorAgent
)
from tools.browser_tools import (
    navigate_to_url,
    take_screenshot,
    fill_form,
    click_element,
    get_page_content,
    execute_javascript,
    wait_for_element,
    find_forms,
    find_links,
    analyze_page_structure,
    # 观测与安全头
    get_console_logs,
    get_js_errors,
    get_dialog_events,
    get_network_events,
    analyze_security_headers,
    clear_event_caches,
    # 表单高级
    fill_input_by_name,
    submit_form,
    test_form_with_payloads,
    # 关闭
    close_browser,
)
from tools.web_scanner import (
    scan_directory,
    scan_subdomains,
    fuzz_parameters,
    check_common_files,
    # 新增快用/高级工具
    quick_directory_scan,
    quick_subdomain_scan,
    quick_param_fuzz,
    discover_api_endpoints,
    fuzzing_headers,
)
from tools.vulnerability_scanner import (
    test_sql_injection,
    test_xss,
    test_lfi,
    test_open_redirect
)
from tools.report_generator import generate_html_report, generate_json_report

console = Console()


def print_banner():
    """打印欢迎横幅"""
    banner = """
╔═══════════════════════════════════════════════════════════╗
║                                                           ║
║        LSJ WebSec Automation                              ║
║        基于 Autogen + Playwright 的自动化渗透测试工具      ║
║                                                           ║
╚═══════════════════════════════════════════════════════════╝
    """
    console.print(Panel(banner, style="bold blue"))


async def run_web_scan(target_url: str):
    """
    运行 Web 扫描任务

    Args:
        target_url: 目标 URL
    """
    # 规范化 URL
    target_url = normalize_url(target_url)
    log.info(f"开始扫描目标: {target_url}")

    # 创建扫描 Agent，并提供工具（精简核心子集，规避服务端对超大工具清单的 500 错误）
    scanner_tools = [
        # 浏览器基础与页面分析（5）
        navigate_to_url,
        take_screenshot,
        analyze_page_structure,
        find_links,
        get_page_content,
        # 观测/安全（2）
        get_network_events,
        analyze_security_headers,
        # HTTP 轻量扫描（5）
        check_common_files,
        quick_directory_scan,
        discover_api_endpoints,
        fuzzing_headers,
        quick_param_fuzz,
    ]

    scanner_agent = WebScannerAgent(tools=scanner_tools)

    # 执行扫描任务
    task = f"""
    请对目标网站 {target_url} 进行安全扫描：

    1. 首先访问目标网站并截图
    2. 检查常见的敏感文件
    3. 分析网站结构
    4. 记录发现的问题

    请详细记录每一步的操作和发现。
    最后请在报告末尾单独一行输出 "TERMINATE" 表示完成。
    """

    try:
        result = await scanner_agent.run(task)
        console.print("\n[green]扫描完成[/green]")

        # 提取扫描结果文本（仅保留包含 TERMINATE 的最终总结，避免引入无关寒暄/反思内容）
        contents: list[str] = []
        for msg in result.messages:
            if hasattr(msg, 'content') and isinstance(msg.content, str):
                contents.append(msg.content)
        final_text = None
        for c in contents:
            if "TERMINATE" in c:
                final_text = c
                break
        if final_text is None and contents:
            final_text = contents[-1]
        if final_text:
            # 去掉单独的 TERMINATE 行
            lines = [ln for ln in final_text.splitlines() if "TERMINATE" not in ln.strip()]
            scan_text = "\n".join(lines).strip()
        else:
            scan_text = ""

        # 构建报告数据
        from datetime import datetime
        scan_results = {
            'target_url': target_url,
            'scan_time': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'scan_text': scan_text,
            'total_vulnerabilities': 0,  # 可以从扫描文本中提取
            'risk_level': '信息收集',
            'vulnerabilities': [],
            'directory_scan': [],
            'recommendations': [
                '定期更新系统和软件',
                '加强访问控制',
                '启用安全响应头',
            ]
        }

        # 生成报告
        console.print("\n[cyan]正在生成报告...[/cyan]")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        html_path = generate_html_report(scan_results,
                                        settings.app.reports_dir / f"web_scan_{timestamp}.html")
        json_path = generate_json_report(scan_results,
                                        settings.app.reports_dir / f"web_scan_{timestamp}.json")

        console.print(f"\n[green]✅ 报告已生成:[/green]")
        console.print(f"  HTML: {html_path}")
        console.print(f"  JSON: {json_path}")

        # 关闭 Agent
        await scanner_agent.close()

    except Exception as e:
        log.error(f"扫描失败: {str(e)}")
        console.print(f"[red]扫描失败: {str(e)}[/red]")
    finally:
        # 关闭浏览器
        await close_browser()


async def run_vulnerability_test(target_url: str):
    """
    运行漏洞测试

    Args:
        target_url: 目标 URL
    """
    # 规范化 URL
    target_url = normalize_url(target_url)
    log.info(f"开始漏洞测试: {target_url}")

    # 创建漏洞分析 Agent
    analyst_tools = [
        test_sql_injection,
        test_xss,
        test_lfi,
        test_open_redirect,
    ]

    analyst_agent = VulnerabilityAnalystAgent(tools=analyst_tools)

    task = f"""
    请对目标网站 {target_url} 进行漏洞测试：

    1. 测试 SQL 注入漏洞
    2. 测试 XSS 跨站脚本漏洞
    3. 测试本地文件包含漏洞
    4. 测试开放重定向漏洞

    对于每个测试，请详细记录测试过程和结果。
    最后请在报告末尾单独一行输出 "TERMINATE" 表示完成。
    """

    try:
        result = await analyst_agent.run(task)
        console.print("\n[green]漏洞测试完成[/green]")

        # 提取测试结果文本（仅保留包含 TERMINATE 的最终总结，避免引入无关寒暄/反思内容）
        contents: list[str] = []
        for msg in result.messages:
            if hasattr(msg, 'content') and isinstance(msg.content, str):
                contents.append(msg.content)
        final_text = None
        for c in contents:
            if "TERMINATE" in c:
                final_text = c
                break
        if final_text is None and contents:
            final_text = contents[-1]
        if final_text:
            # 去掉单独的 TERMINATE 行
            lines = [ln for ln in final_text.splitlines() if "TERMINATE" not in ln.strip()]
            test_text = "\n".join(lines).strip()
        else:
            test_text = ""

        # 构建报告数据
        from datetime import datetime
        test_results = {
            'target_url': target_url,
            'scan_time': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'scan_text': test_text,
            'total_vulnerabilities': 0,
            'risk_level': '漏洞测试',
            'vulnerabilities': [],
            'directory_scan': [],
            'recommendations': [
                '修复发现的漏洞',
                '加强输入验证',
                '使用参数化查询',
            ]
        }

        # 生成报告
        console.print("\n[cyan]正在生成报告...[/cyan]")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        html_path = generate_html_report(test_results,
                                        settings.app.reports_dir / f"vuln_test_{timestamp}.html")
        json_path = generate_json_report(test_results,
                                        settings.app.reports_dir / f"vuln_test_{timestamp}.json")

        console.print(f"\n[green]✅ 报告已生成:[/green]")
        console.print(f"  HTML: {html_path}")
        console.print(f"  JSON: {json_path}")

        await analyst_agent.close()

    except Exception as e:
        log.error(f"漏洞测试失败: {str(e)}")
        console.print(f"[red]漏洞测试失败: {str(e)}[/red]")


async def run_browser_automation(target_url: str):
    """
    运行浏览器自动化测试

    Args:
        target_url: 目标 URL
    """
    # 规范化 URL
    target_url = normalize_url(target_url)
    log.info(f"开始浏览器自动化测试: {target_url}")

    # 创建浏览器自动化 Agent
    from tools.browser_tools import (
        get_console_logs, get_js_errors, get_dialog_events,
        get_network_events, analyze_security_headers, clear_event_caches,
        fill_input_by_name, submit_form, test_form_with_payloads
    )

    browser_tools = [
        # 基础操作
        navigate_to_url,
        take_screenshot,
        fill_form,
        click_element,
        get_page_content,
        execute_javascript,
        wait_for_element,
        find_forms,
        find_links,
        analyze_page_structure,
        # 观测工具
        get_console_logs,
        get_js_errors,
        get_dialog_events,
        get_network_events,
        analyze_security_headers,
        clear_event_caches,
        # 高层表单测试
        fill_input_by_name,
        submit_form,
        test_form_with_payloads,
    ]

    browser_agent = BrowserAutomationAgent(tools=browser_tools)

    task = f"""
    请使用浏览器自动化工具对 {target_url} 进行完整的安全测试，必须完成以下所有步骤：

    第一步：访问和初步分析
    1.1 使用 navigate_to_url 工具访问目标网站
    1.2 使用 take_screenshot 工具截取首页截图
    1.3 使用 analyze_page_structure 工具分析页面整体结构
    1.4 使用 analyze_security_headers 工具检查 HTTP 安全响应头

    第二步：深入分析页面元素
    2.1 使用 find_forms 工具查找所有表单
    2.2 使用 find_links 工具查找所有链接
    2.3 使用 get_page_content 工具获取完整的 HTML 内容（仅获取前 2000 字符）

    第三步：表单安全测试（如果存在表单）
    3.1 使用 clear_event_caches 清空事件缓存
    3.2 使用 test_form_with_payloads 批量测试 XSS payload:
        - <script>alert('XSS')</script>
        - <img src=x onerror=alert('XSS')>
        - "><script>alert('XSS')</script>
    3.3 使用 get_dialog_events 检查是否触发了 alert (XSS 证据)
    3.4 使用 get_console_logs 检查控制台错误
    3.5 使用 get_js_errors 检查 JavaScript 运行时错误

    第四步：网络和 JavaScript 安全检测
    4.1 使用 get_network_events 获取网络请求和响应
    4.2 使用 execute_javascript 检查是否存在敏感信息泄露
    4.3 检查 Cookie 安全设置
    4.4 检查是否存在不安全的第三方脚本

    第五步：生成测试报告
    5.1 总结发现的所有安全问题（包括 XSS、安全头缺失、JS 错误等）
    5.2 列出测试过的功能点
    5.3 提供安全建议
    5.4 在报告末尾添加 "TERMINATE" 表示完成

    重要提示：
    - 必须按顺序完成所有步骤，不要跳过任何一步
    - 每一步都要实际调用相应的工具函数
    - 使用新的观测工具收集安全证据（console logs, dialogs, network events）
    - 详细记录每个工具调用的结果
    - 如果某个工具调用失败，记录错误信息并继续下一步
    - 最后必须提供完整的测试总结报告并说 "TERMINATE"
    """

    try:
        result = await browser_agent.run(task)
        console.print("\n[green]浏览器自动化测试完成[/green]")

        # 提取测试结果文本（仅保留包含 TERMINATE 的最终总结，避免引入无关寒暄/反思内容）
        contents: list[str] = []
        for msg in result.messages:
            if hasattr(msg, 'content') and isinstance(msg.content, str):
                contents.append(msg.content)
        final_text = None
        for c in contents:
            if "TERMINATE" in c:
                final_text = c
                break
        if final_text is None and contents:
            final_text = contents[-1]
        if final_text:
            # 去掉单独的 TERMINATE 行
            lines = [ln for ln in final_text.splitlines() if "TERMINATE" not in ln.strip()]
            automation_text = "\n".join(lines).strip()
        else:
            automation_text = ""

        # 构建报告数据
        from datetime import datetime
        automation_results = {
            'target_url': target_url,
            'scan_time': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'scan_text': automation_text,
            'total_vulnerabilities': 0,
            'risk_level': '自动化测试',
            'vulnerabilities': [],
            'directory_scan': [],
            'recommendations': [
                '检查表单验证',
                '测试用户交互流程',
                '验证页面功能',
            ]
        }

        # 生成报告
        console.print("\n[cyan]正在生成报告...[/cyan]")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        html_path = generate_html_report(automation_results,
                                        settings.app.reports_dir / f"browser_test_{timestamp}.html")
        json_path = generate_json_report(automation_results,
                                        settings.app.reports_dir / f"browser_test_{timestamp}.json")

        console.print(f"\n[green]✅ 报告已生成:[/green]")
        console.print(f"  HTML: {html_path}")
        console.print(f"  JSON: {json_path}")

        await browser_agent.close()

    except Exception as e:
        log.error(f"浏览器自动化测试失败: {str(e)}")
        console.print(f"[red]浏览器自动化测试失败: {str(e)}[/red]")
    finally:
        await close_browser()


async def interactive_mode():
    """交互式模式"""
    print_banner()
    
    console.print("\n[bold cyan]欢迎使用 LSJ WebSec Automation![/bold cyan]\n")
    
    while True:
        console.print("\n[bold]请选择操作:[/bold]")
        console.print("1. Web 扫描")
        console.print("2. 漏洞测试")
        console.print("3. 浏览器自动化测试")
        console.print("4. 完整测试（包含以上所有）")
        console.print("5. 退出")
        
        choice = Prompt.ask("\n请输入选项", choices=["1", "2", "3", "4", "5"], default="1")
        
        if choice == "5":
            console.print("\n[yellow]再见！[/yellow]")
            break
        
        target_url = Prompt.ask("\n请输入目标 URL", default="http://testphp.vulnweb.com")
        
        if choice == "1":
            await run_web_scan(target_url)
        elif choice == "2":
            await run_vulnerability_test(target_url)
        elif choice == "3":
            await run_browser_automation(target_url)
        elif choice == "4":
            await run_web_scan(target_url)
            await run_vulnerability_test(target_url)
            await run_browser_automation(target_url)


async def main():
    """主函数"""
    try:
        await interactive_mode()
    except KeyboardInterrupt:
        console.print("\n\n[yellow]程序被用户中断[/yellow]")
    except Exception as e:
        log.error(f"程序异常: {str(e)}")
        console.print(f"\n[red]程序异常: {str(e)}[/red]")
    finally:
        # 确保浏览器被关闭
        await close_browser()


if __name__ == "__main__":
    asyncio.run(main())
