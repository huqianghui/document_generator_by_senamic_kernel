#!/usr/bin/env python3
"""
演示如何处理不支持 Function Call 的大模型
"""

import asyncio
import json
import re
from typing import Dict, List, Optional, Any
from semantic_kernel.agents import ChatCompletionAgent
from semantic_kernel.contents import ChatMessageContent
from semantic_kernel.contents.utils.author_role import AuthorRole
from semantic_kernel.connectors.ai.function_choice_behavior import FunctionChoiceBehavior
from agents.custom_agent_base import CustomAgentBase, Services
from plugins.code_execution_plugin import CodeExecutionPlugin
from plugins.repo_file_plugin import RepoFilePlugin


class PromptBasedFunctionCaller:
    """基于 Prompt 的函数调用模拟器"""
    
    def __init__(self, plugins: List[object]):
        self.plugins = plugins
        self.function_map = self._build_function_map()
    
    def _build_function_map(self) -> Dict[str, Any]:
        """构建函数映射"""
        function_map = {}
        
        for plugin in self.plugins:
            # 获取插件中的所有方法
            for method_name in dir(plugin):
                method = getattr(plugin, method_name)
                if callable(method) and hasattr(method, '__annotations__'):
                    # 检查是否是 kernel_function
                    if hasattr(method, '_kernel_function_metadata'):
                        function_map[method_name] = {
                            'plugin': plugin,
                            'method': method,
                            'description': getattr(method, '__doc__', ''),
                            'metadata': method._kernel_function_metadata
                        }
        
        return function_map
    
    def get_function_descriptions(self) -> str:
        """获取所有函数的描述"""
        descriptions = []
        
        descriptions.append("You have access to the following functions:")
        descriptions.append("")
        
        for func_name, func_info in self.function_map.items():
            desc = f"Function: {func_name}"
            if func_info['description']:
                desc += f"\nDescription: {func_info['description']}"
            
            # 获取参数信息
            method = func_info['method']
            if hasattr(method, '__annotations__'):
                params = []
                for param_name, param_type in method.__annotations__.items():
                    if param_name != 'return':
                        params.append(f"{param_name}: {param_type}")
                if params:
                    desc += f"\nParameters: {', '.join(params)}"
            
            descriptions.append(desc)
            descriptions.append("")
        
        descriptions.append("To call a function, use this format:")
        descriptions.append("FUNCTION_CALL: function_name")
        descriptions.append("PARAMETERS: {\"param1\": \"value1\", \"param2\": \"value2\"}")
        descriptions.append("")
        
        return "\n".join(descriptions)
    
    async def execute_function_call(self, func_name: str, parameters: Dict[str, Any]) -> str:
        """执行函数调用"""
        if func_name not in self.function_map:
            return f"❌ Function '{func_name}' not found"
        
        try:
            func_info = self.function_map[func_name]
            method = func_info['method']
            
            # 执行函数
            if asyncio.iscoroutinefunction(method):
                result = await method(**parameters)
            else:
                result = method(**parameters)
            
            return f"✅ Function '{func_name}' executed successfully.\nResult: {result}"
            
        except Exception as e:
            return f"❌ Function '{func_name}' execution failed: {str(e)}"


class AdaptiveAgent(CustomAgentBase):
    """自适应的 Agent，支持原生和 Prompt 模式的函数调用"""
    
    def __init__(self, force_prompt_mode: bool = False):
        super().__init__(
            service=self._create_ai_service(Services.AZURE_OPENAI),
            plugins=[CodeExecutionPlugin(), RepoFilePlugin()],
            name="AdaptiveAgent",
            instructions="You are a helpful assistant that can execute code and work with files.",
            description="An adaptive agent that works with both native and prompt-based function calling."
        )
        
        self.force_prompt_mode = force_prompt_mode
        self.prompt_function_caller = PromptBasedFunctionCaller(
            [CodeExecutionPlugin(), RepoFilePlugin()]
        )
        
        # 配置函数调用行为
        if self.force_prompt_mode:
            self.function_choice_behavior = FunctionChoiceBehavior.None_()
            print("🔄 强制使用 Prompt 模式")
        else:
            self.function_choice_behavior = FunctionChoiceBehavior.Auto()
            print("✅ 使用原生 Function Call 模式")
    
    async def invoke(self, messages, **kwargs):
        """重写 invoke 方法以支持 Prompt 模式"""
        if self.force_prompt_mode:
            # 使用 Prompt 模式
            async for response in self._invoke_with_prompt_mode(messages, **kwargs):
                yield response
        else:
            # 使用原生模式
            async for response in super().invoke(messages=messages, **kwargs):
                yield response
    
    async def _invoke_with_prompt_mode(self, messages, **kwargs):
        """使用 Prompt 模式处理"""
        # 增强消息，添加函数描述
        enhanced_messages = self._enhance_messages_with_functions(messages)
        
        # 调用父类方法（禁用了原生 Function Call）
        async for response in super().invoke(messages=enhanced_messages, **kwargs):
            # 检查响应是否包含函数调用
            processed_response = await self._process_prompt_function_calls(response)
            yield processed_response
    
    def _enhance_messages_with_functions(self, messages):
        """增强消息，添加函数描述"""
        function_descriptions = self.prompt_function_caller.get_function_descriptions()
        
        if isinstance(messages, str):
            enhanced_content = f"{function_descriptions}\n\nUser: {messages}"
            return [ChatMessageContent(role=AuthorRole.USER, content=enhanced_content)]
        elif isinstance(messages, list):
            enhanced_messages = []
            for msg in messages:
                if isinstance(msg, str):
                    enhanced_content = f"{function_descriptions}\n\nUser: {msg}"
                    enhanced_messages.append(ChatMessageContent(role=AuthorRole.USER, content=enhanced_content))
                else:
                    enhanced_messages.append(msg)
            return enhanced_messages
        else:
            return messages
    
    async def _process_prompt_function_calls(self, response):
        """处理 Prompt 模式的函数调用"""
        content = response.message.content
        
        # 检查是否包含函数调用
        if "FUNCTION_CALL:" in content:
            try:
                # 解析函数调用
                func_name, parameters = self._parse_function_call(content)
                print(f"🔧 检测到函数调用: {func_name} with {parameters}")
                
                # 执行函数
                result = await self.prompt_function_caller.execute_function_call(func_name, parameters)
                
                # 更新响应内容
                response.message.content = result
                
            except Exception as e:
                response.message.content = f"❌ 函数调用解析失败: {str(e)}"
        
        return response
    
    def _parse_function_call(self, content: str) -> tuple[str, Dict[str, Any]]:
        """解析函数调用格式"""
        # 提取函数名
        func_match = re.search(r'FUNCTION_CALL:\s*(\w+)', content)
        if not func_match:
            raise ValueError("无法找到函数名")
        
        func_name = func_match.group(1)
        
        # 提取参数
        params_match = re.search(r'PARAMETERS:\s*(\{.*?\})', content, re.DOTALL)
        if params_match:
            params_str = params_match.group(1)
            try:
                parameters = json.loads(params_str)
            except json.JSONDecodeError:
                parameters = {}
        else:
            parameters = {}
        
        return func_name, parameters


class ModelCompatibilityTester:
    """模型兼容性测试器"""
    
    @staticmethod
    async def test_native_function_call():
        """测试原生 Function Call 模式"""
        print("=" * 50)
        print("🧪 测试原生 Function Call 模式")
        print("=" * 50)
        
        agent = AdaptiveAgent(force_prompt_mode=False)
        
        test_message = "请运行这段 Python 代码：print('Hello from native function call!')"
        
        try:
            async for response in agent.invoke(test_message):
                print(f"📤 响应: {response.message.content}")
        except Exception as e:
            print(f"❌ 原生模式失败: {e}")
    
    @staticmethod
    async def test_prompt_function_call():
        """测试 Prompt 模式的函数调用"""
        print("\n" + "=" * 50)
        print("🧪 测试 Prompt 模式的函数调用")
        print("=" * 50)
        
        agent = AdaptiveAgent(force_prompt_mode=True)
        
        test_message = "请运行这段 Python 代码：print('Hello from prompt-based function call!')"
        
        try:
            async for response in agent.invoke(test_message):
                print(f"📤 响应: {response.message.content}")
        except Exception as e:
            print(f"❌ Prompt 模式失败: {e}")
    
    @staticmethod
    async def test_file_operations():
        """测试文件操作功能"""
        print("\n" + "=" * 50)
        print("🧪 测试文件操作功能 (Prompt 模式)")
        print("=" * 50)
        
        agent = AdaptiveAgent(force_prompt_mode=True)
        
        test_message = "请创建一个名为 'test.txt' 的文件，内容为 'Hello, World!'"
        
        try:
            async for response in agent.invoke(test_message):
                print(f"📤 响应: {response.message.content}")
        except Exception as e:
            print(f"❌ 文件操作失败: {e}")


async def main():
    """主函数"""
    print("🚀 开始测试 Semantic Kernel 的函数调用兼容性")
    
    # 测试原生 Function Call
    await ModelCompatibilityTester.test_native_function_call()
    
    # 测试 Prompt 模式
    await ModelCompatibilityTester.test_prompt_function_call()
    
    # 测试文件操作
    await ModelCompatibilityTester.test_file_operations()
    
    print("\n" + "=" * 50)
    print("✅ 测试完成")
    print("=" * 50)


if __name__ == "__main__":
    asyncio.run(main())
