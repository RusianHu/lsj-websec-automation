"""
Monkey patch Autogen 以兼容不支持 additionalProperties 的 LLM 服务器
"""
from typing import Any, List, Optional, Sequence, Tuple, cast
from openai.types.chat import ChatCompletionToolParam
from openai.types.shared_params import FunctionDefinition, FunctionParameters

from autogen_core.tools import Tool, ToolSchema
from autogen_ext.models.openai import _openai_client
from utils.logger import log


def _remove_additional_properties(data: Any, path: str = "") -> Tuple[Any, int]:
    """
    递归移除 JSON Schema 中的 additionalProperties 字段

    Args:
        data: 待处理的数据结构
        path: 当前处理路径,用于调试日志

    Returns:
        (清理后的数据, 移除的字段数量)
    """
    removed = 0

    if isinstance(data, dict):
        cleaned_dict = {}
        for key, value in data.items():
            current_path = f"{path}.{key}" if path else key
            if key == "additionalProperties":
                removed += 1
                log.debug(f"已移除 additionalProperties 字段: {current_path}")
                continue
            cleaned_value, child_removed = _remove_additional_properties(value, current_path)
            cleaned_dict[key] = cleaned_value
            removed += child_removed
        return cleaned_dict, removed

    if isinstance(data, list):
        cleaned_list = []
        for index, item in enumerate(data):
            current_path = f"{path}[{index}]"
            cleaned_item, child_removed = _remove_additional_properties(item, current_path)
            cleaned_list.append(cleaned_item)
            removed += child_removed
        return cleaned_list, removed

    return data, removed


def clean_parameters(parameters: dict) -> dict:
    """
    清理参数字典,移除不兼容的字段
    
    Args:
        parameters: 原始参数字典
        
    Returns:
        清理后的参数字典
    """
    cleaned, removed_count = _remove_additional_properties(parameters)

    if removed_count > 0:
        log.debug(f"共移除 {removed_count} 处 additionalProperties 字段")

    return cleaned


def process_create_args_patched(
    self,
    messages: Sequence[Any],
    tools: Sequence[Any] = (),
    tool_choice: Any = "auto",
    json_output: Any = None,
    extra_create_args: Optional[dict] = None,
):
    """
    监控并调整 OpenAI create 参数,便于兼容第三方服务
    """
    if extra_create_args is None:
        extra_create_args = {}

    params = _openai_client._original_process_create_args(  # type: ignore[attr-defined]
        self,
        messages,
        tools,
        tool_choice,
        json_output,
        extra_create_args,
    )

    tool_choice_value = params.create_args.get("tool_choice")
    if tool_choice_value == "none" and params.tools:
        log.debug(
            "检测到 tool_choice='none' 但仍包含 {} 个工具,可能触发兼容性问题".format(len(params.tools))
        )

    log.debug(
        "LLM 请求 create_args: keys={}, tool_choice={}".format(
            sorted(params.create_args.keys()),
            tool_choice_value,
        )
    )

    return params


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
    _openai_client._original_process_create_args = (
        _openai_client.OpenAIChatCompletionClient._process_create_args  # type: ignore[attr-defined]
    )
    
    # 替换为修补版本
    _openai_client.convert_tools = convert_tools_patched
    _openai_client.OpenAIChatCompletionClient._process_create_args = process_create_args_patched  # type: ignore[attr-defined]
    
    log.info("✅ Autogen 兼容性补丁已应用")


def remove_patch():
    """移除 monkey patch"""
    if hasattr(_openai_client, '_original_convert_tools'):
        _openai_client.convert_tools = _openai_client._original_convert_tools
        delattr(_openai_client, '_original_convert_tools')
        log.info("Autogen 兼容性补丁已移除")

    if hasattr(_openai_client, '_original_process_create_args'):
        _openai_client.OpenAIChatCompletionClient._process_create_args = (  # type: ignore[attr-defined]
            _openai_client._original_process_create_args
        )
        delattr(_openai_client, '_original_process_create_args')
