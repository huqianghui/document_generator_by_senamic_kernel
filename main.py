# Copyright (c) Microsoft. All rights reserved.

import asyncio
import logging
import os

from dotenv import load_dotenv
from opentelemetry import trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.semconv.resource import ResourceAttributes

from agents.code_validation_agent import CodeValidationAgent
from agents.content_creation_agent import ContentCreationAgent
from agents.user_agent import UserAgent
from custom_selection_strategy import CustomSelectionStrategy
from custom_termination_strategy import CustomTerminationStrategy
from semantic_kernel.agents import AgentGroupChat
from semantic_kernel.contents import AuthorRole, ChatMessageContent

"""
Note: This sample use the `AgentGroupChat` feature of Semantic Kernel, which is
no longer maintained. For a replacement, consider using the `GroupChatOrchestration`.
Read more about the `GroupChatOrchestration` here:
https://learn.microsoft.com/semantic-kernel/frameworks/agent/agent-orchestration/group-chat?pivots=programming-language-python
Here is a migration guide from `AgentGroupChat` to `GroupChatOrchestration`:
https://learn.microsoft.com/semantic-kernel/support/migration/group-chat-orchestration-migration-guide?pivots=programming-language-python
"""

TASK = """
我需要一篇关于MCP的报告。
                        1. 对MCP的语言偏好是中文
                        2. 报告需要以技术白皮书风格编写
                        3. 希望优先引用的权威来源是Anthropic
                        4. 针对应用案例部分，是偏好开放源代码项目为例
                        5. 报告预计字数在5000字以内
                    
                    整理一份详细的技术报告，内容涵盖以下内容：

                    引言
                        Model Context Protocol的背景和发展
                        它作为function call扩展的意义及目标
                    历史背景
                        协议的起源和动机
                        其在技术发展中的定位
                        协议结构与工作原理
                        详细描述协议的架构和组件
                        数据流如何在协议中传递
                        重点解析与function call的结合方式
                    技术实现细节
                        具体的实现机制
                        使用的技术栈和关键算法
                        数据格式和传输技术
                    优势与应用案例
                        与其他协议相比的主要技术或性能优势
                        当前已知的实际应用场景
                    与其他协议的比较
                        功能、性能、兼容性等方面的对比分析
                        潜在的改进方向
                    总结与展望
                        Model Context Protocol的未来发展方向
                        潜在的技术革新与生态扩展 
"""

load_dotenv()
AZURE_APP_INSIGHTS_CONNECTION_STRING = os.getenv("AZURE_APP_INSIGHTS_CONNECTION_STRING")

resource = Resource.create({ResourceAttributes.SERVICE_NAME: "Document Generator"})


def set_up_tracing():
    from azure.monitor.opentelemetry.exporter import AzureMonitorTraceExporter
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor
    from opentelemetry.trace import set_tracer_provider

    # Initialize a trace provider for the application. This is a factory for creating tracers.
    tracer_provider = TracerProvider(resource=resource)
    tracer_provider.add_span_processor(
        BatchSpanProcessor(AzureMonitorTraceExporter(connection_string=AZURE_APP_INSIGHTS_CONNECTION_STRING))
    )
    # Sets the global default tracer provider
    set_tracer_provider(tracer_provider)


def set_up_logging():
    from azure.monitor.opentelemetry.exporter import AzureMonitorLogExporter
    from opentelemetry._logs import set_logger_provider
    from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler
    from opentelemetry.sdk._logs.export import BatchLogRecordProcessor

    # Create and set a global logger provider for the application.
    logger_provider = LoggerProvider(resource=resource)
    logger_provider.add_log_record_processor(
        BatchLogRecordProcessor(AzureMonitorLogExporter(connection_string=AZURE_APP_INSIGHTS_CONNECTION_STRING))
    )
    # Sets the global default logger provider
    set_logger_provider(logger_provider)

    # Create a logging handler to write logging records, in OTLP format, to the exporter.
    handler = LoggingHandler()
    # Attach the handler to the root logger. `getLogger()` with no arguments returns the root logger.
    # Events from all child loggers will be processed by this handler.
    logger = logging.getLogger()
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)


async def main():
    if AZURE_APP_INSIGHTS_CONNECTION_STRING:
        set_up_tracing()
        set_up_logging()

    tracer = trace.get_tracer(__name__)
    with tracer.start_as_current_span("main"):
        agents = [
            ContentCreationAgent(),
            UserAgent(),
            CodeValidationAgent(),
        ]

        group_chat = AgentGroupChat(
            agents=agents,
            termination_strategy=CustomTerminationStrategy(agents=agents),
            selection_strategy=CustomSelectionStrategy(),
        )
        await group_chat.add_chat_message(
            ChatMessageContent(
                role=AuthorRole.USER,
                content=TASK.strip(),
            )
        )

        async for response in group_chat.invoke():
            print(f"==== {response.name} just responded ====")
            # print(response.content)

        content_history: list[ChatMessageContent] = []
        async for message in group_chat.get_chat_messages(agent=agents[0]):
            if message.name == agents[0].name:
                # The chat history contains responses from other agents.
                content_history.append(message)
        # The chat history is in descending order.
        print("Final content:")
        print(content_history[0].content)


if __name__ == "__main__":
    asyncio.run(main())
