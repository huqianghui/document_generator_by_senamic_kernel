#!/usr/bin/env python3
"""
简单演示：当大模型不支持 Function Call 时的处理方案
"""

import asyncio
import json
import re
from typing import Dict, Any

# 模拟的简单插件
class SimpleCalculatorPlugin:
    """简单的计算器插件"""
    
    def add(self, a: int, b: int) -> int:
        """加法运算"""
        return a + b
    
    def multiply(self, a: int, b: int) -> int:
        """乘法运算"""
        return a * b
    
    def get_function_descriptions(self) -> str:
        """获取函数描述（用于 Prompt 模式）"""
        return """
Available Functions:
1. add(a, b) - 计算两个数的和
2. multiply(a, b) - 计算两个数的乘积

To use a function, format your response as:
FUNCTION_CALL: function_name
PARAMETERS: {"a": 5, "b": 3}
"""


class SimpleAgent:
    """简单的 Agent 实现"""
    
    def __init__(self, plugin: SimpleCalculatorPlugin, use_prompt_mode: bool = False):
        self.plugin = plugin
        self.use_prompt_mode = use_prompt_mode
        print(f"🤖 Agent 初始化，模式: {'Prompt 模式' if use_prompt_mode else '原生 Function Call'}")
    
    async def process_message(self, message: str) -> str:
        """处理用户消息"""
        if self.use_prompt_mode:
            return await self._process_with_prompt_mode(message)
        else:
            return await self._process_with_native_mode(message)
    
    async def _process_with_native_mode(self, message: str) -> str:
        """原生 Function Call 模式处理"""
        # 在真实环境中，这里会调用大模型的原生 Function Call
        # 这里我们模拟大模型不支持的情况
        return "❌ 抱歉，当前模型不支持原生 Function Call 功能"
    
    async def _process_with_prompt_mode(self, message: str) -> str:
        """Prompt 模式处理"""
        # 1. 向用户消息添加函数描述
        enhanced_message = f"""
{self.plugin.get_function_descriptions()}

User: {message}

If you need to use a function, respond with the function call format. Otherwise, respond normally.
"""
        
        # 2. 模拟大模型的响应（在实际应用中，这里会调用真实的大模型）
        simulated_response = await self._simulate_model_response(enhanced_message)
        
        # 3. 检查响应中是否包含函数调用
        if "FUNCTION_CALL:" in simulated_response:
            return await self._execute_function_from_response(simulated_response)
        else:
            return simulated_response
    
    async def _simulate_model_response(self, enhanced_message: str) -> str:
        """模拟大模型的响应"""
        # 在实际应用中，这里会调用真实的大模型 API
        # 这里我们模拟一个简单的响应
        
        if "计算" in enhanced_message and "加" in enhanced_message:
            return """
我需要使用加法函数来计算结果。

FUNCTION_CALL: add
PARAMETERS: {"a": 10, "b": 20}
"""
        elif "计算" in enhanced_message and "乘" in enhanced_message:
            return """
我需要使用乘法函数来计算结果。

FUNCTION_CALL: multiply
PARAMETERS: {"a": 5, "b": 6}
"""
        else:
            return "我是一个简单的 AI 助手，可以帮您进行数学计算。"
    
    async def _execute_function_from_response(self, response: str) -> str:
        """从响应中解析并执行函数调用"""
        try:
            # 解析函数名
            func_match = re.search(r'FUNCTION_CALL:\s*(\w+)', response)
            if not func_match:
                return "❌ 无法解析函数名"
            
            func_name = func_match.group(1)
            
            # 解析参数
            params_match = re.search(r'PARAMETERS:\s*(\{.*?\})', response, re.DOTALL)
            if not params_match:
                return "❌ 无法解析函数参数"
            
            params_str = params_match.group(1)
            parameters = json.loads(params_str)
            
            # 执行函数
            if hasattr(self.plugin, func_name):
                func = getattr(self.plugin, func_name)
                result = func(**parameters)
                return f"✅ 函数 {func_name} 执行成功\n参数: {parameters}\n结果: {result}"
            else:
                return f"❌ 函数 {func_name} 不存在"
                
        except Exception as e:
            return f"❌ 函数执行失败: {str(e)}"


async def demo_function_call_compatibility():
    """演示函数调用兼容性"""
    
    print("🚀 演示：处理不支持 Function Call 的大模型")
    print("=" * 60)
    
    # 创建插件
    calculator = SimpleCalculatorPlugin()
    
    # 测试场景1：原生 Function Call 模式（模拟不支持的情况）
    print("\n📝 场景1：尝试使用原生 Function Call")
    print("-" * 40)
    
    native_agent = SimpleAgent(calculator, use_prompt_mode=False)
    result1 = await native_agent.process_message("请帮我计算 10 + 20")
    print(f"结果: {result1}")
    
    # 测试场景2：Prompt 模式（兼容性解决方案）
    print("\n📝 场景2：使用 Prompt 模式作为替代方案")
    print("-" * 40)
    
    prompt_agent = SimpleAgent(calculator, use_prompt_mode=True)
    result2 = await prompt_agent.process_message("请帮我计算 10 + 20")
    print(f"结果: {result2}")
    
    # 测试场景3：乘法运算
    print("\n📝 场景3：测试乘法运算")
    print("-" * 40)
    
    result3 = await prompt_agent.process_message("请帮我计算 5 × 6")
    print(f"结果: {result3}")
    
    # 测试场景4：普通对话
    print("\n📝 场景4：测试普通对话")
    print("-" * 40)
    
    result4 = await prompt_agent.process_message("你好，请介绍一下自己")
    print(f"结果: {result4}")
    
    print("\n" + "=" * 60)
    print("✅ 演示完成")


if __name__ == "__main__":
    asyncio.run(demo_function_call_compatibility())
