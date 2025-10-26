"""
交互式渗透测试工具
提供友好的命令行界面进行安全测试
"""
import asyncio
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any

sys.path.insert(0, str(Path(__file__).parent))

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich import box
from rich.markdown import Markdown

from tools.web_scanner import check_common_files, scan_directory, fuzz_parameters
from tools.vulnerability_scanner import test_sql_injection, test_xss, test_lfi, test_open_redirect
from tools.browser_tools import navigate_to_url, take_screenshot, get_page_content, close_browser
from tools.advanced_report_generator import generate_advanced_html_report
from utils.logger import log

console = Console()


class InteractiveTester:
    """交互式测试器"""
    
    def __init__(self):
        self.target_url = ""
        self.results = {
            "target": "",
            "start_time": "",
            "end_time": "",
            "tests": []
        }
    
    def show_banner(self):
        """显示欢迎横幅"""
        banner = """
╔═══════════════════════════════════════════════════════════╗
║                                                           ║
║        LSJ WebSec Automation - 交互式测试工具             ║
║                                                           ║
║        基于 Autogen + Playwright 的自动化渗透测试         ║
║                                                           ║
╚═══════════════════════════════════════════════════════════╝
        """
        console.print(banner, style="bold cyan")
    
    def show_menu(self) -> str:
        """显示主菜单"""
        console.print("\n")
        menu_table = Table(show_header=False, box=box.ROUNDED, border_style="cyan")
        menu_table.add_column("选项", style="bold yellow", width=10)
        menu_table.add_column("功能", style="white")
        
        menu_table.add_row("1", "敏感文件检测")
        menu_table.add_row("2", "目录扫描")
        menu_table.add_row("3", "SQL 注入测试")
        menu_table.add_row("4", "XSS 跨站脚本测试")
        menu_table.add_row("5", "本地文件包含测试")
        menu_table.add_row("6", "开放重定向测试")
        menu_table.add_row("7", "浏览器访问测试")
        menu_table.add_row("8", "全面扫描（所有测试）")
        menu_table.add_row("9", "生成测试报告")
        menu_table.add_row("0", "退出")
        
        console.print(menu_table)
        
        choice = Prompt.ask(
            "\n请选择功能",
            choices=["0", "1", "2", "3", "4", "5", "6", "7", "8", "9"],
            default="8"
        )
        return choice
    
    async def test_sensitive_files(self):
        """测试敏感文件"""
        console.print("\n[bold cyan]敏感文件检测[/bold cyan]")
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("正在扫描敏感文件...", total=None)
            
            result = await check_common_files(self.target_url)
            progress.update(task, completed=True)
        
        if result['success']:
            table = Table(title="发现的敏感文件", box=box.ROUNDED)
            table.add_column("文件", style="cyan")
            table.add_column("状态码", style="green")
            table.add_column("大小", style="yellow")
            
            for item in result['results']:
                table.add_row(
                    item['file'],
                    str(item['status_code']),
                    str(item.get('size', 'N/A'))
                )
            
            console.print(table)
            console.print(f"\n[bold green]成功[/bold green] 发现 {result['found']} 个敏感文件")
        else:
            console.print(f"[bold red]错误[/bold red] 扫描失败: {result.get('error')}")
        
        self.results['tests'].append({
            "type": "敏感文件检测",
            "result": result,
            "timestamp": datetime.now().isoformat()
        })
    
    async def test_directory_scan(self):
        """目录扫描"""
        console.print("\n[bold cyan]目录扫描[/bold cyan]")
        
        wordlist_path = "wordlists/common_dirs.txt"
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("正在扫描目录...", total=None)
            
            result = await scan_directory(self.target_url, wordlist_path)
            progress.update(task, completed=True)
        
        if result['success']:
            table = Table(title="发现的目录", box=box.ROUNDED)
            table.add_column("目录", style="cyan")
            table.add_column("状态码", style="green")
            table.add_column("大小", style="yellow")
            
            for item in result['results'][:20]:  # 只显示前20个
                table.add_row(
                    item['directory'],
                    str(item['status_code']),
                    str(item.get('size', 'N/A'))
                )
            
            console.print(table)
            console.print(f"\n[bold green]成功[/bold green] 发现 {result['found']} 个目录")
            if result['found'] > 20:
                console.print(f"[dim]（仅显示前 20 个结果）[/dim]")
        else:
            console.print(f"[bold red]错误[/bold red] 扫描失败: {result.get('error')}")
        
        self.results['tests'].append({
            "type": "目录扫描",
            "result": result,
            "timestamp": datetime.now().isoformat()
        })
    
    async def test_sql_injection(self):
        """SQL 注入测试"""
        console.print("\n[bold cyan]SQL 注入测试[/bold cyan]")
        
        # 询问测试参数
        test_url = Prompt.ask("请输入测试 URL", default=f"{self.target_url}/artists.php")
        param_name = Prompt.ask("请输入参数名", default="artist")
        param_value = Prompt.ask("请输入参数值", default="1")
        
        params = {param_name: param_value}
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("正在测试 SQL 注入...", total=None)
            
            result = await test_sql_injection(test_url, params)
            progress.update(task, completed=True)
        
        if result['success']:
            if result['count'] > 0:
                table = Table(title="发现的 SQL 注入点", box=box.ROUNDED, border_style="red")
                table.add_column("参数", style="cyan")
                table.add_column("Payload", style="yellow")
                table.add_column("检测方法", style="green")
                
                for vuln in result['vulnerabilities'][:10]:  # 只显示前10个
                    table.add_row(
                        vuln['parameter'],
                        vuln['payload'][:50] + "..." if len(vuln['payload']) > 50 else vuln['payload'],
                        vuln['detection_method']
                    )
                
                console.print(table)
                console.print(f"\n[bold red]警告[/bold red] 发现 {result['count']} 个可能的 SQL 注入点")
            else:
                console.print("[bold green]未发现 SQL 注入漏洞[/bold green]")
        else:
            console.print(f"[bold red]错误[/bold red] 测试失败: {result.get('error')}")
        
        self.results['tests'].append({
            "type": "SQL 注入测试",
            "result": result,
            "timestamp": datetime.now().isoformat()
        })
    
    async def test_xss(self):
        """XSS 测试"""
        console.print("\n[bold cyan]XSS 跨站脚本测试[/bold cyan]")
        
        # 询问测试参数
        test_url = Prompt.ask("请输入测试 URL", default=f"{self.target_url}/artists.php")
        param_name = Prompt.ask("请输入参数名", default="artist")
        param_value = Prompt.ask("请输入参数值", default="test")
        
        params = {param_name: param_value}
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("正在测试 XSS...", total=None)
            
            result = await test_xss(test_url, params)
            progress.update(task, completed=True)
        
        if result['success']:
            if result['count'] > 0:
                table = Table(title="发现的 XSS 漏洞", box=box.ROUNDED, border_style="red")
                table.add_column("参数", style="cyan")
                table.add_column("Payload", style="yellow")
                table.add_column("类型", style="green")
                
                for vuln in result['vulnerabilities']:
                    table.add_row(
                        vuln['parameter'],
                        vuln['payload'][:60] + "..." if len(vuln['payload']) > 60 else vuln['payload'],
                        vuln['type']
                    )
                
                console.print(table)
                console.print(f"\n[bold red]警告[/bold red] 发现 {result['count']} 个可能的 XSS 漏洞")
            else:
                console.print("[bold green]未发现 XSS 漏洞[/bold green]")
        else:
            console.print(f"[bold red]错误[/bold red] 测试失败: {result.get('error')}")
        
        self.results['tests'].append({
            "type": "XSS 测试",
            "result": result,
            "timestamp": datetime.now().isoformat()
        })
    
    async def test_browser_access(self):
        """浏览器访问测试"""
        console.print("\n[bold cyan]浏览器访问测试[/bold cyan]")
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task1 = progress.add_task("正在访问网站...", total=None)
            nav_result = await navigate_to_url(self.target_url)
            progress.update(task1, completed=True)
            
            task2 = progress.add_task("正在截图...", total=None)
            screenshot_name = f"test_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            screenshot_result = await take_screenshot(screenshot_name)
            progress.update(task2, completed=True)
        
        if nav_result['success']:
            info_table = Table(title="页面信息", box=box.ROUNDED)
            info_table.add_column("项目", style="cyan")
            info_table.add_column("值", style="white")
            
            info_table.add_row("URL", nav_result['url'])
            info_table.add_row("标题", nav_result['title'])
            info_table.add_row("截图", screenshot_result.get('path', 'N/A'))
            
            console.print(info_table)
            console.print(f"\n[bold green]成功[/bold green] 浏览器访问成功")
        else:
            console.print(f"[bold red]错误[/bold red] 访问失败: {nav_result.get('error')}")
        
        self.results['tests'].append({
            "type": "浏览器访问",
            "result": {"navigation": nav_result, "screenshot": screenshot_result},
            "timestamp": datetime.now().isoformat()
        })
    
    async def run_full_scan(self):
        """运行全面扫描"""
        console.print("\n[bold cyan]开始全面扫描[/bold cyan]\n")
        
        tests = [
            ("敏感文件检测", self.test_sensitive_files),
            ("浏览器访问", self.test_browser_access),
            ("SQL 注入测试", self.test_sql_injection),
            ("XSS 测试", self.test_xss),
        ]
        
        for test_name, test_func in tests:
            console.print(f"\n[bold yellow]>>> {test_name}[/bold yellow]")
            await test_func()
            await asyncio.sleep(1)  # 短暂延迟
        
        console.print("\n[bold green]全面扫描完成[/bold green]")
    
    def generate_report(self):
        """生成测试报告"""
        console.print("\n[bold cyan]生成测试报告[/bold cyan]")

        if not self.results['tests']:
            console.print("[bold red]错误[/bold red] 没有测试数据，请先运行测试")
            return

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("正在生成报告...", total=None)

            # 生成高级 HTML 报告
            html_path = generate_advanced_html_report(self.results, f"report_{timestamp}.html")

            progress.update(task, completed=True)

        report_table = Table(title="报告已生成", box=box.ROUNDED, border_style="green")
        report_table.add_column("格式", style="cyan", width=15)
        report_table.add_column("路径", style="white")

        report_table.add_row("HTML", html_path)

        console.print(report_table)
        console.print(f"\n[bold green]报告生成成功！[/bold green]")
        console.print(f"\n[dim]提示: 在浏览器中打开 HTML 报告查看详细结果[/dim]")
    
    async def run(self):
        """运行交互式测试"""
        self.show_banner()
        
        # 获取目标 URL
        self.target_url = Prompt.ask(
            "\n[bold cyan]请输入目标 URL[/bold cyan]",
            default="http://testphp.vulnweb.com"
        )
        
        self.results['target'] = self.target_url
        self.results['start_time'] = datetime.now().isoformat()
        
        console.print(f"\n[bold green]目标设置为: {self.target_url}[/bold green]")
        
        try:
            while True:
                choice = self.show_menu()
                
                if choice == "0":
                    console.print("\n[bold yellow]感谢使用，再见！[/bold yellow]\n")
                    break
                elif choice == "1":
                    await self.test_sensitive_files()
                elif choice == "2":
                    await self.test_directory_scan()
                elif choice == "3":
                    await self.test_sql_injection()
                elif choice == "4":
                    await self.test_xss()
                elif choice == "7":
                    await self.test_browser_access()
                elif choice == "8":
                    await self.run_full_scan()
                elif choice == "9":
                    self.generate_report()
                
                # 询问是否继续
                if choice != "0" and choice != "9":
                    if not Confirm.ask("\n继续测试？", default=True):
                        if Confirm.ask("是否生成报告？", default=True):
                            self.generate_report()
                        break
        
        finally:
            self.results['end_time'] = datetime.now().isoformat()
            await close_browser()


async def main():
    """主函数"""
    tester = InteractiveTester()
    await tester.run()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        console.print("\n\n[bold yellow]警告：用户中断[/bold yellow]\n")
    except Exception as e:
        console.print(f"\n[bold red]错误: {str(e)}[/bold red]\n")
        log.error(f"程序错误: {str(e)}")
