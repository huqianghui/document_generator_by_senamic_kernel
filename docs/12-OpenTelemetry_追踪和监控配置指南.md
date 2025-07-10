# OpenTelemetry 追踪和监控配置指南

## 概述

本文档说明如何在 Semantic Kernel 项目中配置 OpenTelemetry 追踪和 Azure Application Insights 监控，以及如何处理常见的连接和配置问题。

## 问题背景

在使用 OpenTelemetry 与 Azure Application Insights 时，可能会遇到以下问题：

1. **连接超时错误**: `ConnectionError: [SSL: CERTIFICATE_VERIFY_FAILED]`
2. **依赖缺失错误**: Azure Monitor 导出器未安装
3. **网络连接问题**: 无法连接到 Azure Application Insights 端点
4. **配置错误**: 错误的连接字符串或端点配置

## 解决方案

### 1. 错误处理策略

我们的解决方案采用了多级回退机制：

```python
def set_up_tracing():
    """设置追踪配置，包含错误处理和回退机制"""
    try:
        # 尝试设置 Azure Monitor 导出器
        if AZURE_APP_INSIGHTS_CONNECTION_STRING:
            try:
                from opentelemetry.exporter.azure.monitor.trace_exporter import AzureMonitorTraceExporter
                azure_exporter = AzureMonitorTraceExporter(
                    connection_string=AZURE_APP_INSIGHTS_CONNECTION_STRING
                )
                # 配置成功
            except ImportError:
                # 依赖未安装，回退到控制台追踪
                pass
            except Exception as e:
                # 连接失败，回退到控制台追踪
                pass
                
        # 如果 Azure Monitor 失败，使用控制台追踪
        if azure_exporter is None:
            from opentelemetry.exporter.console import ConsoleSpanExporter
            console_exporter = ConsoleSpanExporter()
            # 配置控制台追踪
            
    except Exception as e:
        # 完全失败，继续运行但无追踪
        print(f"❌ 追踪设置失败: {e}")
```

### 2. 依赖安装

#### 基础依赖
```bash
pip install opentelemetry-api opentelemetry-sdk
```

#### Azure Monitor 支持
```bash
pip install opentelemetry-exporter-azure-monitor
```

#### 控制台导出器（用于调试）
```bash
pip install opentelemetry-exporter-console
```

#### 完整安装
```bash
pip install -r requirements-tracing.txt
```

### 3. 配置 Azure Application Insights

#### 获取连接字符串
1. 登录 Azure Portal
2. 创建或选择 Application Insights 资源
3. 在 "概述" 页面复制连接字符串
4. 设置环境变量：
   ```bash
   export AZURE_APP_INSIGHTS_CONNECTION_STRING="InstrumentationKey=your-key;IngestionEndpoint=your-endpoint"
   ```

#### 连接字符串格式
```
InstrumentationKey=12345678-1234-1234-1234-123456789abc;IngestionEndpoint=https://your-region.in.applicationinsights.azure.com/;LiveEndpoint=https://your-region.livediagnostics.monitor.azure.com/
```

### 4. 错误类型和处理

#### SSL 证书验证失败
```
ConnectionError: [SSL: CERTIFICATE_VERIFY_FAILED]
```

**原因**: 网络环境、防火墙或 SSL 配置问题

**解决方案**:
1. 检查网络连接
2. 验证防火墙设置
3. 使用回退到控制台追踪
4. 考虑使用代理或不同的网络环境

#### 导入错误
```
ImportError: No module named 'opentelemetry.exporter.azure.monitor.trace_exporter'
```

**原因**: 缺少 Azure Monitor 导出器包

**解决方案**:
```bash
pip install opentelemetry-exporter-azure-monitor
```

#### 连接超时
```
TimeoutError: Request timed out
```

**原因**: 网络延迟或 Azure 服务暂时不可用

**解决方案**:
1. 增加超时时间
2. 配置重试机制
3. 使用批处理导出器
4. 回退到本地追踪

### 5. 最佳实践

#### 1. 优雅降级
```python
# 总是提供回退选项
try:
    # 尝试云端监控
    setup_azure_monitoring()
except Exception:
    # 回退到本地追踪
    setup_local_tracing()
```

#### 2. 配置验证
```python
# 验证配置是否正确
if not AZURE_APP_INSIGHTS_CONNECTION_STRING:
    print("⚠️ 未配置 Azure Application Insights")
    use_console_tracing()
```

#### 3. 用户友好的错误消息
```python
# 提供清晰的错误信息和解决建议
except ImportError:
    print("⚠️ Azure Monitor 导出器未安装，请运行:")
    print("   pip install opentelemetry-exporter-azure-monitor")
```

#### 4. 性能考虑
```python
# 使用批处理导出器减少网络调用
span_processor = BatchSpanProcessor(
    azure_exporter,
    max_export_batch_size=100,
    export_timeout_millis=30000,
    max_queue_size=2048,
)
```

### 6. 调试技巧

#### 1. 启用详细日志
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

#### 2. 使用控制台导出器进行调试
```python
from opentelemetry.exporter.console import ConsoleSpanExporter
console_exporter = ConsoleSpanExporter()
```

#### 3. 检查连接字符串
```python
if AZURE_APP_INSIGHTS_CONNECTION_STRING:
    print(f"连接字符串: {AZURE_APP_INSIGHTS_CONNECTION_STRING[:50]}...")
```

### 7. 常见问题排查

#### Q: 为什么会出现 SSL 证书验证失败？
A: 通常是网络环境问题，可以：
- 检查系统时间是否正确
- 验证网络连接
- 尝试使用不同的网络环境
- 检查防火墙设置

#### Q: 如何确认 Azure Application Insights 是否正常工作？
A: 可以：
- 在 Azure Portal 中检查 Application Insights 资源
- 查看实时指标流
- 检查追踪数据是否出现在 Azure 中

#### Q: 如何在开发环境中禁用云端追踪？
A: 不设置 `AZURE_APP_INSIGHTS_CONNECTION_STRING` 环境变量，或者设置为空字符串。

### 8. 生产环境建议

1. **监控连接状态**: 定期检查 Azure Application Insights 连接
2. **设置警报**: 在 Azure 中配置追踪数据丢失警报
3. **日志归档**: 保留本地日志作为备份
4. **性能监控**: 监控追踪对应用性能的影响

## 结论

通过实现多级回退机制和充分的错误处理，我们可以确保应用在各种网络和配置环境下都能正常运行。即使无法连接到 Azure Application Insights，应用也会继续正常工作，并提供有用的错误信息帮助诊断问题。

这种方法提高了应用的可靠性和用户体验，特别是在网络环境不稳定或配置不完整的情况下。
