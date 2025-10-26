"""
Monkey patch Autogen 以兼容不支持 additionalProperties 的 LLM 服务器
"""
from typing import List, Sequence, cast
from openai.types.chat import ChatCompletionToolParam
from openai.types.shared_params import FunctionDefinition, FunctionParameters

from autogen_core.tools import Tool, ToolSchema
from autogen_ext.models.openai import _openai_client
from utils.logger import log


def clean_parameters(parameters: dict) -> dict:
    """
    清理参数字典,移除不兼容的字段
    
    Args:
        parameters: 原始参数字典
        
    Returns:
        清理后的参数字典
    """
    cleaned = dict(parameters)
    
    # 移除 additionalProperties 字段
    if "additionalProperties" in cleaned:
        del cleaned["additionalProperties"]
        log.debug("已移除 additionalProperties 字段")
    
    return cleaned


def convert_tools_patched(
    tools: Sequence[Tool | ToolSchema],
) -> List[ChatCompletionToolParam]:
    """
    转换工具列表为 OpenAI 格式,移除不兼容的字段
    
    这是 autogen_ext.models.openai._openai_client.convert_tools 的修补版本
    """
    result: List[ChatCompletionToolParam] = []
    for tool in tools:
        if isinstance(tool, Tool):
            tool_schema = tool.schema
        else:
            assert isinstance(tool, dict)
            tool_schema = tool

        # 清理 parameters
        parameters = tool_schema.get("parameters", {})
        cleaned_parameters = clean_parameters(parameters) if parameters else {}

        result.append(
            ChatCompletionToolParam(
                type="function",
                function=FunctionDefinition(
                    name=tool_schema["name"],
                    description=(tool_schema["description"] if "description" in tool_schema else ""),
                    parameters=cast(FunctionParameters, cleaned_parameters),
                    # 不包含 strict 字段,或者设置为 None
                    # strict=(tool_schema["strict"] if "strict" in tool_schema else False),
                ),
            )
        )
    
    # 检查所有工具是否有有效的名称
    from autogen_ext.models.openai._openai_client import assert_valid_name
    for tool_param in result:
        assert_valid_name(tool_param["function"]["name"])
    
    log.debug(f"已转换 {len(result)} 个工具,移除了不兼容的字段")
    return result


def apply_patch():
    """应用 monkey patch"""
    log.info("正在应用 Autogen 兼容性补丁...")
    
    # 保存原始函数
    _openai_client._original_convert_tools = _openai_client.convert_tools
    
    # 替换为修补版本
    _openai_client.convert_tools = convert_tools_patched
    
    log.info("✅ Autogen 兼容性补丁已应用")


def remove_patch():
    """移除 monkey patch"""
    if hasattr(_openai_client, '_original_convert_tools'):
        _openai_client.convert_tools = _openai_client._original_convert_tools
        delattr(_openai_client, '_original_convert_tools')
        log.info("Autogen 兼容性补丁已移除")

