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
    close_browser
)
from tools.web_scanner import (
    scan_directory,
    scan_subdomains,
    fuzz_parameters,
    check_common_files
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
    log.info(f"开始扫描目标: {target_url}")

    # 创建扫描 Agent，并提供工具
    scanner_tools = [
        navigate_to_url,
        take_screenshot,
        check_common_files,
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
    """

    try:
        result = await scanner_agent.run(task)
        console.print("\n[green]扫描完成[/green]")

        # 提取扫描结果文本
        scan_text = ""
        for msg in result.messages:
            if hasattr(msg, 'content') and isinstance(msg.content, str):
                scan_text += msg.content + "\n\n"

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
    """

    try:
        result = await analyst_agent.run(task)
        console.print("\n[green]漏洞测试完成[/green]")

        # 提取测试结果文本
        test_text = ""
        for msg in result.messages:
            if hasattr(msg, 'content') and isinstance(msg.content, str):
                test_text += msg.content + "\n\n"

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
    log.info(f"开始浏览器自动化测试: {target_url}")

    # 创建浏览器自动化 Agent
    browser_tools = [
        navigate_to_url,
        take_screenshot,
        fill_form,
        click_element,
        get_page_content,
        execute_javascript,
        wait_for_element,
    ]

    browser_agent = BrowserAutomationAgent(tools=browser_tools)

    task = f"""
    请使用浏览器自动化工具测试 {target_url}：

    1. 访问目标网站
    2. 截取首页截图
    3. 分析页面结构
    4. 查找登录表单
    5. 测试表单输入

    请详细记录每一步操作。
    """

    try:
        result = await browser_agent.run(task)
        console.print("\n[green]浏览器自动化测试完成[/green]")

        # 提取测试结果文本
        automation_text = ""
        for msg in result.messages:
            if hasattr(msg, 'content') and isinstance(msg.content, str):
                automation_text += msg.content + "\n\n"

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
