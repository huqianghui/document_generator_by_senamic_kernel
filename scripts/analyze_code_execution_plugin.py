#!/usr/bin/env python3
"""
CodeExecutionPlugin 转换机制实际演示

展示项目中实际的 CodeExecutionPlugin 如何转换为 Function Call Definition
"""

import json
import inspect
from typing import get_type_hints, get_origin, get_args
from plugins.code_execution_plugin import CodeExecutionPlugin


def analyze_kernel_function(plugin_class, method_name):
    """分析 KernelFunction 的详细信息"""
    print(f"🔍 分析 {plugin_class.__name__}.{method_name}")
    print("-" * 60)
    
    method = getattr(plugin_class, method_name)
    
    # 1. 检查是否为 kernel_function
    if hasattr(method, '__kernel_function__'):
        kernel_func_info = method.__kernel_function__
        print(f"✅ 确认为 KernelFunction")
        print(f"📝 Description: {kernel_func_info.get('description', 'No description')}")
    else:
        print(f"❌ 不是 KernelFunction")
        return None
    
    # 2. 分析函数签名
    sig = inspect.signature(method)
    print(f"📋 函数签名: {sig}")
    
    # 3. 分析参数
    params_info = {}
    for param_name, param in sig.parameters.items():
        if param_name == 'self':
            continue
        
        param_info = {
            "name": param_name,
            "annotation": str(param.annotation),
            "default": str(param.default) if param.default != inspect.Parameter.empty else "Required",
            "type_hint": None,
            "description": None
        }
        
        # 处理 Annotated 类型
        if hasattr(param.annotation, '__origin__') and param.annotation.__origin__ is not None:
            try:
                from typing import get_origin, get_args
                if get_origin(param.annotation) is not None:
                    args = get_args(param.annotation)
                    if len(args) >= 2:
                        param_info["type_hint"] = str(args[0])
                        param_info["description"] = args[1]
            except:
                pass
        
        params_info[param_name] = param_info
        print(f"  📌 参数 {param_name}:")
        print(f"     🏷️  类型: {param_info['type_hint'] or param_info['annotation']}")
        print(f"     📝 描述: {param_info['description'] or 'No description'}")
        print(f"     🔧 默认值: {param_info['default']}")
    
    # 4. 分析返回类型
    return_annotation = sig.return_annotation
    return_info = {
        "annotation": str(return_annotation),
        "type_hint": None,
        "description": None
    }
    
    if hasattr(return_annotation, '__origin__') and return_annotation.__origin__ is not None:
        try:
            from typing import get_origin, get_args
            if get_origin(return_annotation) is not None:
                args = get_args(return_annotation)
                if len(args) >= 2:
                    return_info["type_hint"] = str(args[0])
                    return_info["description"] = args[1]
        except:
            pass
    
    print(f"🔄 返回类型:")
    print(f"   🏷️  类型: {return_info['type_hint'] or return_info['annotation']}")
    print(f"   📝 描述: {return_info['description'] or 'No description'}")
    
    return {
        "method_name": method_name,
        "kernel_function_info": kernel_func_info,
        "parameters": params_info,
        "return_info": return_info
    }


def convert_to_openai_schema(plugin_name, function_info):
    """将 KernelFunction 转换为 OpenAI Function Call Schema"""
    if not function_info:
        return None
    
    schema = {
        "name": f"{plugin_name}_{function_info['method_name']}",
        "description": function_info['kernel_function_info'].get('description', ''),
        "parameters": {
            "type": "object",
            "properties": {},
            "required": []
        }
    }
    
    # 转换参数
    for param_name, param_info in function_info['parameters'].items():
        # 确定 JSON Schema 类型
        json_type = "string"  # 默认
        if param_info['type_hint']:
            if 'str' in param_info['type_hint']:
                json_type = "string"
            elif 'int' in param_info['type_hint']:
                json_type = "integer"
            elif 'float' in param_info['type_hint']:
                json_type = "number"
            elif 'bool' in param_info['type_hint']:
                json_type = "boolean"
        
        schema["parameters"]["properties"][param_name] = {
            "type": json_type,
            "description": param_info['description'] or f"Parameter {param_name}"
        }
        
        # 检查是否为必需参数
        if param_info['default'] == "Required":
            schema["parameters"]["required"].append(param_name)
    
    return schema


def main():
    """主函数"""
    print("🚀 CodeExecutionPlugin 转换机制实际演示")
    print("=" * 80)
    
    # 1. 分析 CodeExecutionPlugin
    print(f"\n📦 分析插件: CodeExecutionPlugin")
    print("=" * 50)
    
    plugin_class = CodeExecutionPlugin
    
    # 查找所有的 kernel_function
    kernel_functions = []
    for attr_name in dir(plugin_class):
        if not attr_name.startswith('_'):  # 跳过私有方法
            attr = getattr(plugin_class, attr_name)
            if callable(attr) and hasattr(attr, '__kernel_function__'):
                kernel_functions.append(attr_name)
    
    print(f"🔍 发现的 KernelFunction: {kernel_functions}")
    
    # 2. 详细分析每个函数
    all_schemas = []
    for func_name in kernel_functions:
        print(f"\n" + "="*60)
        function_info = analyze_kernel_function(plugin_class, func_name)
        
        if function_info:
            # 转换为 OpenAI Schema
            schema = convert_to_openai_schema("CodeExecutionPlugin", function_info)
            all_schemas.append(schema)
    
    # 3. 显示最终的 Function Call Definitions
    print(f"\n🔄 转换后的 Function Call Definitions")
    print("=" * 80)
    
    for i, schema in enumerate(all_schemas, 1):
        print(f"\n📋 Function {i}:")
        print(json.dumps(schema, indent=2, ensure_ascii=False))
    
    # 4. 模拟实际的 API 调用格式
    print(f"\n🌐 模拟发送给大模型的完整请求")
    print("=" * 80)
    
    api_request = {
        "model": "gpt-4",
        "messages": [
            {
                "role": "system",
                "content": "You are a helpful assistant that can execute Python code to help users solve problems."
            },
            {
                "role": "user",
                "content": "Please calculate the factorial of 5 using Python code."
            }
        ],
        "functions": all_schemas,
        "function_call": "auto"
    }
    
    print(json.dumps(api_request, indent=2, ensure_ascii=False))
    
    # 5. 模拟大模型的响应
    print(f"\n🤖 模拟大模型的响应")
    print("=" * 80)
    
    model_response = {
        "id": "chatcmpl-123",
        "object": "chat.completion",
        "created": 1677652288,
        "choices": [
            {
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": None,
                    "function_call": {
                        "name": "CodeExecutionPlugin_run",
                        "arguments": json.dumps({
                            "code": "import math\n\ndef factorial(n):\n    return math.factorial(n)\n\nresult = factorial(5)\nprint(f'The factorial of 5 is: {result}')\nresult"
                        })
                    }
                },
                "finish_reason": "function_call"
            }
        ]
    }
    
    print(json.dumps(model_response, indent=2, ensure_ascii=False))
    
    # 6. 解释整个流程
    print(f"\n📚 流程总结")
    print("=" * 80)
    print("1. 📦 CodeExecutionPlugin 包含用 @kernel_function 装饰的方法")
    print("2. 🔄 Semantic Kernel 自动将这些方法转换为 Function Call Definitions")
    print("3. 📡 转换后的定义随用户消息一起发送给大模型")
    print("4. 🤖 大模型根据用户意图选择合适的函数并生成调用参数")
    print("5. ⚡ Semantic Kernel 接收函数调用请求并执行对应的 Python 方法")
    print("6. 📝 执行结果返回给大模型，大模型生成最终回复")
    
    print(f"\n🎯 关键理解:")
    print("   • Plugin = 一组 Function Call Definitions")
    print("   • @kernel_function = 单个 Function Definition")
    print("   • 大模型负责选择，Semantic Kernel 负责执行")
    print("   • 整个过程对开发者透明，只需专注于业务逻辑实现")


if __name__ == "__main__":
    main()
