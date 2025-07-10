# Copyright (c) Microsoft. All rights reserved.

import asyncio
import logging
from typing import List, Optional

from agents.code_validation_agent import CodeValidationAgent
from agents.content_creation_agent import ContentCreationAgent
from agents.user_agent import UserAgent
from semantic_kernel.agents.orchestration.group_chat import (
    GroupChatOrchestration, 
    RoundRobinGroupChatManager,
)
from semantic_kernel.agents.runtime import InProcessRuntime
from semantic_kernel.contents.chat_message_content import ChatMessageContent

"""
根据官方文档的 AgentGroupChat 到 GroupChatOrchestration 迁移示例
参考：https://learn.microsoft.com/en-us/semantic-kernel/frameworks/agent/agent-orchestration/group-chat?pivots=programming-language-python
"""

TASK = """
我需要一篇关于MCP的报告。
内容要求：
1. 包含技术概述
2. 实施方案
3. 最佳实践
4. 代码示例
5. 总结建议

请协作完成这个任务。
"""

# ==========================================
# 清洁版本的迁移示例
# ==========================================

async def simple_migration_example():
    """根据官方文档的正确迁移示例"""
    
    # 定义响应回调函数
    def agent_response_callback(message: ChatMessageContent) -> None:
        print(f"**{message.name}**\n{message.content}\n")
    
    # 创建代理
    agents = [
        ContentCreationAgent(),
        UserAgent(),
        CodeValidationAgent(),
    ]
    
    # 创建群聊编排
    group_chat_orchestration = GroupChatOrchestration(
        members=agents,
        manager=RoundRobinGroupChatManager(max_rounds=5),
        agent_response_callback=agent_response_callback,
    )
    
    # 创建并启动运行时
    runtime = InProcessRuntime()
    runtime.start()
    
    try:
        # 执行编排
        orchestration_result = await group_chat_orchestration.invoke(
            task=TASK,
            runtime=runtime,
        )
        
        # 等待编排完成并获取结果
        value = await orchestration_result.get()
        print(f"\n***** 最终结果 *****\n{value}")
        
    except Exception as e:
        print(f"错误: {e}")
        raise
    
    finally:
        # 停止运行时以清理资源
        await runtime.stop_when_idle()

# ==========================================
# 主函数
# ==========================================

async def main():
    """主函数"""
    print("🎯 AgentGroupChat 到 GroupChatOrchestration 迁移示例")
    print("=" * 80)
    
    # 运行迁移示例
    await simple_migration_example()
    
    print("\n🎉 迁移完成")

if __name__ == "__main__":
    asyncio.run(main())
