#!/usr/bin/env python3
"""
统一函数调用架构演示
展示 Plugin 和 MCP Server 的本质相似性，以及如何实现混合架构
"""

import asyncio
import json
import time
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass
from abc import ABC, abstractmethod

# 模拟 Semantic Kernel 的 kernel_function 装饰器
def kernel_function(description: str = ""):
    def decorator(func):
        func._kernel_function_metadata = {
            'name': func.__name__,
            'description': description,
            'parameters': {
                'type': 'object',
                'properties': {},
                'required': []
            }
        }
        return func
    return decorator

# 模拟 MCP 客户端
class MockMCPClient:
    def __init__(self, server_name: str):
        self.server_name = server_name
        self.tools = [
            {
                'name': 'fetch_web_content',
                'description': '获取网页内容',
                'inputSchema': {
                    'type': 'object',
                    'properties': {
                        'url': {'type': 'string'}
                    },
                    'required': ['url']
                }
            },
            {
                'name': 'analyze_sentiment',
                'description': '分析文本情感',
                'inputSchema': {
                    'type': 'object',
                    'properties': {
                        'text': {'type': 'string'}
                    },
                    'required': ['text']
                }
            }
        ]
    
    def list_tools(self) -> List[Dict]:
        return self.tools
    
    async def call_tool(self, name: str, arguments: Dict) -> Dict:
        """模拟 MCP 远程调用"""
        # 模拟网络延迟
        await asyncio.sleep(0.1)
        
        if name == 'fetch_web_content':
            return {
                'content': f"网页内容来自 {arguments['url']}",
                'status': 'success'
            }
        elif name == 'analyze_sentiment':
            return {
                'sentiment': 'positive' if 'good' in arguments['text'] else 'negative',
                'confidence': 0.85
            }
        else:
            return {'error': f'Unknown tool: {name}'}

# 本地 Plugin 示例
class LocalPlugin:
    @kernel_function(description="执行数学计算")
    def calculate(self, expression: str) -> str:
        try:
            result = eval(expression)
            return f"计算结果: {result}"
        except Exception as e:
            return f"计算错误: {str(e)}"
    
    @kernel_function(description="格式化文本")
    def format_text(self, text: str, style: str = "upper") -> str:
        if style == "upper":
            return text.upper()
        elif style == "lower":
            return text.lower()
        elif style == "title":
            return text.title()
        else:
            return text

# 函数调用信息
@dataclass
class FunctionCallInfo:
    name: str
    description: str
    schema: Dict[str, Any]
    executor_type: str  # 'local' or 'remote'
    executor: Any

# 统一函数注册表
class UnifiedFunctionRegistry:
    def __init__(self):
        self.functions: Dict[str, FunctionCallInfo] = {}
        self.call_stats = {
            'local_calls': 0,
            'remote_calls': 0,
            'total_time': 0
        }
    
    def register_plugin(self, plugin: Any):
        """注册本地 Plugin"""
        for method_name in dir(plugin):
            if method_name.startswith('_'):
                continue
            
            method = getattr(plugin, method_name)
            if hasattr(method, '_kernel_function_metadata'):
                metadata = method._kernel_function_metadata
                self.functions[method_name] = FunctionCallInfo(
                    name=method_name,
                    description=metadata['description'],
                    schema=metadata['parameters'],
                    executor_type='local',
                    executor=method
                )
                print(f"✓ 注册本地函数: {method_name}")
    
    def register_mcp_server(self, mcp_client: MockMCPClient):
        """注册远程 MCP Server"""
        tools = mcp_client.list_tools()
        for tool in tools:
            self.functions[tool['name']] = FunctionCallInfo(
                name=tool['name'],
                description=tool['description'],
                schema=tool['inputSchema'],
                executor_type='remote',
                executor=mcp_client
            )
            print(f"✓ 注册远程函数: {tool['name']}")
    
    def list_all_functions(self) -> Dict[str, Dict]:
        """列出所有可用函数"""
        result = {}
        for name, info in self.functions.items():
            result[name] = {
                'name': info.name,
                'description': info.description,
                'type': info.executor_type,
                'schema': info.schema
            }
        return result
    
    async def call_function(self, name: str, arguments: Dict) -> Dict:
        """统一函数调用接口"""
        if name not in self.functions:
            return {'error': f'函数 {name} 不存在'}
        
        func_info = self.functions[name]
        start_time = time.time()
        
        try:
            if func_info.executor_type == 'local':
                # 本地函数调用
                result = func_info.executor(**arguments)
                self.call_stats['local_calls'] += 1
                return {'result': result, 'type': 'local'}
            
            elif func_info.executor_type == 'remote':
                # 远程函数调用
                result = await func_info.executor.call_tool(name, arguments)
                self.call_stats['remote_calls'] += 1
                return {'result': result, 'type': 'remote'}
            
        except Exception as e:
            return {'error': str(e), 'type': func_info.executor_type}
        
        finally:
            elapsed = time.time() - start_time
            self.call_stats['total_time'] += elapsed
    
    def get_stats(self) -> Dict:
        """获取调用统计"""
        return self.call_stats.copy()

# 模拟 AI 选择和调用函数的过程
class AIFunctionCaller:
    def __init__(self, registry: UnifiedFunctionRegistry):
        self.registry = registry
    
    def get_available_functions(self) -> str:
        """获取可用函数列表（模拟发送给 AI 的 Function Call Schema）"""
        functions = self.registry.list_all_functions()
        return json.dumps(functions, indent=2, ensure_ascii=False)
    
    async def simulate_ai_call(self, user_request: str) -> Dict:
        """模拟 AI 根据用户请求选择和调用函数"""
        print(f"\n🤖 AI 收到用户请求: {user_request}")
        
        # 模拟 AI 的决策过程
        if "计算" in user_request:
            # 选择本地函数
            return await self.registry.call_function('calculate', {'expression': '2 + 3 * 4'})
        
        elif "格式化" in user_request:
            # 选择本地函数
            return await self.registry.call_function('format_text', {'text': 'hello world', 'style': 'title'})
        
        elif "网页" in user_request:
            # 选择远程函数
            return await self.registry.call_function('fetch_web_content', {'url': 'https://example.com'})
        
        elif "情感" in user_request:
            # 选择远程函数
            return await self.registry.call_function('analyze_sentiment', {'text': 'This is a good day'})
        
        else:
            return {'error': '无法理解用户请求'}

# 性能对比测试
class PerformanceComparison:
    def __init__(self, registry: UnifiedFunctionRegistry):
        self.registry = registry
    
    async def compare_performance(self):
        """对比本地和远程函数调用性能"""
        print("\n📊 性能对比测试")
        
        # 测试本地函数调用
        print("\n测试本地函数调用性能...")
        local_times = []
        for i in range(10):
            start = time.time()
            await self.registry.call_function('calculate', {'expression': '1 + 1'})
            local_times.append(time.time() - start)
        
        # 测试远程函数调用
        print("测试远程函数调用性能...")
        remote_times = []
        for i in range(10):
            start = time.time()
            await self.registry.call_function('fetch_web_content', {'url': 'https://test.com'})
            remote_times.append(time.time() - start)
        
        # 打印结果
        avg_local = sum(local_times) / len(local_times) * 1000
        avg_remote = sum(remote_times) / len(remote_times) * 1000
        
        print(f"本地函数平均耗时: {avg_local:.2f}ms")
        print(f"远程函数平均耗时: {avg_remote:.2f}ms")
        print(f"性能差异: {avg_remote/avg_local:.1f}x")

# 主演示函数
async def main():
    print("🚀 统一函数调用架构演示")
    print("=" * 50)
    
    # 1. 创建统一注册表
    registry = UnifiedFunctionRegistry()
    
    # 2. 注册本地 Plugin
    print("\n📦 注册本地 Plugin...")
    local_plugin = LocalPlugin()
    registry.register_plugin(local_plugin)
    
    # 3. 注册远程 MCP Server
    print("\n🌐 注册远程 MCP Server...")
    mcp_client = MockMCPClient("web_service")
    registry.register_mcp_server(mcp_client)
    
    # 4. 显示所有可用函数
    print("\n📋 所有可用函数:")
    functions = registry.list_all_functions()
    for name, info in functions.items():
        print(f"  • {name} ({info['type']}): {info['description']}")
    
    # 5. 创建 AI 调用器
    ai_caller = AIFunctionCaller(registry)
    
    # 6. 模拟各种用户请求
    print("\n🎯 模拟用户请求和 AI 响应:")
    
    test_requests = [
        "帮我计算一个数学表达式",
        "格式化一段文本",
        "获取网页内容",
        "分析文本情感"
    ]
    
    for request in test_requests:
        result = await ai_caller.simulate_ai_call(request)
        print(f"   结果: {result}")
    
    # 7. 性能对比
    performance = PerformanceComparison(registry)
    await performance.compare_performance()
    
    # 8. 显示统计信息
    print("\n📈 调用统计:")
    stats = registry.get_stats()
    print(f"  本地调用次数: {stats['local_calls']}")
    print(f"  远程调用次数: {stats['remote_calls']}")
    print(f"  总计耗时: {stats['total_time']:.3f}秒")
    
    # 9. 展示混合架构的优势
    print("\n✨ 混合架构的优势:")
    print("  1. 统一接口: 无论本地还是远程函数，调用方式一致")
    print("  2. 性能优化: 高频功能用本地，重型计算用远程")
    print("  3. 灵活扩展: 可以随时添加新的 Plugin 或 MCP Server")
    print("  4. 透明切换: AI 无需关心函数是本地还是远程")

if __name__ == "__main__":
    asyncio.run(main())
