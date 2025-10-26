"""
高级报告生成器
生成详细、美观、专业的安全测试报告
"""
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional

from config.settings import settings
from utils.logger import log


def _get_severity_info(count: int) -> tuple:
    """根据漏洞数量获取严重程度信息"""
    if count == 0:
        return "安全", "#28a745", "OK"
    elif count <= 3:
        return "低危", "#ffc107", "LOW"
    elif count <= 10:
        return "中危", "#fd7e14", "MED"
    else:
        return "高危", "#dc3545", "HIGH"


def _calculate_statistics(results: Dict[str, Any]) -> Dict[str, Any]:
    """计算统计信息"""
    stats = {
        "total_tests": len(results.get('tests', [])),
        "sql_injection": 0,
        "xss": 0,
        "lfi": 0,
        "open_redirect": 0,
        "sensitive_files": 0,
        "directories": 0,
        "total_vulnerabilities": 0
    }
    
    for test in results.get('tests', []):
        test_type = test.get('type', '')
        test_result = test.get('result', {})
        
        if 'SQL' in test_type:
            stats['sql_injection'] = test_result.get('count', 0)
        elif 'XSS' in test_type:
            stats['xss'] = test_result.get('count', 0)
        elif 'LFI' in test_type or '文件包含' in test_type:
            stats['lfi'] = test_result.get('count', 0)
        elif '重定向' in test_type:
            stats['open_redirect'] = test_result.get('count', 0)
        elif '敏感文件' in test_type:
            stats['sensitive_files'] = test_result.get('found', 0)
        elif '目录' in test_type:
            stats['directories'] = test_result.get('found', 0)
    
    stats['total_vulnerabilities'] = (
        stats['sql_injection'] + 
        stats['xss'] + 
        stats['lfi'] + 
        stats['open_redirect']
    )
    
    return stats


def generate_advanced_html_report(results: Dict[str, Any], filename: Optional[str] = None) -> str:
    """
    生成高级 HTML 报告
    
    Args:
        results: 测试结果字典
        filename: 输出文件名
        
    Returns:
        报告文件路径
    """
    if filename is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"report_{timestamp}.html"
    
    output_path = settings.app.reports_dir / filename
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # 计算统计信息
    stats = _calculate_statistics(results)
    severity_label, severity_color, severity_icon = _get_severity_info(stats['total_vulnerabilities'])
    
    # 生成时间信息
    start_time = results.get('start_time', '')
    end_time = results.get('end_time', '')
    if start_time and end_time:
        try:
            start_dt = datetime.fromisoformat(start_time)
            end_dt = datetime.fromisoformat(end_time)
            duration = (end_dt - start_dt).total_seconds()
            duration_str = f"{int(duration // 60)}分{int(duration % 60)}秒"
        except:
            duration_str = "N/A"
    else:
        duration_str = "N/A"
    
    html_content = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Web 安全测试报告 - {results.get('target', 'Unknown')}</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: 'Segoe UI', 'Microsoft YaHei', Arial, sans-serif;
            line-height: 1.6;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px;
        }}
        
        .container {{
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            border-radius: 15px;
            overflow: hidden;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
        }}
        
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 40px;
            text-align: center;
        }}
        
        .header h1 {{
            font-size: 3em;
            margin-bottom: 10px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.2);
        }}
        
        .header .subtitle {{
            font-size: 1.2em;
            opacity: 0.9;
        }}
        
        .summary {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            padding: 40px;
            background: #f8f9fa;
        }}
        
        .summary-card {{
            background: white;
            padding: 25px;
            border-radius: 10px;
            text-align: center;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            transition: transform 0.3s;
        }}
        
        .summary-card:hover {{
            transform: translateY(-5px);
            box-shadow: 0 8px 12px rgba(0,0,0,0.15);
        }}
        
        .summary-card .icon {{
            font-size: 3em;
            margin-bottom: 10px;
        }}
        
        .summary-card .value {{
            font-size: 2.5em;
            font-weight: bold;
            color: #667eea;
            margin: 10px 0;
        }}
        
        .summary-card .label {{
            color: #666;
            font-size: 0.9em;
        }}
        
        .severity-badge {{
            display: inline-block;
            padding: 8px 20px;
            border-radius: 20px;
            font-weight: bold;
            font-size: 1.1em;
            background: {severity_color};
            color: white;
        }}
        
        .section {{
            padding: 40px;
            border-bottom: 1px solid #eee;
        }}
        
        .section:last-child {{
            border-bottom: none;
        }}
        
        .section h2 {{
            font-size: 2em;
            color: #333;
            margin-bottom: 25px;
            padding-bottom: 15px;
            border-bottom: 3px solid #667eea;
        }}
        
        .test-result {{
            background: #f8f9fa;
            padding: 25px;
            margin: 20px 0;
            border-radius: 10px;
            border-left: 5px solid #667eea;
        }}
        
        .test-result h3 {{
            color: #667eea;
            font-size: 1.5em;
            margin-bottom: 15px;
        }}
        
        .vulnerability-list {{
            margin-top: 15px;
        }}
        
        .vulnerability-item {{
            background: white;
            padding: 15px;
            margin: 10px 0;
            border-radius: 8px;
            border-left: 4px solid #ffc107;
        }}
        
        .vulnerability-item.high {{
            border-left-color: #dc3545;
            background: #fff5f5;
        }}
        
        .vulnerability-item.medium {{
            border-left-color: #fd7e14;
            background: #fff8f0;
        }}
        
        .vulnerability-item.low {{
            border-left-color: #ffc107;
            background: #fffbf0;
        }}
        
        .vulnerability-item .param {{
            font-weight: bold;
            color: #667eea;
        }}
        
        .vulnerability-item .payload {{
            font-family: 'Courier New', monospace;
            background: #f0f0f0;
            padding: 5px 10px;
            border-radius: 4px;
            display: inline-block;
            margin: 5px 0;
            word-break: break-all;
        }}
        
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
            background: white;
            border-radius: 8px;
            overflow: hidden;
        }}
        
        th {{
            background: #667eea;
            color: white;
            padding: 15px;
            text-align: left;
            font-weight: 600;
        }}
        
        td {{
            padding: 12px 15px;
            border-bottom: 1px solid #eee;
        }}
        
        tr:hover {{
            background: #f8f9fa;
        }}
        
        .status-ok {{
            color: #28a745;
            font-weight: bold;
        }}
        
        .status-warning {{
            color: #ffc107;
            font-weight: bold;
        }}
        
        .status-danger {{
            color: #dc3545;
            font-weight: bold;
        }}
        
        .footer {{
            background: #2c3e50;
            color: white;
            text-align: center;
            padding: 30px;
        }}
        
        .footer p {{
            margin: 5px 0;
            opacity: 0.8;
        }}
        
        .chart-container {{
            margin: 30px 0;
            padding: 20px;
            background: white;
            border-radius: 10px;
        }}
        
        @media print {{
            body {{
                background: white;
                padding: 0;
            }}
            .container {{
                box-shadow: none;
            }}
            .summary-card:hover {{
                transform: none;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Web 安全测试报告</h1>
            <p class="subtitle">LSJ WebSec Automation - 自动化渗透测试</p>
            <p style="margin-top: 20px;">生成时间: {datetime.now().strftime("%Y年%m月%d日 %H:%M:%S")}</p>
        </div>
        
        <div class="summary">
            <div class="summary-card">
                <div class="icon">目标</div>
                <div class="label">目标网站</div>
                <div class="value" style="font-size: 1.2em; word-break: break-all;">{results.get('target', 'N/A')}</div>
            </div>
            
            <div class="summary-card">
                <div class="icon">耗时</div>
                <div class="label">扫描耗时</div>
                <div class="value">{duration_str}</div>
            </div>
            
            <div class="summary-card">
                <div class="icon">测试</div>
                <div class="label">执行测试</div>
                <div class="value">{stats['total_tests']}</div>
            </div>
            
            <div class="summary-card">
                <div class="icon">{severity_icon}</div>
                <div class="label">发现漏洞</div>
                <div class="value" style="color: {severity_color};">{stats['total_vulnerabilities']}</div>
                <div class="severity-badge">{severity_label}</div>
            </div>
        </div>
        
        <div class="section">
            <h2>漏洞统计</h2>
            <table>
                <tr>
                    <th>漏洞类型</th>
                    <th>数量</th>
                    <th>风险等级</th>
                </tr>
                <tr>
                    <td>SQL 注入</td>
                    <td class="{'status-danger' if stats['sql_injection'] > 0 else 'status-ok'}">{stats['sql_injection']}</td>
                    <td>{_get_severity_info(stats['sql_injection'])[0]}</td>
                </tr>
                <tr>
                    <td>XSS 跨站脚本</td>
                    <td class="{'status-danger' if stats['xss'] > 0 else 'status-ok'}">{stats['xss']}</td>
                    <td>{_get_severity_info(stats['xss'])[0]}</td>
                </tr>
                <tr>
                    <td>本地文件包含</td>
                    <td class="{'status-danger' if stats['lfi'] > 0 else 'status-ok'}">{stats['lfi']}</td>
                    <td>{_get_severity_info(stats['lfi'])[0]}</td>
                </tr>
                <tr>
                    <td>开放重定向</td>
                    <td class="{'status-danger' if stats['open_redirect'] > 0 else 'status-ok'}">{stats['open_redirect']}</td>
                    <td>{_get_severity_info(stats['open_redirect'])[0]}</td>
                </tr>
                <tr>
                    <td>敏感文件</td>
                    <td class="{'status-warning' if stats['sensitive_files'] > 0 else 'status-ok'}">{stats['sensitive_files']}</td>
                    <td>{_get_severity_info(stats['sensitive_files'])[0]}</td>
                </tr>
                <tr>
                    <td>可访问目录</td>
                    <td class="status-ok">{stats['directories']}</td>
                    <td>信息</td>
                </tr>
            </table>
        </div>
        
        {_generate_detailed_results_html(results)}
        
        <div class="footer">
            <p><strong>LSJ WebSec Automation</strong></p>
            <p>基于 Autogen + Playwright 的自动化渗透测试工具</p>
            <p>Copyright {datetime.now().year} - 仅供授权安全测试使用</p>
            <p style="margin-top: 15px; font-size: 0.9em;">
                警告：未经授权对他人系统进行渗透测试是违法行为
            </p>
        </div>
    </div>
</body>
</html>"""
    
    # 写入文件
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    log.info(f"高级 HTML 报告已生成: {output_path}")
    return str(output_path)


def _generate_detailed_results_html(results: Dict[str, Any]) -> str:
    """生成详细测试结果 HTML"""
    html = '<div class="section"><h2>详细测试结果</h2>'
    
    for test in results.get('tests', []):
        test_type = test.get('type', 'Unknown')
        test_result = test.get('result', {})
        timestamp = test.get('timestamp', '')
        
        html += f'<div class="test-result">'
        html += f'<h3>{test_type}</h3>'
        html += f'<p><strong>测试时间:</strong> {timestamp}</p>'
        
        # 根据不同测试类型生成不同的结果展示
        if 'SQL' in test_type or 'XSS' in test_type:
            count = test_result.get('count', 0)
            if count > 0:
                html += f'<p class="status-danger"><strong>警告：发现 {count} 个可能的漏洞</strong></p>'
                html += '<div class="vulnerability-list">'
                for vuln in test_result.get('vulnerabilities', [])[:20]:
                    html += '<div class="vulnerability-item medium">'
                    html += f'<p><span class="param">参数:</span> {vuln.get("parameter", "N/A")}</p>'
                    html += f'<p><span class="param">Payload:</span> <span class="payload">{vuln.get("payload", "N/A")}</span></p>'
                    if 'detection_method' in vuln:
                        html += f'<p><span class="param">检测方法:</span> {vuln.get("detection_method")}</p>'
                    html += '</div>'
                if count > 20:
                    html += f'<p style="margin-top: 10px; color: #666;"><em>（仅显示前 20 个结果，共 {count} 个）</em></p>'
                html += '</div>'
            else:
                html += '<p class="status-ok"><strong>未发现漏洞</strong></p>'
        
        elif '敏感文件' in test_type:
            found = test_result.get('found', 0)
            if found > 0:
                html += f'<p class="status-warning"><strong>警告：发现 {found} 个敏感文件</strong></p>'
                html += '<table><tr><th>文件</th><th>状态码</th><th>大小</th></tr>'
                for item in test_result.get('results', []):
                    html += f'<tr><td>{item.get("file", "N/A")}</td><td>{item.get("status_code", "N/A")}</td><td>{item.get("size", "N/A")}</td></tr>'
                html += '</table>'
            else:
                html += '<p class="status-ok"><strong>未发现敏感文件</strong></p>'
        
        elif '浏览器' in test_type:
            nav_result = test_result.get('navigation', {})
            if nav_result.get('success'):
                html += '<p class="status-ok"><strong>浏览器访问成功</strong></p>'
                html += f'<p><strong>页面标题:</strong> {nav_result.get("title", "N/A")}</p>'
                html += f'<p><strong>URL:</strong> {nav_result.get("url", "N/A")}</p>'
                screenshot = test_result.get('screenshot', {})
                if screenshot.get('success'):
                    html += f'<p><strong>截图:</strong> {screenshot.get("path", "N/A")}</p>'
            else:
                html += f'<p class="status-danger"><strong>访问失败:</strong> {nav_result.get("error", "Unknown")}</p>'
        
        html += '</div>'
    
    html += '</div>'
    return html
