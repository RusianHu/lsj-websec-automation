"""
高级扫描策略模块
基于 ffuf 工具的专业渗透测试策略
"""
from typing import Dict, Any, List, Optional, Tuple
import httpx
import asyncio
import re
from urllib.parse import urljoin, urlparse, parse_qs, urlencode
from utils.logger import log
from utils.url_helper import normalize_url


async def fuzzing_directory_advanced(
    base_url: str,
    wordlist: List[str],
    extensions: Optional[List[str]] = None,
    recursion_depth: int = 0,
    auto_calibrate: bool = True,
    rate_limit: int = 40,
    timeout: int = 10
) -> Dict[str, Any]:
    """
    高级目录模糊测试 (基于 ffuf 策略)
    
    Args:
        base_url: 基础 URL
        wordlist: 字典列表
        extensions: 文件扩展名列表
        recursion_depth: 递归深度 (0=不递归)
        auto_calibrate: 自动校准，过滤重复响应
        rate_limit: 每秒请求数限制
        timeout: 请求超时时间
    
    Returns:
        扫描结果
    """
    base_url = normalize_url(base_url)
    
    if extensions is None:
        extensions = ["", ".php", ".html", ".asp", ".aspx", ".jsp", ".txt", ".bak", ".old"]
    
    results = []
    calibration_data = {}
    
    log.info(f"开始高级目录模糊测试: {base_url}")
    log.info(f"字典大小: {len(wordlist)}, 扩展名: {extensions}, 递归深度: {recursion_depth}")
    
    # 自动校准：检测默认响应模式
    if auto_calibrate:
        log.info("执行自动校准...")
        calibration_data = await _auto_calibrate(base_url, timeout)
        log.info(f"校准完成: 默认状态码={calibration_data.get('status_code')}, "
                f"默认大小={calibration_data.get('content_length')}")
    
    # 限速器
    semaphore = asyncio.Semaphore(rate_limit)
    delay = 1.0 / rate_limit if rate_limit > 0 else 0
    
    async def scan_path(path: str, depth: int = 0):
        """扫描单个路径"""
        async with semaphore:
            url = urljoin(base_url, path)
            
            try:
                async with httpx.AsyncClient(timeout=timeout, follow_redirects=False) as client:
                    response = await client.get(url)
                    
                    # 应用自动校准过滤
                    if auto_calibrate and _should_filter(response, calibration_data):
                        return None
                    
                    # 记录有效结果
                    if response.status_code in [200, 201, 204, 301, 302, 307, 401, 403, 405, 500]:
                        result = {
                            "url": url,
                            "path": path,
                            "status_code": response.status_code,
                            "content_length": len(response.content),
                            "content_type": response.headers.get("content-type", ""),
                            "depth": depth,
                            "interesting": _is_interesting(response)
                        }
                        
                        log.info(f"发现: {url} [{response.status_code}] {len(response.content)} bytes")
                        
                        # 递归扫描
                        if recursion_depth > depth and response.status_code in [200, 301, 302]:
                            log.info(f"递归扫描: {url} (深度 {depth + 1})")
                            # 这里可以添加递归逻辑
                        
                        return result
                        
            except Exception as e:
                log.debug(f"请求失败: {url} - {str(e)}")
            
            await asyncio.sleep(delay)
            return None
    
    # 并发扫描
    tasks = []
    for word in wordlist:
        for ext in extensions:
            path = f"{word}{ext}"
            tasks.append(scan_path(path))
    
    # 执行所有任务
    scan_results = await asyncio.gather(*tasks)
    results = [r for r in scan_results if r is not None]
    
    log.info(f"目录模糊测试完成，发现 {len(results)} 个有效路径")
    
    return {
        "success": True,
        "base_url": base_url,
        "total_scanned": len(wordlist) * len(extensions),
        "found": len(results),
        "results": results,
        "calibration": calibration_data if auto_calibrate else None
    }


async def fuzzing_parameters(
    url: str,
    param_wordlist: List[str],
    value_wordlist: Optional[List[str]] = None,
    method: str = "GET",
    mode: str = "sniper",
    auto_calibrate: bool = True,
    timeout: int = 10
) -> Dict[str, Any]:
    """
    参数模糊测试 (基于 ffuf 参数发现策略)
    
    Args:
        url: 目标 URL
        param_wordlist: 参数名字典
        value_wordlist: 参数值字典 (可选)
        method: HTTP 方法 (GET/POST)
        mode: 模式 (sniper/clusterbomb/pitchfork)
        auto_calibrate: 自动校准
        timeout: 超时时间
    
    Returns:
        测试结果
    """
    url = normalize_url(url)
    
    if value_wordlist is None:
        value_wordlist = ["test", "1", "true", "admin", ""]
    
    results = []
    calibration_data = {}
    
    log.info(f"开始参数模糊测试: {url}")
    log.info(f"参数字典: {len(param_wordlist)}, 值字典: {len(value_wordlist)}, 模式: {mode}")
    
    # 自动校准
    if auto_calibrate:
        calibration_data = await _auto_calibrate(url, timeout)
    
    async with httpx.AsyncClient(timeout=timeout, follow_redirects=False) as client:
        if mode == "sniper":
            # Sniper 模式：一次测试一个参数
            for param in param_wordlist:
                for value in value_wordlist:
                    test_url = f"{url}?{param}={value}"
                    
                    try:
                        if method == "GET":
                            response = await client.get(test_url)
                        else:
                            response = await client.post(url, data={param: value})
                        
                        if auto_calibrate and _should_filter(response, calibration_data):
                            continue
                        
                        if response.status_code != 404:
                            result = {
                                "parameter": param,
                                "value": value,
                                "url": test_url,
                                "status_code": response.status_code,
                                "content_length": len(response.content),
                                "interesting": _is_interesting(response)
                            }
                            results.append(result)
                            log.info(f"发现参数: {param}={value} [{response.status_code}]")
                    
                    except Exception as e:
                        log.debug(f"请求失败: {test_url} - {str(e)}")
                    
                    await asyncio.sleep(0.01)
        
        elif mode == "clusterbomb":
            # Clusterbomb 模式：测试所有组合
            for param in param_wordlist:
                for value in value_wordlist:
                    params = {param: value}
                    
                    try:
                        if method == "GET":
                            response = await client.get(url, params=params)
                        else:
                            response = await client.post(url, data=params)
                        
                        if auto_calibrate and _should_filter(response, calibration_data):
                            continue
                        
                        if response.status_code != 404:
                            result = {
                                "parameter": param,
                                "value": value,
                                "status_code": response.status_code,
                                "content_length": len(response.content)
                            }
                            results.append(result)
                            log.info(f"发现参数组合: {param}={value}")
                    
                    except Exception as e:
                        log.debug(f"请求失败 - {str(e)}")
                    
                    await asyncio.sleep(0.01)
    
    log.info(f"参数模糊测试完成，发现 {len(results)} 个有效参数")
    
    return {
        "success": True,
        "url": url,
        "mode": mode,
        "found": len(results),
        "results": results
    }


async def fuzzing_headers(
    url: str,
    header_wordlist: List[str],
    value_wordlist: Optional[List[str]] = None,
    auto_calibrate: bool = True,
    timeout: int = 10
) -> Dict[str, Any]:
    """
    HTTP 头模糊测试
    
    Args:
        url: 目标 URL
        header_wordlist: 头部名称字典
        value_wordlist: 头部值字典
        auto_calibrate: 自动校准
        timeout: 超时时间
    
    Returns:
        测试结果
    """
    url = normalize_url(url)
    
    if value_wordlist is None:
        value_wordlist = ["127.0.0.1", "localhost", "admin", "true", "1"]
    
    results = []
    calibration_data = {}
    
    log.info(f"开始 HTTP 头模糊测试: {url}")
    
    if auto_calibrate:
        calibration_data = await _auto_calibrate(url, timeout)
    
    async with httpx.AsyncClient(timeout=timeout, follow_redirects=False) as client:
        for header in header_wordlist:
            for value in value_wordlist:
                headers = {header: value}
                
                try:
                    response = await client.get(url, headers=headers)
                    
                    if auto_calibrate and _should_filter(response, calibration_data):
                        continue
                    
                    if response.status_code != 404:
                        result = {
                            "header": header,
                            "value": value,
                            "status_code": response.status_code,
                            "content_length": len(response.content),
                            "interesting": _is_interesting(response)
                        }
                        results.append(result)
                        log.info(f"发现敏感头: {header}: {value} [{response.status_code}]")
                
                except Exception as e:
                    log.debug(f"请求失败 - {str(e)}")
                
                await asyncio.sleep(0.01)
    
    log.info(f"HTTP 头模糊测试完成，发现 {len(results)} 个敏感头")
    
    return {
        "success": True,
        "url": url,
        "found": len(results),
        "results": results
    }


# 辅助函数

async def _auto_calibrate(url: str, timeout: int) -> Dict[str, Any]:
    """
    自动校准：检测默认响应模式
    """
    calibration_urls = [
        urljoin(url, "nonexistent_" + str(i)) for i in range(3)
    ]
    
    responses = []
    
    async with httpx.AsyncClient(timeout=timeout, follow_redirects=False) as client:
        for cal_url in calibration_urls:
            try:
                response = await client.get(cal_url)
                responses.append({
                    "status_code": response.status_code,
                    "content_length": len(response.content),
                    "content": response.text[:500]
                })
            except:
                pass
    
    if not responses:
        return {}
    
    # 找出共同特征
    common_status = responses[0]["status_code"]
    common_length = responses[0]["content_length"]
    
    return {
        "status_code": common_status,
        "content_length": common_length,
        "pattern": responses[0]["content"][:100]
    }


def _should_filter(response: httpx.Response, calibration_data: Dict[str, Any]) -> bool:
    """
    判断是否应该过滤此响应
    """
    if not calibration_data:
        return False
    
    # 过滤相同状态码和大小的响应
    if (response.status_code == calibration_data.get("status_code") and
        abs(len(response.content) - calibration_data.get("content_length", 0)) < 50):
        return True
    
    return False


def _is_interesting(response: httpx.Response) -> bool:
    """
    判断响应是否有趣/值得关注
    """
    interesting_patterns = [
        r"admin", r"login", r"password", r"token", r"api",
        r"config", r"backup", r"\.git", r"\.env",
        r"error", r"exception", r"stack trace",
        r"sql", r"database", r"query"
    ]
    
    content = response.text.lower()
    
    for pattern in interesting_patterns:
        if re.search(pattern, content, re.IGNORECASE):
            return True
    
    # 检查响应头
    interesting_headers = ["x-powered-by", "server", "x-aspnet-version"]
    for header in interesting_headers:
        if header in response.headers:
            return True
    
    return False

