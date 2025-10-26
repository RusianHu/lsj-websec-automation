"""
自动化测试脚本
无需交互，自动执行完整测试并生成报告
"""
import asyncio
import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent))

from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.table import Table
from rich import box

from tools.web_scanner import check_common_files
from tools.vulnerability_scanner import test_sql_injection, test_xss
from tools.browser_tools import navigate_to_url, take_screenshot, close_browser
from tools.advanced_report_generator import generate_advanced_html_report
from utils.logger import log

console = Console()


async def run_auto_test(target_url: str = "http://yanshanlaosiji.top"):
    """运行自动化测试"""
    
    # 显示横幅
    console.print(Panel.fit(
        "[bold cyan]LSJ WebSec Automation - 自动化测试[/bold cyan]\n"
        f"目标: {target_url}\n"
        f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        border_style="cyan"
    ))
    
    # 初始化结果
    results = {
        "target": target_url,
        "start_time": datetime.now().isoformat(),
        "tests": []
    }
    
    # 创建进度条
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        console=console
    ) as progress:
        
        # 总任务
        main_task = progress.add_task("[cyan]执行测试...", total=4)
        
        # 1. 敏感文件检测
        progress.update(main_task, description="[cyan]1/4 敏感文件检测...")
        console.print("\n[bold yellow]>>> 敏感文件检测[/bold yellow]")
        
        try:
            result = await check_common_files(target_url)
            results['tests'].append({
                "type": "敏感文件检测",
                "result": result,
                "timestamp": datetime.now().isoformat()
            })
            
            if result['success']:
                console.print(f"[green]成功[/green] 发现 {result['found']} 个敏感文件")
            else:
                console.print("[red]失败[/red] 扫描失败")
        except Exception as e:
            console.print(f"[red]错误: {str(e)}[/red]")
            log.error(f"敏感文件检测失败: {str(e)}")
        
        progress.update(main_task, advance=1)
        await asyncio.sleep(0.5)
        
        # 2. 浏览器访问
        progress.update(main_task, description="[cyan]2/4 浏览器访问...")
        console.print("\n[bold yellow]>>> 浏览器访问测试[/bold yellow]")
        
        try:
            nav_result = await navigate_to_url(target_url)
            screenshot_name = f"auto_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            screenshot_result = await take_screenshot(screenshot_name)
            
            results['tests'].append({
                "type": "浏览器访问",
                "result": {
                    "navigation": nav_result,
                    "screenshot": screenshot_result
                },
                "timestamp": datetime.now().isoformat()
            })
            
            if nav_result['success']:
                console.print(f"[green]成功[/green] 访问成功: {nav_result['title']}")
            else:
                console.print("[red]失败[/red] 访问失败")
        except Exception as e:
            console.print(f"[red]错误: {str(e)}[/red]")
            log.error(f"浏览器访问失败: {str(e)}")
        
        progress.update(main_task, advance=1)
        await asyncio.sleep(0.5)
        
        # 3. SQL 注入测试
        progress.update(main_task, description="[cyan]3/4 SQL 注入测试...")
        console.print("\n[bold yellow]>>> SQL 注入测试[/bold yellow]")
        
        try:
            test_url = f"{target_url}/artists.php"
            params = {"artist": "1"}
            
            result = await test_sql_injection(test_url, params)
            results['tests'].append({
                "type": "SQL 注入测试",
                "result": result,
                "timestamp": datetime.now().isoformat()
            })
            
            if result['success']:
                if result['count'] > 0:
                    console.print(f"[red]警告[/red] 发现 {result['count']} 个可能的 SQL 注入点")
                else:
                    console.print("[green]未发现 SQL 注入漏洞[/green]")
            else:
                console.print("[red]失败[/red] 测试失败")
        except Exception as e:
            console.print(f"[red]错误: {str(e)}[/red]")
            log.error(f"SQL 注入测试失败: {str(e)}")
        
        progress.update(main_task, advance=1)
        await asyncio.sleep(0.5)
        
        # 4. XSS 测试
        progress.update(main_task, description="[cyan]4/4 XSS 测试...")
        console.print("\n[bold yellow]>>> XSS 跨站脚本测试[/bold yellow]")
        
        try:
            test_url = f"{target_url}/artists.php"
            params = {"artist": "test"}
            
            result = await test_xss(test_url, params)
            results['tests'].append({
                "type": "XSS 测试",
                "result": result,
                "timestamp": datetime.now().isoformat()
            })
            
            if result['success']:
                if result['count'] > 0:
                    console.print(f"[red]警告[/red] 发现 {result['count']} 个可能的 XSS 漏洞")
                else:
                    console.print("[green]未发现 XSS 漏洞[/green]")
            else:
                console.print("[red]失败[/red] 测试失败")
        except Exception as e:
            console.print(f"[red]错误: {str(e)}[/red]")
            log.error(f"XSS 测试失败: {str(e)}")
        
        progress.update(main_task, advance=1)
    
    # 完成测试
    results['end_time'] = datetime.now().isoformat()
    
    # 显示总结
    console.print("\n")
    console.print(Panel.fit(
        "[bold green]测试完成[/bold green]",
        border_style="green"
    ))
    
    # 统计信息
    stats_table = Table(title="测试统计", box=box.ROUNDED, border_style="cyan")
    stats_table.add_column("项目", style="cyan")
    stats_table.add_column("结果", style="white")
    
    total_tests = len(results['tests'])
    sql_count = 0
    xss_count = 0
    files_count = 0
    
    for test in results['tests']:
        if 'SQL' in test['type']:
            sql_count = test['result'].get('count', 0)
        elif 'XSS' in test['type']:
            xss_count = test['result'].get('count', 0)
        elif '敏感文件' in test['type']:
            files_count = test['result'].get('found', 0)
    
    stats_table.add_row("执行测试", str(total_tests))
    stats_table.add_row("SQL 注入", f"{sql_count} 个")
    stats_table.add_row("XSS 漏洞", f"{xss_count} 个")
    stats_table.add_row("敏感文件", f"{files_count} 个")
    
    console.print(stats_table)
    
    # 生成报告
    console.print("\n[bold cyan]生成测试报告...[/bold cyan]")
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    try:
        html_path = generate_advanced_html_report(results, f"auto_report_{timestamp}.html")

        report_table = Table(title="报告已生成", box=box.ROUNDED, border_style="green")
        report_table.add_column("格式", style="cyan", width=15)
        report_table.add_column("路径", style="white")

        report_table.add_row("HTML", html_path)

        console.print(report_table)
        console.print(f"\n[bold green]报告生成成功！[/bold green]")
        console.print(f"[dim]在浏览器中打开 HTML 报告查看详细结果[/dim]\n")

    except Exception as e:
        console.print(f"[red]报告生成失败: {str(e)}[/red]")
        log.error(f"报告生成失败: {str(e)}")
    
    # 清理
    await close_browser()
    
    return results


async def main():
    """主函数"""
    
    # 可以从命令行参数获取目标 URL
    target = sys.argv[1] if len(sys.argv) > 1 else "http://testphp.vulnweb.com"
    
    try:
        await run_auto_test(target)
    except KeyboardInterrupt:
        console.print("\n[yellow]警告：用户中断[/yellow]")
    except Exception as e:
        console.print(f"\n[red]错误: {str(e)}[/red]")
        log.error(f"程序错误: {str(e)}")
    finally:
        await close_browser()


if __name__ == "__main__":
    asyncio.run(main())
