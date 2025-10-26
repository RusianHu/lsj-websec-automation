"""
报告生成工具
"""
from typing import Dict, Any, List, Optional
from datetime import datetime
from pathlib import Path
import json
from config.settings import settings
from utils.logger import log


def generate_html_report(
    scan_results: Dict[str, Any],
    output_path: Optional[str] = None
) -> str:
    """
    生成 HTML 格式的安全测试报告
    
    Args:
        scan_results: 扫描结果字典
        output_path: 输出路径
        
    Returns:
        报告文件路径
    """
    if output_path is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = settings.app.reports_dir / f"report_{timestamp}.html"
    
    html_content = f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Web 安全测试报告</title>
    <style>
        body {{
            font-family: 'Microsoft YaHei', Arial, sans-serif;
            line-height: 1.6;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            border-radius: 10px;
            margin-bottom: 30px;
        }}
        .header h1 {{
            margin: 0;
            font-size: 2.5em;
        }}
        .section {{
            background: white;
            padding: 25px;
            margin-bottom: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .section h2 {{
            color: #667eea;
            border-bottom: 2px solid #667eea;
            padding-bottom: 10px;
            margin-top: 0;
        }}
        .vulnerability {{
            background: #fff3cd;
            border-left: 4px solid #ffc107;
            padding: 15px;
            margin: 10px 0;
            border-radius: 4px;
        }}
        .vulnerability.high {{
            background: #f8d7da;
            border-left-color: #dc3545;
        }}
        .vulnerability.medium {{
            background: #fff3cd;
            border-left-color: #ffc107;
        }}
        .vulnerability.low {{
            background: #d1ecf1;
            border-left-color: #17a2b8;
        }}
        .info-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 15px;
            margin: 20px 0;
        }}
        .info-item {{
            background: #f8f9fa;
            padding: 15px;
            border-radius: 5px;
        }}
        .info-item strong {{
            color: #667eea;
            display: block;
            margin-bottom: 5px;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 15px 0;
        }}
        th, td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }}
        th {{
            background-color: #667eea;
            color: white;
        }}
        tr:hover {{
            background-color: #f5f5f5;
        }}
        .footer {{
            text-align: center;
            color: #666;
            margin-top: 30px;
            padding: 20px;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>Web 安全测试报告</h1>
        <p>生成时间: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
    </div>
    
    <div class="section">
        <h2>执行摘要</h2>
        <div class="info-grid">
            <div class="info-item">
                <strong>目标 URL</strong>
                {scan_results.get('target_url', 'N/A')}
            </div>
            <div class="info-item">
                <strong>扫描时间</strong>
                {scan_results.get('scan_time', 'N/A')}
            </div>
            <div class="info-item">
                <strong>发现漏洞</strong>
                {scan_results.get('total_vulnerabilities', 0)} 个
            </div>
            <div class="info-item">
                <strong>风险等级</strong>
                {scan_results.get('risk_level', 'N/A')}
            </div>
        </div>
    </div>
    
    <div class="section">
        <h2>扫描详情</h2>
        {_generate_scan_text_html(scan_results.get('scan_text', ''))}
    </div>

    <div class="section">
        <h2>扫描结果</h2>
        {_generate_vulnerabilities_html(scan_results.get('vulnerabilities', []))}
    </div>

    <div class="section">
        <h2>目录扫描结果</h2>
        {_generate_directory_scan_html(scan_results.get('directory_scan', []))}
    </div>

    <div class="section">
        <h2>修复建议</h2>
        {_generate_recommendations_html(scan_results.get('recommendations', []))}
    </div>
    
    <div class="footer">
        <p>本报告由 LSJ WebSec Automation 自动生成</p>
        <p>Copyright {datetime.now().year} - 仅供授权安全测试使用</p>
    </div>
</body>
</html>
"""
    
    # 写入文件
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    log.info(f"HTML 报告已生成: {output_path}")
    return str(output_path)


def _generate_scan_text_html(scan_text: str) -> str:
    """生成扫描详情 HTML"""
    if not scan_text:
        return "<p>无扫描详情</p>"

    # 将文本转换为 HTML,保留换行和格式
    import html
    escaped_text = html.escape(scan_text)
    formatted_text = escaped_text.replace('\n', '<br>')

    return f'<div style="white-space: pre-wrap; font-family: monospace; background: #f5f5f5; padding: 15px; border-radius: 5px; max-height: 600px; overflow-y: auto;">{formatted_text}</div>'


def _generate_vulnerabilities_html(vulnerabilities: List[Dict[str, Any]]) -> str:
    """生成漏洞列表 HTML"""
    if not vulnerabilities:
        return "<p>未发现明显漏洞</p>"

    html = ""
    for vuln in vulnerabilities:
        severity = vuln.get('severity', 'medium').lower()
        html += f"""
        <div class="vulnerability {severity}">
            <h3>{vuln.get('type', 'Unknown')} - {vuln.get('name', 'N/A')}</h3>
            <p><strong>严重程度:</strong> {vuln.get('severity', 'N/A')}</p>
            <p><strong>描述:</strong> {vuln.get('description', 'N/A')}</p>
            <p><strong>位置:</strong> {vuln.get('location', 'N/A')}</p>
            <p><strong>证据:</strong> <code>{vuln.get('evidence', 'N/A')}</code></p>
        </div>
        """
    return html


def _generate_directory_scan_html(results: List[Dict[str, Any]]) -> str:
    """生成目录扫描结果 HTML"""
    if not results:
        return "<p>无目录扫描结果</p>"
    
    html = "<table><tr><th>URL</th><th>状态码</th><th>大小</th><th>类型</th></tr>"
    for item in results[:50]:  # 只显示前50个
        html += f"""
        <tr>
            <td>{item.get('url', 'N/A')}</td>
            <td>{item.get('status_code', 'N/A')}</td>
            <td>{item.get('content_length', 'N/A')} bytes</td>
            <td>{item.get('content_type', 'N/A')}</td>
        </tr>
        """
    html += "</table>"
    return html


def _generate_recommendations_html(recommendations: List[str]) -> str:
    """生成修复建议 HTML"""
    if not recommendations:
        return "<p>暂无修复建议</p>"
    
    html = "<ul>"
    for rec in recommendations:
        html += f"<li>{rec}</li>"
    html += "</ul>"
    return html


def generate_json_report(
    scan_results: Dict[str, Any],
    output_path: Optional[str] = None
) -> str:
    """
    生成 JSON 格式的报告
    
    Args:
        scan_results: 扫描结果
        output_path: 输出路径
        
    Returns:
        报告文件路径
    """
    if output_path is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = settings.app.reports_dir / f"report_{timestamp}.json"
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(scan_results, f, ensure_ascii=False, indent=2)
    
    log.info(f"JSON 报告已生成: {output_path}")
    return str(output_path)
