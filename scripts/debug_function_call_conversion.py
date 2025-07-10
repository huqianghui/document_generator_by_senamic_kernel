#!/usr/bin/env python3
"""
Semantic Kernel Plugin 与 Function Call 转换机制演示

此脚本展示了 Plugin 中的 KernelFunction 如何转换为大模型可理解的 Function Call Definitions，
以及大模型如何选择和调用这些函数。
"""

import json
import asyncio
from typing import Annotated, Dict, Any, List
from semantic_kernel.functions import kernel_function
from semantic_kernel.contents.chat_message_content import ChatMessageContent
from semantic_kernel.contents.utils.author_role import AuthorRole


class DebugPlugin:
    """用于演示的调试插件"""
    
    @kernel_function(
        name="calculate_math",
        description="Perform basic mathematical calculations like addition, subtraction, multiplication, division"
    )
    async def calculate_math(
        self,
        expression: Annotated[str, "Mathematical expression to calculate (e.g., '2 + 3', '10 / 2')"],
        operation: Annotated[str, "Type of operation: add, subtract, multiply, divide"] = "add"
    ) -> Annotated[str, "Result of the mathematical calculation"]:
        """执行基本的数学计算"""
        try:
            # 简单的数学表达式解析
            if operation == "add":
                parts = expression.split('+')
                if len(parts) == 2:
                    result = float(parts[0].strip()) + float(parts[1].strip())
                    return f"Result: {result}"
            elif operation == "subtract":
                parts = expression.split('-')
                if len(parts) == 2:
                    result = float(parts[0].strip()) - float(parts[1].strip())
                    return f"Result: {result}"
            elif operation == "multiply":
                parts = expression.split('*')
                if len(parts) == 2:
                    result = float(parts[0].strip()) * float(parts[1].strip())
                    return f"Result: {result}"
            elif operation == "divide":
                parts = expression.split('/')
                if len(parts) == 2:
                    denominator = float(parts[1].strip())
                    if denominator != 0:
                        result = float(parts[0].strip()) / denominator
                        return f"Result: {result}"
                    else:
                        return "Error: Division by zero"
            
            # 使用 eval 作为后备方案（在生产环境中应谨慎使用）
            result = eval(expression)
            return f"Result: {result}"
        except Exception as e:
            return f"Error: {str(e)}"
    
    @kernel_function(
        name="format_text",
        description="Format text in various ways like uppercase, lowercase, title case, or reverse"
    )
    async def format_text(
        self,
        text: Annotated[str, "Text to format"],
        format_type: Annotated[str, "Format type: upper, lower, title, reverse"] = "upper"
    ) -> Annotated[str, "Formatted text"]:
        """格式化文本"""
        try:
            if format_type == "upper":
                return text.upper()
            elif format_type == "lower":
                return text.lower()
            elif format_type == "title":
                return text.title()
            elif format_type == "reverse":
                return text[::-1]
            else:
                return f"Unknown format type: {format_type}"
        except Exception as e:
            return f"Error: {str(e)}"
    
    @kernel_function(
        name="generate_list",
        description="Generate a list of items based on specified criteria"
    )
    async def generate_list(
        self,
        list_type: Annotated[str, "Type of list to generate: numbers, letters, words"],
        count: Annotated[int, "Number of items to generate"] = 5
    ) -> Annotated[str, "Generated list"]:
        """生成列表"""
        try:
            if list_type == "numbers":
                return str(list(range(1, count + 1)))
            elif list_type == "letters":
                import string
                return str(list(string.ascii_lowercase[:count]))
            elif list_type == "words":
                sample_words = ["apple", "banana", "cherry", "date", "elderberry", "fig", "grape"]
                return str(sample_words[:count])
            else:
                return f"Unknown list type: {list_type}"
        except Exception as e:
            return f"Error: {str(e)}"


class FunctionCallDebugger:
    """函数调用调试器 - 展示转换过程"""
    
    def __init__(self, plugin: Any):
        self.plugin = plugin
        self.function_schemas = []
        self._analyze_plugin()
    
    def _analyze_plugin(self):
        """分析插件并生成函数定义"""
        print("🔍 分析 Plugin 中的 KernelFunction...")
        
        # 获取插件中的所有方法
        for method_name in dir(self.plugin):
            method = getattr(self.plugin, method_name)
            
            # 检查是否是 kernel_function
            if hasattr(method, '__kernel_function__'):
                print(f"  ✅ 发现 KernelFunction: {method_name}")
                
                # 提取函数信息
                function_info = method.__kernel_function__
                schema = self._convert_to_openai_schema(method_name, function_info, method)
                self.function_schemas.append(schema)
                
                print(f"    📝 函数描述: {function_info.get('description', 'No description')}")
                print(f"    📋 参数信息: {self._get_parameter_info(method)}")
    
    def _get_parameter_info(self, method) -> Dict[str, Any]:
        """获取方法的参数信息"""
        import inspect
        
        sig = inspect.signature(method)
        params = {}
        
        for param_name, param in sig.parameters.items():
            if param_name == 'self':
                continue
                
            param_info = {
                "name": param_name,
                "type": str(param.annotation) if param.annotation != inspect.Parameter.empty else "Any",
                "default": str(param.default) if param.default != inspect.Parameter.empty else "Required"
            }
            params[param_name] = param_info
        
        return params
    
    def _convert_to_openai_schema(self, method_name: str, function_info: Dict, method) -> Dict[str, Any]:
        """将 KernelFunction 转换为 OpenAI Function Call Schema"""
        import inspect
        
        # 基础 schema
        schema = {
            "name": f"DebugPlugin_{method_name}",
            "description": function_info.get('description', ''),
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
        
        # 分析参数
        sig = inspect.signature(method)
        for param_name, param in sig.parameters.items():
            if param_name == 'self':
                continue
            
            # 提取参数类型和描述
            param_type = "string"  # 默认为字符串
            param_description = ""
            
            if hasattr(param.annotation, '__origin__'):
                # 处理 Annotated 类型
                if param.annotation.__origin__ is Annotated:
                    args = param.annotation.__args__
                    if len(args) >= 2:
                        actual_type = args[0]
                        param_description = args[1]
                        
                        # 转换 Python 类型到 JSON Schema 类型
                        if actual_type == int:
                            param_type = "integer"
                        elif actual_type == float:
                            param_type = "number"
                        elif actual_type == bool:
                            param_type = "boolean"
                        elif actual_type == str:
                            param_type = "string"
            
            schema["parameters"]["properties"][param_name] = {
                "type": param_type,
                "description": param_description
            }
            
            # 检查是否为必需参数
            if param.default == inspect.Parameter.empty:
                schema["parameters"]["required"].append(param_name)
        
        return schema
    
    def display_function_schemas(self):
        """显示转换后的函数定义"""
        print("\n🔄 转换后的 Function Call Definitions:")
        print("=" * 80)
        
        for i, schema in enumerate(self.function_schemas, 1):
            print(f"\n📋 Function {i}: {schema['name']}")
            print(f"   📝 Description: {schema['description']}")
            print(f"   📄 Schema:")
            print(json.dumps(schema, indent=4, ensure_ascii=False))
    
    def simulate_model_selection(self, user_query: str) -> Dict[str, Any]:
        """模拟大模型的函数选择过程"""
        print(f"\n🤖 模拟大模型选择函数...")
        print(f"   👤 用户查询: {user_query}")
        print(f"   🎯 可用函数: {[schema['name'] for schema in self.function_schemas]}")
        
        # 简单的关键词匹配逻辑（实际大模型会更复杂）
        selected_function = None
        selected_args = {}
        
        query_lower = user_query.lower()
        
        if any(word in query_lower for word in ['calculate', 'math', 'add', 'subtract', 'multiply', 'divide', '+', '-', '*', '/']):
            selected_function = "DebugPlugin_calculate_math"
            # 提取数学表达式
            if '+' in query_lower:
                selected_args = {"expression": "2 + 3", "operation": "add"}
            elif '-' in query_lower:
                selected_args = {"expression": "10 - 5", "operation": "subtract"}
            elif '*' in query_lower:
                selected_args = {"expression": "4 * 6", "operation": "multiply"}
            elif '/' in query_lower:
                selected_args = {"expression": "20 / 4", "operation": "divide"}
            else:
                selected_args = {"expression": "2 + 3", "operation": "add"}
        
        elif any(word in query_lower for word in ['format', 'upper', 'lower', 'title', 'reverse', 'text']):
            selected_function = "DebugPlugin_format_text"
            if 'upper' in query_lower:
                selected_args = {"text": "hello world", "format_type": "upper"}
            elif 'lower' in query_lower:
                selected_args = {"text": "HELLO WORLD", "format_type": "lower"}
            elif 'title' in query_lower:
                selected_args = {"text": "hello world", "format_type": "title"}
            elif 'reverse' in query_lower:
                selected_args = {"text": "hello", "format_type": "reverse"}
            else:
                selected_args = {"text": "hello world", "format_type": "upper"}
        
        elif any(word in query_lower for word in ['list', 'generate', 'numbers', 'letters', 'words']):
            selected_function = "DebugPlugin_generate_list"
            if 'numbers' in query_lower:
                selected_args = {"list_type": "numbers", "count": 5}
            elif 'letters' in query_lower:
                selected_args = {"list_type": "letters", "count": 5}
            elif 'words' in query_lower:
                selected_args = {"list_type": "words", "count": 5}
            else:
                selected_args = {"list_type": "numbers", "count": 5}
        
        if selected_function:
            print(f"   ✅ 选择的函数: {selected_function}")
            print(f"   📝 函数参数: {json.dumps(selected_args, indent=2)}")
            
            return {
                "function_call": {
                    "name": selected_function,
                    "arguments": json.dumps(selected_args)
                }
            }
        else:
            print(f"   ❌ 没有找到合适的函数")
            return {
                "content": "I don't have a suitable function to handle this request."
            }
    
    async def execute_function_call(self, function_call: Dict[str, Any]) -> str:
        """执行函数调用"""
        print(f"\n⚡ 执行函数调用...")
        
        function_name = function_call["name"]
        function_args = json.loads(function_call["arguments"])
        
        print(f"   🎯 函数名: {function_name}")
        print(f"   📝 参数: {json.dumps(function_args, indent=2)}")
        
        # 解析函数名，提取实际的方法名
        if function_name.startswith("DebugPlugin_"):
            method_name = function_name.replace("DebugPlugin_", "")
            
            if hasattr(self.plugin, method_name):
                method = getattr(self.plugin, method_name)
                try:
                    # 执行函数
                    result = await method(**function_args)
                    print(f"   ✅ 执行成功: {result}")
                    return result
                except Exception as e:
                    error_msg = f"Error executing {method_name}: {str(e)}"
                    print(f"   ❌ 执行失败: {error_msg}")
                    return error_msg
        
        error_msg = f"Function {function_name} not found"
        print(f"   ❌ 函数未找到: {error_msg}")
        return error_msg


async def main():
    """主演示函数"""
    print("🚀 Semantic Kernel Plugin 与 Function Call 转换机制演示")
    print("=" * 80)
    
    # 1. 创建插件实例
    plugin = DebugPlugin()
    
    # 2. 创建调试器
    debugger = FunctionCallDebugger(plugin)
    
    # 3. 显示转换后的函数定义
    debugger.display_function_schemas()
    
    # 4. 模拟不同的用户查询
    test_queries = [
        "Please calculate 2 + 3",
        "Convert 'hello world' to uppercase",
        "Generate a list of 5 numbers",
        "Format text to title case",
        "Divide 20 by 4",
        "Create a list of letters"
    ]
    
    print(f"\n🧪 测试不同的用户查询:")
    print("=" * 80)
    
    for query in test_queries:
        print(f"\n📝 测试查询: {query}")
        print("-" * 40)
        
        # 模拟大模型选择函数
        model_response = debugger.simulate_model_selection(query)
        
        # 如果大模型选择了函数调用，则执行它
        if "function_call" in model_response:
            result = await debugger.execute_function_call(model_response["function_call"])
            print(f"   💬 最终回复: I've executed the function and got: {result}")
        else:
            print(f"   💬 最终回复: {model_response.get('content', 'No response')}")
    
    print(f"\n🎉 演示完成!")
    print("=" * 80)
    print("总结:")
    print("1. Plugin 中的 @kernel_function 被自动转换为 Function Call Definitions")
    print("2. 大模型根据用户查询选择合适的函数")
    print("3. Semantic Kernel 自动执行被选择的函数")
    print("4. 函数执行结果被返回给用户")


if __name__ == "__main__":
    asyncio.run(main())
