"""
Web 扫描工具
基于 ffuf 知识库的扫描功能
"""
from typing import Dict, Any, List, Optional
import httpx
import asyncio
from pathlib import Path
from urllib.parse import urljoin, urlparse
from utils.logger import log
from utils.url_helper import normalize_url


async def scan_directory(
    base_url: str,
    wordlist: List[str],
    extensions: Optional[List[str]] = None,
    status_codes: Optional[List[int]] = None,
    timeout: int = 10
) -> Dict[str, Any]:
    """
    目录扫描

    Args:
        base_url: 基础 URL
        wordlist: 字典列表
        extensions: 文件扩展名列表
        status_codes: 要匹配的状态码列表
        timeout: 请求超时时间

    Returns:
        扫描结果
    """
    # 规范化 URL
    base_url = normalize_url(base_url)

    if status_codes is None:
        status_codes = [200, 201, 204, 301, 302, 307, 401, 403]

    if extensions is None:
        extensions = ["", ".php", ".html", ".asp", ".aspx", ".jsp"]

    results = []
    total = len(wordlist) * len(extensions)
    scanned = 0

    log.info(f"开始目录扫描: {base_url}")
    log.info(f"字典大小: {len(wordlist)}, 扩展名: {extensions}")

    async with httpx.AsyncClient(timeout=timeout, follow_redirects=False) as client:
        for word in wordlist:
            for ext in extensions:
                path = f"{word}{ext}"
                url = urljoin(base_url, path)

                try:
                    response = await client.get(url)
                    scanned += 1

                    if response.status_code in status_codes:
                        result = {
                            "url": url,
                            "status_code": response.status_code,
                            "content_length": len(response.content),
                            "content_type": response.headers.get("content-type", ""),
                        }
                        results.append(result)
                        log.info(f"发现: {url} [{response.status_code}] {len(response.content)} bytes")

                    # 进度显示
                    if scanned % 100 == 0:
                        log.info(f"扫描进度: {scanned}/{total}")

                except Exception as e:
                    log.debug(f"请求失败: {url} - {str(e)}")
                    continue

                # 避免请求过快
                await asyncio.sleep(0.01)

    log.info(f"目录扫描完成，发现 {len(results)} 个结果")

    return {
        "success": True,
        "base_url": base_url,
        "total_scanned": scanned,
        "found": len(results),
        "results": results
    }


async def scan_subdomains(
    domain: str,
    wordlist: List[str],
    timeout: int = 5
) -> Dict[str, Any]:
    """
    子域名扫描

    Args:
        domain: 主域名
        wordlist: 子域名字典
        timeout: 请求超时时间

    Returns:
        扫描结果
    """
    results = []
    total = len(wordlist)
    scanned = 0

    log.info(f"开始子域名扫描: {domain}")

    async with httpx.AsyncClient(timeout=timeout, follow_redirects=False) as client:
        for subdomain in wordlist:
            url = f"http://{subdomain}.{domain}"

            try:
                response = await client.get(url)
                scanned += 1

                result = {
                    "subdomain": f"{subdomain}.{domain}",
                    "url": url,
                    "status_code": response.status_code,
                    "ip": response.headers.get("x-forwarded-for", ""),
                }
                results.append(result)
                log.info(f"发现子域名: {subdomain}.{domain} [{response.status_code}]")

                if scanned % 50 == 0:
                    log.info(f"扫描进度: {scanned}/{total}")

            except Exception as e:
                log.debug(f"请求失败: {url} - {str(e)}")
                continue

            await asyncio.sleep(0.01)

    log.info(f"子域名扫描完成，发现 {len(results)} 个子域名")

    return {
        "success": True,
        "domain": domain,
        "total_scanned": scanned,
        "found": len(results),
        "results": results
    }


async def fuzz_parameters(
    url: str,
    param_name: str,
    wordlist: List[str],
    method: str = "GET",
    timeout: int = 10
) -> Dict[str, Any]:
    """
    参数模糊测试

    Args:
        url: 目标 URL
        param_name: 参数名称
        wordlist: 测试值列表
        method: HTTP 方法
        timeout: 请求超时时间

    Returns:
        测试结果
    """
    # 规范化 URL
    url = normalize_url(url)

    results = []
    total = len(wordlist)
    tested = 0

    log.info(f"开始参数模糊测试: {url}?{param_name}=FUZZ")

    async with httpx.AsyncClient(timeout=timeout, follow_redirects=False) as client:
        for value in wordlist:
            try:
                if method.upper() == "GET":
                    response = await client.get(url, params={param_name: value})
                elif method.upper() == "POST":
                    response = await client.post(url, data={param_name: value})
                else:
                    continue

                tested += 1

                result = {
                    "value": value,
                    "status_code": response.status_code,
                    "content_length": len(response.content),
                    "response_time": response.elapsed.total_seconds(),
                }
                results.append(result)

                if tested % 50 == 0:
                    log.info(f"测试进度: {tested}/{total}")

            except Exception as e:
                log.debug(f"请求失败: {param_name}={value} - {str(e)}")
                continue

            await asyncio.sleep(0.01)

    log.info(f"参数模糊测试完成，测试了 {tested} 个值")

    return {
        "success": True,
        "url": url,
        "parameter": param_name,
        "total_tested": tested,
        "results": results
    }


async def check_common_files(base_url: str) -> Dict[str, Any]:
    """
    检查常见敏感文件

    Args:
        base_url: 基础 URL

    Returns:
        检查结果
    """
    # 规范化 URL
    base_url = normalize_url(base_url)

    common_files = [
        "robots.txt",
        "sitemap.xml",
        ".git/config",
        ".env",
        "config.php",
        "web.config",
        "phpinfo.php",
        "info.php",
        "test.php",
        "admin.php",
        "login.php",
        "backup.sql",
        "database.sql",
        ".htaccess",
        "composer.json",
        "package.json",
    ]

    results = []

    log.info(f"检查常见敏感文件: {base_url}")

    async with httpx.AsyncClient(timeout=10, follow_redirects=False) as client:
        for file in common_files:
            url = urljoin(base_url, file)

            try:
                response = await client.get(url)

                if response.status_code in [200, 201, 204]:
                    result = {
                        "file": file,
                        "url": url,
                        "status_code": response.status_code,
                        "content_length": len(response.content),
                        "found": True
                    }
                    results.append(result)
                    log.warning(f"发现敏感文件: {url} [{response.status_code}]")

            except Exception as e:
                log.debug(f"检查失败: {url} - {str(e)}")
                continue

    log.info(f"敏感文件检查完成，发现 {len(results)} 个文件")

    return {
        "success": True,
        "base_url": base_url,
        "found": len(results),
        "results": results
    }



# ========= 便捷包装 & 高级探测工具 =========

async def quick_directory_scan(base_url: str, profile: str = "small", timeout: int = 10) -> Dict[str, Any]:
    """
    快速目录扫描（内置小词表/扩展名），便于 LLM 直接调用
    Args:
        base_url: 目标基础 URL
        profile: 词表档位（tiny/small）
        timeout: 超时
    """
    profiles = {
        "tiny": ( ["admin", "login", "config"], ["", ".php", ".html"] ),
        "small": (["admin", "login", "config", "backup", "test", ".git", ".env"], ["", ".php", ".html", ".asp", ".aspx"]),
    }
    wordlist, extensions = profiles.get(profile, profiles["small"])
    return await scan_directory(base_url, wordlist, extensions=extensions, timeout=timeout)


async def quick_subdomain_scan(domain: str, profile: str = "tiny", timeout: int = 5) -> Dict[str, Any]:
    """
    快速子域名扫描（内置小词表）
    Args:
        domain: 主域名（如 example.com）
        profile: tiny/small
    """
    profiles = {
        "tiny":  ["www", "test", "dev", "admin", "api"],
        "small": ["www", "test", "dev", "admin", "api", "stg", "stage", "beta", "cdn"],
    }
    wordlist = profiles.get(profile, profiles["tiny"])
    return await scan_subdomains(domain, wordlist, timeout=timeout)


async def quick_param_fuzz(
    url: str,
    param_name: str,
    profile: str = "common",
    method: str = "GET",
    timeout: int = 10,
) -> Dict[str, Any]:
    """
    快速参数模糊测试（内置小 payload 集）
    Args:
        url: 目标 URL
        param_name: 参数名
        profile: 预设 payload 集（common/tiny）
        method: GET/POST
    """
    payload_profiles = {
        "common": [
            "", "1", "admin", "'", '"',
            "<script>alert('XSS')</script>",
            "../../etc/passwd",
            "1 OR 1=1",
            "%27%22%3E",
            "<img src=x onerror=alert(1)>",
        ],
        "tiny": ["", "'", "<script>alert(1)</script>"],
    }
    values = payload_profiles.get(profile, payload_profiles["common"])
    return await fuzz_parameters(url, param_name, values, method=method, timeout=timeout)


async def discover_api_endpoints(base_url: str, timeout: int = 10) -> Dict[str, Any]:
    """
    轻量 API 端点发现（HEAD 优先，必要时 GET）
    """
    base_url = normalize_url(base_url)
    candidates = [
        "/api/", "/api/v1/", "/api/status", "/api/health",
        "/graphql", "/.well-known/openid-configuration",
    ]
    results: List[Dict[str, Any]] = []
    async with httpx.AsyncClient(timeout=timeout, follow_redirects=False) as client:
        for path in candidates:
            url = urljoin(base_url, path)
            try:
                resp = await client.head(url)
                status = resp.status_code
                ctype = resp.headers.get("content-type", "")
                clen = int(resp.headers.get("content-length", "0") or 0)
                if status >= 400 or status == 405:
                    resp = await client.get(url)
                    status = resp.status_code
                    ctype = resp.headers.get("content-type", "")
                    clen = len(resp.content)
                results.append({
                    "url": url,
                    "status_code": status,
                    "content_type": ctype,
                    "content_length": clen,
                })
                if status in (200, 201, 204, 301, 302, 307, 308):
                    log.info(f"发现可能的 API 端点: {url} [{status}]")
            except Exception as e:
                log.debug(f"探测失败: {url} - {e}")
            await asyncio.sleep(0.01)
    return {
        "success": True,
        "base_url": base_url,
        "found": sum(1 for r in results if r.get("status_code", 0) < 400),
        "results": results,
    }


async def fuzzing_headers(base_url: str, path: str = "/", timeout: int = 10) -> Dict[str, Any]:
    """
    HTTP 头部模糊测试（小而安全的头集合），用于侦测行为变化/绕过迹象
    """
    base_url = normalize_url(base_url)
    url = urljoin(base_url, path)
    tests = [
        {"X-Forwarded-For": "127.0.0.1"},
        {"X-Original-URL": "/admin"},
        {"X-Rewrite-URL": "/admin"},
        {"X-HTTP-Method-Override": "PUT"},
        {"X-HTTP-Method-Override": "DELETE"},
        {"X-Host": "localhost"},
        {"X-Forwarded-Host": "evil.com"},
    ]
    results: List[Dict[str, Any]] = []
    async with httpx.AsyncClient(timeout=timeout, follow_redirects=False) as client:
        try:
            base_resp = await client.get(url)
            base_status = base_resp.status_code
            base_len = len(base_resp.content)
            base_loc = base_resp.headers.get("location", "")
        except Exception as e:
            return {"success": False, "error": str(e)}
        for hdr in tests:
            try:
                resp = await client.get(url, headers=hdr)
                change = {
                    "headers": hdr,
                    "status_code": resp.status_code,
                    "location": resp.headers.get("location", ""),
                    "content_length": len(resp.content),
                    "diff_status": resp.status_code != base_status,
                    "diff_length": abs(len(resp.content) - base_len) > 200,
                }
                results.append(change)
                if change["diff_status"] or change["location"] != base_loc:
                    log.warning(f"头部可能影响行为: {hdr} -> {resp.status_code}")
            except Exception as e:
                log.debug(f"头部测试失败 {hdr}: {e}")
            await asyncio.sleep(0.01)
    return {
        "success": True,
        "url": url,
        "tested": len(results),
        "results": results,
    }
