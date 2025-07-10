#!/usr/bin/env python3
"""
演示 Semantic Kernel Plugin 与 MCP Server 的相似性和集成方式
"""

import asyncio
import json
from typing import Annotated, Dict, Any, List
from semantic_kernel.functions import kernel_function


# ========================================
# 1. 传统的 Semantic Kernel Plugin
# ========================================

class TraditionalPlugin:
    """传统的 Semantic Kernel Plugin"""
    
    @kernel_function(
        name="calculate",
        description="Perform basic mathematical calculations"
    )
    def calculate(
        self,
        expression: Annotated[str, "Mathematical expression like '2 + 3'"],
        operation: Annotated[str, "Operation type: add, subtract, multiply, divide"] = "add"
    ) -> Annotated[str, "Calculation result"]:
        """执行数学计算"""
        try:
            if operation == "add" and "+" in expression:
                parts = expression.split("+")
                result = sum(float(p.strip()) for p in parts)
            elif operation == "subtract" and "-" in expression:
                parts = expression.split("-")
                result = float(parts[0].strip()) - float(parts[1].strip())
            elif operation == "multiply" and "*" in expression:
                parts = expression.split("*")
                result = float(parts[0].strip()) * float(parts[1].strip())
            elif operation == "divide" and "/" in expression:
                parts = expression.split("/")
                result = float(parts[0].strip()) / float(parts[1].strip())
            else:
                result = eval(expression)  # 简单示例，生产环境需要安全处理
            
            return f"Result: {result}"
        except Exception as e:
            return f"Error: {str(e)}"


# ========================================
# 2. MCP Server 风格的工具定义
# ========================================

class MCPStyleTool:
    """MCP 风格的工具定义"""
    
    def __init__(self, name: str, description: str, input_schema: Dict[str, Any]):
        self.name = name
        self.description = description
        self.input_schema = input_schema
    
    async def execute(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """执行工具 - 需要子类实现"""
        raise NotImplementedError


class CalculatorMCPTool(MCPStyleTool):
    """MCP 风格的计算器工具"""
    
    def __init__(self):
        super().__init__(
            name="calculator",
            description="Perform mathematical calculations",
            input_schema={
                "type": "object",
                "properties": {
                    "expression": {
                        "type": "string",
                        "description": "Mathematical expression to evaluate"
                    },
                    "operation": {
                        "type": "string",
                        "description": "Type of operation",
                        "enum": ["add", "subtract", "multiply", "divide", "auto"]
                    }
                },
                "required": ["expression"]
            }
        )
    
    async def execute(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """执行计算"""
        try:
            expression = arguments.get("expression", "")
            operation = arguments.get("operation", "auto")
            
            if operation == "auto":
                result = eval(expression)  # 简单示例
            else:
                # 与 TraditionalPlugin 相同的逻辑
                if operation == "add" and "+" in expression:
                    parts = expression.split("+")
                    result = sum(float(p.strip()) for p in parts)
                # ... 其他操作逻辑
                else:
                    result = eval(expression)
            
            return {
                "type": "text",
                "content": f"Calculation result: {result}",
                "metadata": {
                    "expression": expression,
                    "operation": operation,
                    "result": result
                }
            }
        except Exception as e:
            return {
                "type": "error",
                "content": f"Calculation failed: {str(e)}",
                "metadata": {"error": str(e)}
            }


class FileOperationMCPTool(MCPStyleTool):
    """MCP 风格的文件操作工具"""
    
    def __init__(self):
        super().__init__(
            name="file_operations",
            description="Perform file operations like read, write, list",
            input_schema={
                "type": "object",
                "properties": {
                    "operation": {
                        "type": "string",
                        "enum": ["read", "write", "list", "delete"]
                    },
                    "file_path": {
                        "type": "string",
                        "description": "Path to the file"
                    },
                    "content": {
                        "type": "string",
                        "description": "Content to write (for write operation)"
                    }
                },
                "required": ["operation"]
            }
        )
    
    async def execute(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """执行文件操作"""
        try:
            operation = arguments.get("operation")
            file_path = arguments.get("file_path", "")
            content = arguments.get("content", "")
            
            if operation == "read":
                with open(file_path, 'r', encoding='utf-8') as f:
                    file_content = f.read()
                return {
                    "type": "text",
                    "content": f"File content:\n{file_content}",
                    "metadata": {"file_path": file_path, "size": len(file_content)}
                }
            
            elif operation == "write":
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                return {
                    "type": "text",
                    "content": f"Successfully wrote to {file_path}",
                    "metadata": {"file_path": file_path, "bytes_written": len(content)}
                }
            
            elif operation == "list":
                import os
                directory = file_path or "."
                files = os.listdir(directory)
                return {
                    "type": "text",
                    "content": f"Files in {directory}:\n" + "\n".join(files),
                    "metadata": {"directory": directory, "file_count": len(files)}
                }
            
            else:
                return {
                    "type": "error",
                    "content": f"Unknown operation: {operation}",
                    "metadata": {"error": f"Unsupported operation: {operation}"}
                }
                
        except Exception as e:
            return {
                "type": "error",
                "content": f"File operation failed: {str(e)}",
                "metadata": {"error": str(e)}
            }


# ========================================
# 3. MCP 服务器模拟器
# ========================================

class MCPServerSimulator:
    """MCP 服务器模拟器"""
    
    def __init__(self):
        self.tools: Dict[str, MCPStyleTool] = {}
        self.register_default_tools()
    
    def register_default_tools(self):
        """注册默认工具"""
        self.register_tool(CalculatorMCPTool())
        self.register_tool(FileOperationMCPTool())
    
    def register_tool(self, tool: MCPStyleTool):
        """注册工具"""
        self.tools[tool.name] = tool
        print(f"📝 已注册 MCP 工具: {tool.name}")
    
    def list_tools(self) -> List[Dict[str, Any]]:
        """列出所有可用工具"""
        return [
            {
                "name": tool.name,
                "description": tool.description,
                "inputSchema": tool.input_schema
            }
            for tool in self.tools.values()
        ]
    
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """调用指定工具"""
        if tool_name not in self.tools:
            return {
                "type": "error",
                "content": f"Tool '{tool_name}' not found",
                "metadata": {"available_tools": list(self.tools.keys())}
            }
        
        tool = self.tools[tool_name]
        print(f"🔧 调用 MCP 工具: {tool_name} with args: {arguments}")
        
        result = await tool.execute(arguments)
        return result


# ========================================
# 4. MCP 集成插件 (桥接器)
# ========================================

class MCPIntegrationPlugin:
    """将 MCP 服务器集成到 Semantic Kernel 的插件"""
    
    def __init__(self, mcp_server: MCPServerSimulator):
        self.mcp_server = mcp_server
        print("🌉 MCP 集成插件已初始化")
    
    @kernel_function(
        name="call_mcp_tool",
        description="Call an external MCP tool"
    )
    async def call_mcp_tool(
        self,
        tool_name: Annotated[str, "Name of the MCP tool to call"],
        arguments: Annotated[str, "JSON string of arguments to pass to the tool"]
    ) -> Annotated[str, "Result from the MCP tool"]:
        """调用 MCP 工具"""
        try:
            # 解析参数
            args = json.loads(arguments)
            
            # 调用 MCP 服务器
            result = await self.mcp_server.call_tool(tool_name, args)
            
            # 格式化返回结果
            if result["type"] == "error":
                return f"❌ MCP Tool Error: {result['content']}"
            else:
                return f"✅ MCP Tool Result: {result['content']}"
                
        except json.JSONDecodeError:
            return "❌ Invalid JSON arguments"
        except Exception as e:
            return f"❌ MCP Integration Error: {str(e)}"
    
    @kernel_function(
        name="list_mcp_tools",
        description="List all available MCP tools"
    )
    def list_mcp_tools(self) -> Annotated[str, "List of available MCP tools"]:
        """列出所有可用的 MCP 工具"""
        tools = self.mcp_server.list_tools()
        
        result = "Available MCP Tools:\n"
        for tool in tools:
            result += f"\n🔧 {tool['name']}: {tool['description']}\n"
            result += f"   Schema: {json.dumps(tool['inputSchema'], indent=2)}\n"
        
        return result


# ========================================
# 5. 混合 Agent 演示
# ========================================

class HybridAgent:
    """混合了传统插件和 MCP 集成的 Agent"""
    
    def __init__(self):
        # 创建 MCP 服务器
        self.mcp_server = MCPServerSimulator()
        
        # 创建插件
        self.traditional_plugin = TraditionalPlugin()
        self.mcp_integration_plugin = MCPIntegrationPlugin(self.mcp_server)
        
        print("🤖 混合 Agent 已初始化")
    
    async def process_request(self, request: str) -> str:
        """处理用户请求"""
        print(f"\n📥 处理请求: {request}")
        
        # 简单的路由逻辑
        if "list tools" in request.lower():
            return self.mcp_integration_plugin.list_mcp_tools()
        
        elif "calculate" in request.lower() or "math" in request.lower():
            # 可以选择使用传统插件或 MCP 工具
            if "mcp" in request.lower():
                # 使用 MCP 工具
                args = json.dumps({"expression": "2 + 3", "operation": "add"})
                return await self.mcp_integration_plugin.call_mcp_tool("calculator", args)
            else:
                # 使用传统插件
                return self.traditional_plugin.calculate("2 + 3", "add")
        
        elif "file" in request.lower():
            # 使用 MCP 文件操作工具
            args = json.dumps({"operation": "list", "file_path": "."})
            return await self.mcp_integration_plugin.call_mcp_tool("file_operations", args)
        
        else:
            return "Sorry, I don't understand that request."


# ========================================
# 6. 演示程序
# ========================================

async def demonstrate_hybrid_approach():
    """演示混合方法"""
    print("🚀 Semantic Kernel Plugin 与 MCP Server 集成演示")
    print("=" * 70)
    
    # 创建混合 Agent
    agent = HybridAgent()
    
    # 测试请求
    test_requests = [
        "List available tools",
        "Calculate 5 + 10 using traditional plugin",
        "Calculate 5 * 10 using MCP tool", 
        "List files in current directory"
    ]
    
    for request in test_requests:
        result = await agent.process_request(request)
        print(f"📤 结果: {result}")
        print("-" * 50)
    
    print("\n🎯 总结:")
    print("1. 传统插件：直接集成，高性能，应用内部使用")
    print("2. MCP 集成：标准化接口，跨应用复用，独立维护")
    print("3. 混合方式：结合两者优势，灵活选择适合的工具")


async def compare_performance():
    """性能对比"""
    print("\n⚡ 性能对比测试")
    print("=" * 30)
    
    import time
    
    agent = HybridAgent()
    
    # 测试传统插件性能
    start = time.time()
    result1 = agent.traditional_plugin.calculate("100 + 200", "add")
    traditional_time = time.time() - start
    
    # 测试 MCP 工具性能
    start = time.time()
    args = json.dumps({"expression": "100 + 200", "operation": "add"})
    result2 = await agent.mcp_integration_plugin.call_mcp_tool("calculator", args)
    mcp_time = time.time() - start
    
    print(f"🏃 传统插件: {traditional_time*1000:.2f}ms - {result1}")
    print(f"🌐 MCP 工具: {mcp_time*1000:.2f}ms - {result2}")
    print(f"📊 性能差异: {(mcp_time/traditional_time):.1f}x")


if __name__ == "__main__":
    asyncio.run(demonstrate_hybrid_approach())
    asyncio.run(compare_performance())
