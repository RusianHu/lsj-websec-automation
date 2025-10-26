"""
认证与授权安全测试模块
包含认证绕过、会话管理、IDOR、权限提升等测试
"""
from typing import Dict, Any, List, Optional
import httpx
import asyncio
import re
from urllib.parse import urljoin, urlparse, parse_qs
from utils.logger import log
from utils.url_helper import normalize_url


async def test_authentication_bypass(
    login_url: str,
    protected_url: str,
    timeout: int = 10
) -> Dict[str, Any]:
    """
    认证绕过测试 (基于 ffuf 认证测试策略)
    
    Args:
        login_url: 登录页面 URL
        protected_url: 受保护的页面 URL
        timeout: 超时时间
    
    Returns:
        测试结果
    """
    login_url = normalize_url(login_url)
    protected_url = normalize_url(protected_url)
    
    results = []
    
    log.info(f"开始认证绕过测试")
    log.info(f"登录页面: {login_url}")
    log.info(f"受保护页面: {protected_url}")
    
    # 绕过技术列表
    bypass_techniques = [
        {
            "name": "直接访问",
            "headers": {},
            "description": "尝试直接访问受保护资源"
        },
        {
            "name": "X-Original-URL 头绕过",
            "headers": {"X-Original-URL": protected_url},
            "description": "使用 X-Original-URL 头绕过认证"
        },
        {
            "name": "X-Rewrite-URL 头绕过",
            "headers": {"X-Rewrite-URL": protected_url},
            "description": "使用 X-Rewrite-URL 头绕过认证"
        },
        {
            "name": "X-Forwarded-For 本地绕过",
            "headers": {"X-Forwarded-For": "127.0.0.1"},
            "description": "伪造本地 IP 绕过认证"
        },
        {
            "name": "X-Custom-IP-Authorization",
            "headers": {"X-Custom-IP-Authorization": "127.0.0.1"},
            "description": "使用自定义 IP 认证头"
        },
        {
            "name": "Referer 绕过",
            "headers": {"Referer": login_url},
            "description": "使用 Referer 头绕过"
        },
        {
            "name": "User-Agent 绕过",
            "headers": {"User-Agent": "GoogleBot/2.1"},
            "description": "伪装成搜索引擎爬虫"
        },
    ]
    
    async with httpx.AsyncClient(timeout=timeout, follow_redirects=False) as client:
        for technique in bypass_techniques:
            try:
                response = await client.get(protected_url, headers=technique["headers"])
                
                # 判断是否绕过成功
                bypassed = _check_bypass_success(response)
                
                result = {
                    "technique": technique["name"],
                    "description": technique["description"],
                    "status_code": response.status_code,
                    "bypassed": bypassed,
                    "severity": "高" if bypassed else "无",
                    "headers_used": technique["headers"]
                }
                results.append(result)
                
                if bypassed:
                    log.warning(f"认证绕过成功: {technique['name']}")
                else:
                    log.info(f"认证绕过失败: {technique['name']}")
            
            except Exception as e:
                log.debug(f"测试失败: {technique['name']} - {str(e)}")
            
            await asyncio.sleep(0.01)
    
    log.info(f"认证绕过测试完成")
    
    bypassed_count = sum(1 for r in results if r["bypassed"])
    
    return {
        "success": True,
        "login_url": login_url,
        "protected_url": protected_url,
        "total_tests": len(results),
        "bypassed_count": bypassed_count,
        "vulnerable": bypassed_count > 0,
        "results": results
    }


async def test_idor_vulnerability(
    base_url: str,
    id_parameter: str,
    id_range: range,
    auth_headers: Optional[Dict[str, str]] = None,
    timeout: int = 10
) -> Dict[str, Any]:
    """
    IDOR (不安全的直接对象引用) 漏洞测试
    
    Args:
        base_url: 基础 URL (如 https://example.com/api/users/)
        id_parameter: ID 参数名 (如 'id' 或直接在 URL 路径中)
        id_range: ID 范围 (如 range(1, 100))
        auth_headers: 认证头
        timeout: 超时时间
    
    Returns:
        测试结果
    """
    base_url = normalize_url(base_url)
    
    results = []
    accessible_ids = []
    
    log.info(f"开始 IDOR 测试: {base_url}")
    log.info(f"测试 ID 范围: {id_range.start} - {id_range.stop}")
    
    async with httpx.AsyncClient(timeout=timeout, follow_redirects=False) as client:
        for test_id in id_range:
            # 构建测试 URL
            if id_parameter == "path":
                url = urljoin(base_url, str(test_id))
            else:
                url = f"{base_url}?{id_parameter}={test_id}"
            
            try:
                headers = auth_headers if auth_headers else {}
                response = await client.get(url, headers=headers)
                
                # 检查是否可以访问
                if response.status_code == 200:
                    accessible_ids.append(test_id)
                    
                    result = {
                        "id": test_id,
                        "url": url,
                        "status_code": response.status_code,
                        "content_length": len(response.content),
                        "accessible": True
                    }
                    results.append(result)
                    log.info(f"可访问 ID: {test_id} [{response.status_code}]")
            
            except Exception as e:
                log.debug(f"请求失败: {url} - {str(e)}")
            
            await asyncio.sleep(0.01)
    
    log.info(f"IDOR 测试完成，发现 {len(accessible_ids)} 个可访问的 ID")
    
    # 判断是否存在 IDOR 漏洞
    vulnerable = len(accessible_ids) > 1
    
    return {
        "success": True,
        "base_url": base_url,
        "tested_range": f"{id_range.start}-{id_range.stop}",
        "accessible_count": len(accessible_ids),
        "vulnerable": vulnerable,
        "severity": "高" if vulnerable else "无",
        "description": f"发现 {len(accessible_ids)} 个可访问的对象 ID，可能存在 IDOR 漏洞" if vulnerable else "未发现 IDOR 漏洞",
        "accessible_ids": accessible_ids[:20],  # 只返回前 20 个
        "results": results[:20]
    }


async def test_session_management(
    login_url: str,
    credentials: Dict[str, str],
    protected_url: str,
    timeout: int = 10
) -> Dict[str, Any]:
    """
    会话管理测试
    
    Args:
        login_url: 登录 URL
        credentials: 登录凭证 (如 {"username": "test", "password": "test"})
        protected_url: 受保护的 URL
        timeout: 超时时间
    
    Returns:
        测试结果
    """
    login_url = normalize_url(login_url)
    protected_url = normalize_url(protected_url)
    
    results = {
        "tests": []
    }
    
    log.info(f"开始会话管理测试")
    
    async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
        # 1. 登录获取会话
        try:
            login_response = await client.post(login_url, data=credentials)
            
            if login_response.status_code == 200:
                log.info("登录成功")
                
                # 检查 Cookie
                cookies = client.cookies
                
                results["tests"].append({
                    "test": "登录",
                    "success": True,
                    "cookies": dict(cookies)
                })
                
                # 2. 测试会话 Cookie 属性
                session_cookie_test = _test_cookie_security(cookies)
                results["tests"].append(session_cookie_test)
                
                # 3. 测试会话固定
                session_fixation_test = await _test_session_fixation(
                    client, login_url, credentials, protected_url
                )
                results["tests"].append(session_fixation_test)
                
                # 4. 测试会话超时
                log.info("会话超时测试需要等待...")
                
            else:
                log.error(f"登录失败: {login_response.status_code}")
                results["tests"].append({
                    "test": "登录",
                    "success": False,
                    "status_code": login_response.status_code
                })
        
        except Exception as e:
            log.error(f"会话管理测试失败: {str(e)}")
    
    log.info(f"会话管理测试完成")
    
    return {
        "success": True,
        "login_url": login_url,
        "results": results
    }


async def test_privilege_escalation(
    base_url: str,
    low_priv_headers: Dict[str, str],
    high_priv_endpoints: List[str],
    timeout: int = 10
) -> Dict[str, Any]:
    """
    权限提升测试
    
    Args:
        base_url: 基础 URL
        low_priv_headers: 低权限用户的认证头
        high_priv_endpoints: 高权限端点列表
        timeout: 超时时间
    
    Returns:
        测试结果
    """
    base_url = normalize_url(base_url)
    
    results = []
    
    log.info(f"开始权限提升测试: {base_url}")
    log.info(f"测试 {len(high_priv_endpoints)} 个高权限端点")
    
    async with httpx.AsyncClient(timeout=timeout, follow_redirects=False) as client:
        for endpoint in high_priv_endpoints:
            url = urljoin(base_url, endpoint)
            
            try:
                # 使用低权限凭证访问高权限端点
                response = await client.get(url, headers=low_priv_headers)
                
                # 判断是否可以访问
                accessible = response.status_code == 200
                
                result = {
                    "endpoint": endpoint,
                    "url": url,
                    "status_code": response.status_code,
                    "accessible": accessible,
                    "vulnerable": accessible,
                    "severity": "高" if accessible else "无"
                }
                results.append(result)
                
                if accessible:
                    log.warning(f"权限提升漏洞: 低权限用户可访问 {endpoint}")
                else:
                    log.info(f"端点受保护: {endpoint}")
            
            except Exception as e:
                log.debug(f"请求失败: {url} - {str(e)}")
            
            await asyncio.sleep(0.01)
    
    log.info(f"权限提升测试完成")
    
    vulnerable_count = sum(1 for r in results if r["vulnerable"])
    
    return {
        "success": True,
        "base_url": base_url,
        "total_endpoints": len(high_priv_endpoints),
        "vulnerable_count": vulnerable_count,
        "vulnerable": vulnerable_count > 0,
        "results": results
    }


# 辅助函数

def _check_bypass_success(response: httpx.Response) -> bool:
    """检查认证绕过是否成功"""
    # 成功的指标
    if response.status_code == 200:
        # 检查是否包含登录表单（如果包含，说明未绕过）
        if re.search(r'<form.*login', response.text, re.IGNORECASE):
            return False
        
        # 检查是否重定向到登录页
        if "login" in response.text.lower() and len(response.text) < 1000:
            return False
        
        return True
    
    return False


def _test_cookie_security(cookies) -> Dict[str, Any]:
    """测试 Cookie 安全属性"""
    issues = []
    
    for cookie in cookies.jar:
        # 检查 Secure 标志
        if not cookie.secure:
            issues.append(f"Cookie '{cookie.name}' 缺少 Secure 标志")
        
        # 检查 HttpOnly 标志
        if not cookie.has_nonstandard_attr("HttpOnly"):
            issues.append(f"Cookie '{cookie.name}' 缺少 HttpOnly 标志")
        
        # 检查 SameSite 属性
        if not cookie.has_nonstandard_attr("SameSite"):
            issues.append(f"Cookie '{cookie.name}' 缺少 SameSite 属性")
    
    return {
        "test": "Cookie 安全属性",
        "issues": issues,
        "vulnerable": len(issues) > 0,
        "severity": "中" if len(issues) > 0 else "无"
    }


async def _test_session_fixation(
    client: httpx.AsyncClient,
    login_url: str,
    credentials: Dict[str, str],
    protected_url: str
) -> Dict[str, Any]:
    """测试会话固定漏洞"""
    # 获取登录前的 Cookie
    try:
        pre_login_response = await client.get(login_url)
        pre_login_cookies = dict(client.cookies)
        
        # 登录
        await client.post(login_url, data=credentials)
        post_login_cookies = dict(client.cookies)
        
        # 比较 Cookie 是否改变
        if pre_login_cookies == post_login_cookies:
            return {
                "test": "会话固定",
                "vulnerable": True,
                "severity": "高",
                "description": "登录前后会话 ID 未改变，存在会话固定漏洞"
            }
        else:
            return {
                "test": "会话固定",
                "vulnerable": False,
                "description": "登录后会话 ID 已更新"
            }
    
    except Exception as e:
        return {
            "test": "会话固定",
            "error": str(e)
        }

