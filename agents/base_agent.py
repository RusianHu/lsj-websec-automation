"""
基础 Agent 模块
"""
from typing import Optional, List, Callable, Any, Dict

from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.teams import RoundRobinGroupChat
from autogen_agentchat.conditions import MaxMessageTermination, TextMentionTermination
from autogen_ext.models.openai import OpenAIChatCompletionClient
from config.settings import settings
from utils.logger import log


class BaseSecurityAgent:
    """安全测试基础 Agent"""
    
    def __init__(
        self,
        name: str,
        system_message: str,
        tools: Optional[List[Callable]] = None,
        model_client: Optional[OpenAIChatCompletionClient] = None
    ):
        """
        初始化 Agent
        
        Args:
            name: Agent 名称
            system_message: 系统消息
            tools: 工具函数列表
            model_client: 模型客户端
        """
        self.name = name
        self.system_message = system_message
        self.tools = tools or []
        
        model_info = settings.llm.get_effective_model_info()
        client_kwargs: Dict[str, Any] = {
            "model": settings.llm.model,
            "api_key": settings.llm.api_key,
            "base_url": settings.llm.api_base,
            "temperature": settings.llm.temperature,
            "seed": settings.llm.seed,
        }
        if model_info is not None:
            client_kwargs["model_info"] = model_info
        
        # 创建模型客户端
        if model_client is None:
            self.model_client = OpenAIChatCompletionClient(**client_kwargs)
        else:
            self.model_client = model_client
        
        # 创建 Agent
        self.agent = AssistantAgent(
            name=self.name,
            system_message=self.system_message,
            model_client=self.model_client,
            tools=self.tools,
            reflect_on_tool_use=settings.app.autogen_reflect_on_tool_use,
        )
        
        log.info(f"Agent '{self.name}' 初始化成功")
    
    async def run(self, task: str, max_turns: Optional[int] = None) -> Any:
        """
        运行任务

        Args:
            task: 任务描述
            max_turns: 最大消息数，如果为 None 则使用配置文件中的值

        Returns:
            任务结果
        """
        # 如果未指定 max_turns，使用配置文件中的值
        if max_turns is None:
            max_turns = settings.app.autogen_max_turns

        log.info(f"Agent '{self.name}' 开始执行任务: {task}")
        log.info(f"最大轮数设置: {max_turns}")

        # 使用 RoundRobinGroupChat 来控制对话轮次
        # 创建一个只包含当前 agent 的团队
        # 组合两个终止条件: 达到最大消息数 或 检测到 TERMINATE 关键词
        max_msg_termination = MaxMessageTermination(max_messages=max_turns)
        # 仅当来自当前 Assistant 的消息包含 TERMINATE 时才触发终止，避免用户任务/系统提示中的术语误触发
        text_termination = TextMentionTermination("TERMINATE", sources=[self.name])

        # 使用 OR 逻辑: 任一条件满足即终止
        termination = max_msg_termination | text_termination

        team = RoundRobinGroupChat([self.agent], termination_condition=termination)

        # 运行任务
        result = await team.run(task=task)

        log.info(f"Agent '{self.name}' 任务执行完成")
        return result
    
    async def close(self):
        """关闭 Agent"""
        if self.model_client:
            await self.model_client.close()
        log.info(f"Agent '{self.name}' 已关闭")


def create_model_client(
    model: Optional[str] = None,
    api_key: Optional[str] = None,
    base_url: Optional[str] = None,
    temperature: Optional[float] = None,
    seed: Optional[int] = None,
    model_info: Optional[Any] = None,
) -> OpenAIChatCompletionClient:
    """
    创建模型客户端

    Args:
        model: 模型名称
        api_key: API 密钥
        base_url: API 基础 URL
        temperature: 温度参数
        seed: 随机种子
        model_info: 模型能力说明

    Returns:
        OpenAIChatCompletionClient 实例
    """
    effective_model_info = model_info or settings.llm.get_effective_model_info()
    client_kwargs: Dict[str, Any] = {
        "model": model or settings.llm.model,
        "api_key": api_key or settings.llm.api_key,
        "base_url": base_url or settings.llm.api_base,
        "temperature": temperature if temperature is not None else settings.llm.temperature,
        "seed": seed if seed is not None else settings.llm.seed,
    }
    if effective_model_info is not None:
        client_kwargs["model_info"] = effective_model_info

    return OpenAIChatCompletionClient(
        **client_kwargs
    )
