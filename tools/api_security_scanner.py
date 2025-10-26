"""
API 安全测试模块
专门用于 REST API、GraphQL、WebSocket 等 API 端点的安全测试
"""
from typing import Dict, Any, List, Optional
import httpx
import asyncio
import json
import re
from urllib.parse import urljoin, urlparse
from utils.logger import log
from utils.url_helper import normalize_url


async def discover_api_endpoints(
    base_url: str,
    api_wordlist: Optional[List[str]] = None,
    versions: Optional[List[str]] = None,
    auto_calibrate: bool = True,
    timeout: int = 10
) -> Dict[str, Any]:
    """
    API 端点发现 (基于 ffuf API 测试策略)
    
    Args:
        base_url: 基础 URL
        api_wordlist: API 端点字典
        versions: API 版本列表 (如 v1, v2, v3)
        auto_calibrate: 自动校准
        timeout: 超时时间
    
    Returns:
        发现的 API 端点
    """
    base_url = normalize_url(base_url)
    
    if api_wordlist is None:
        api_wordlist = [
            "users", "user", "admin", "login", "auth", "token",
            "api", "v1", "v2", "v3", "graphql", "swagger",
            "docs", "openapi", "health", "status", "config",
            "settings", "profile", "account", "dashboard",
            "products", "orders", "payments", "upload", "download"
        ]
    
    if versions is None:
        versions = ["", "v1", "v2", "v3", "api/v1", "api/v2"]
    
    results = []
    
    log.info(f"开始 API 端点发现: {base_url}")
    log.info(f"端点字典: {len(api_wordlist)}, 版本: {versions}")
    
    async with httpx.AsyncClient(timeout=timeout, follow_redirects=False) as client:
        for version in versions:
            for endpoint in api_wordlist:
                # 构建 API 路径
                if version:
                    path = f"{version}/{endpoint}"
                else:
                    path = endpoint
                
                url = urljoin(base_url, path)
                
                try:
                    response = await client.get(url)
                    
                    # 检测 API 响应
                    if _is_api_response(response):
                        result = {
                            "url": url,
                            "endpoint": endpoint,
                            "version": version,
                            "status_code": response.status_code,
                            "content_type": response.headers.get("content-type", ""),
                            "content_length": len(response.content),
                            "api_type": _detect_api_type(response),
                            "methods": await _detect_http_methods(client, url)
                        }
                        results.append(result)
                        log.info(f"发现 API 端点: {url} [{response.status_code}] {result['api_type']}")
                
                except Exception as e:
                    log.debug(f"请求失败: {url} - {str(e)}")
                
                await asyncio.sleep(0.01)
    
    log.info(f"API 端点发现完成，找到 {len(results)} 个端点")
    
    return {
        "success": True,
        "base_url": base_url,
        "found": len(results),
        "results": results
    }


async def test_api_authentication(
    api_url: str,
    auth_headers: Optional[Dict[str, str]] = None,
    test_bypass: bool = True,
    timeout: int = 10
) -> Dict[str, Any]:
    """
    API 认证测试
    
    Args:
        api_url: API URL
        auth_headers: 认证头 (如 Authorization: Bearer token)
        test_bypass: 是否测试认证绕过
        timeout: 超时时间
    
    Returns:
        测试结果
    """
    api_url = normalize_url(api_url)
    
    results = {
        "url": api_url,
        "tests": []
    }
    
    log.info(f"开始 API 认证测试: {api_url}")
    
    async with httpx.AsyncClient(timeout=timeout, follow_redirects=False) as client:
        # 1. 无认证访问测试
        try:
            response = await client.get(api_url)
            results["tests"].append({
                "test": "无认证访问",
                "status_code": response.status_code,
                "vulnerable": response.status_code == 200,
                "description": "API 允许无认证访问" if response.status_code == 200 else "需要认证"
            })
        except Exception as e:
            log.error(f"无认证测试失败: {str(e)}")
        
        # 2. 有效认证测试
        if auth_headers:
            try:
                response = await client.get(api_url, headers=auth_headers)
                results["tests"].append({
                    "test": "有效认证访问",
                    "status_code": response.status_code,
                    "success": response.status_code == 200
                })
            except Exception as e:
                log.error(f"认证测试失败: {str(e)}")
        
        # 3. 认证绕过测试
        if test_bypass:
            bypass_headers = [
                {"X-Original-URL": api_url},
                {"X-Rewrite-URL": api_url},
                {"X-Forwarded-For": "127.0.0.1"},
                {"X-Forwarded-Host": "localhost"},
                {"X-Custom-IP-Authorization": "127.0.0.1"},
                {"X-Originating-IP": "127.0.0.1"},
                {"X-Remote-IP": "127.0.0.1"},
                {"X-Client-IP": "127.0.0.1"},
            ]
            
            for bypass_header in bypass_headers:
                try:
                    response = await client.get(api_url, headers=bypass_header)
                    if response.status_code == 200:
                        results["tests"].append({
                            "test": "认证绕过",
                            "method": f"使用头: {list(bypass_header.keys())[0]}",
                            "status_code": response.status_code,
                            "vulnerable": True,
                            "severity": "高"
                        })
                        log.warning(f"发现认证绕过: {list(bypass_header.keys())[0]}")
                except Exception as e:
                    log.debug(f"绕过测试失败: {str(e)}")
                
                await asyncio.sleep(0.01)
    
    log.info(f"API 认证测试完成")
    
    return {
        "success": True,
        "results": results
    }


async def test_api_rate_limiting(
    api_url: str,
    requests_count: int = 100,
    auth_headers: Optional[Dict[str, str]] = None,
    timeout: int = 10
) -> Dict[str, Any]:
    """
    API 速率限制测试
    
    Args:
        api_url: API URL
        requests_count: 请求次数
        auth_headers: 认证头
        timeout: 超时时间
    
    Returns:
        测试结果
    """
    api_url = normalize_url(api_url)
    
    log.info(f"开始 API 速率限制测试: {api_url}")
    log.info(f"将发送 {requests_count} 个请求")
    
    responses = []
    rate_limited = False
    
    async with httpx.AsyncClient(timeout=timeout, follow_redirects=False) as client:
        for i in range(requests_count):
            try:
                headers = auth_headers if auth_headers else {}
                response = await client.get(api_url, headers=headers)
                
                responses.append({
                    "request_num": i + 1,
                    "status_code": response.status_code,
                    "headers": dict(response.headers)
                })
                
                # 检测速率限制
                if response.status_code == 429:
                    rate_limited = True
                    log.info(f"检测到速率限制: 请求 #{i + 1}")
                    break
                
                # 检查速率限制头
                if "X-RateLimit-Remaining" in response.headers:
                    remaining = response.headers.get("X-RateLimit-Remaining")
                    log.info(f"剩余请求数: {remaining}")
                
            except Exception as e:
                log.debug(f"请求失败: {str(e)}")
            
            # 快速连续请求
            await asyncio.sleep(0.01)
    
    log.info(f"速率限制测试完成，发送了 {len(responses)} 个请求")
    
    return {
        "success": True,
        "url": api_url,
        "total_requests": len(responses),
        "rate_limited": rate_limited,
        "vulnerable": not rate_limited,
        "severity": "中" if not rate_limited else "无",
        "description": "API 未实施速率限制" if not rate_limited else "API 已实施速率限制",
        "responses": responses[:10]  # 只返回前 10 个响应
    }


async def test_api_methods(
    api_url: str,
    auth_headers: Optional[Dict[str, str]] = None,
    timeout: int = 10
) -> Dict[str, Any]:
    """
    测试 API 支持的 HTTP 方法
    
    Args:
        api_url: API URL
        auth_headers: 认证头
        timeout: 超时时间
    
    Returns:
        测试结果
    """
    api_url = normalize_url(api_url)
    
    methods = ["GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS", "TRACE"]
    results = []
    
    log.info(f"开始 HTTP 方法测试: {api_url}")
    
    async with httpx.AsyncClient(timeout=timeout, follow_redirects=False) as client:
        for method in methods:
            try:
                headers = auth_headers if auth_headers else {}
                response = await client.request(method, api_url, headers=headers)
                
                result = {
                    "method": method,
                    "status_code": response.status_code,
                    "allowed": response.status_code not in [404, 405, 501],
                    "content_length": len(response.content)
                }
                results.append(result)
                
                if result["allowed"]:
                    log.info(f"方法 {method} 被允许 [{response.status_code}]")
                
                # 检查 Allow 头
                if method == "OPTIONS" and "Allow" in response.headers:
                    allowed_methods = response.headers.get("Allow")
                    log.info(f"OPTIONS 响应 - 允许的方法: {allowed_methods}")
            
            except Exception as e:
                log.debug(f"方法 {method} 测试失败: {str(e)}")
            
            await asyncio.sleep(0.01)
    
    log.info(f"HTTP 方法测试完成")
    
    return {
        "success": True,
        "url": api_url,
        "results": results,
        "allowed_methods": [r["method"] for r in results if r["allowed"]]
    }


async def test_graphql_introspection(
    graphql_url: str,
    timeout: int = 10
) -> Dict[str, Any]:
    """
    GraphQL 内省查询测试
    
    Args:
        graphql_url: GraphQL 端点 URL
        timeout: 超时时间
    
    Returns:
        测试结果
    """
    graphql_url = normalize_url(graphql_url)
    
    # GraphQL 内省查询
    introspection_query = {
        "query": """
        {
            __schema {
                types {
                    name
                    fields {
                        name
                        type {
                            name
                        }
                    }
                }
            }
        }
        """
    }
    
    log.info(f"开始 GraphQL 内省测试: {graphql_url}")
    
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(
                graphql_url,
                json=introspection_query,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                data = response.json()
                
                if "data" in data and "__schema" in data["data"]:
                    log.warning("GraphQL 内省查询已启用 - 可能泄露 API 结构")
                    
                    return {
                        "success": True,
                        "url": graphql_url,
                        "introspection_enabled": True,
                        "vulnerable": True,
                        "severity": "中",
                        "schema": data["data"]["__schema"],
                        "description": "GraphQL 内省查询已启用，攻击者可以获取完整的 API 结构"
                    }
    
    except Exception as e:
        log.error(f"GraphQL 内省测试失败: {str(e)}")
    
    return {
        "success": True,
        "url": graphql_url,
        "introspection_enabled": False,
        "vulnerable": False
    }


# 辅助函数

def _is_api_response(response: httpx.Response) -> bool:
    """判断是否为 API 响应"""
    content_type = response.headers.get("content-type", "").lower()
    
    # 检查内容类型
    if any(t in content_type for t in ["json", "xml", "api"]):
        return True
    
    # 检查状态码
    if response.status_code in [200, 201, 204, 401, 403]:
        try:
            # 尝试解析 JSON
            response.json()
            return True
        except:
            pass
    
    return False


def _detect_api_type(response: httpx.Response) -> str:
    """检测 API 类型"""
    content_type = response.headers.get("content-type", "").lower()
    
    if "json" in content_type:
        return "REST/JSON"
    elif "xml" in content_type:
        return "REST/XML"
    elif "graphql" in response.text.lower():
        return "GraphQL"
    else:
        return "Unknown"


async def _detect_http_methods(client: httpx.AsyncClient, url: str) -> List[str]:
    """检测支持的 HTTP 方法"""
    try:
        response = await client.options(url)
        if "Allow" in response.headers:
            return response.headers.get("Allow").split(", ")
    except:
        pass
    
    return []

