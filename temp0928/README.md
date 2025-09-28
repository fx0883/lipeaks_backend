# 客户端许可证激活与集成文档

## 文档概述

本文档详细说明了客户端软件如何与许可证服务器进行交互，包括许可证激活、验证、心跳检测等完整流程。

## 文档结构

- [README.md](./README.md) - 本文档，提供概述和导航
- [integration_guide.md](./integration_guide.md) - 完整集成指南和流程说明
- [api_reference.md](./api_reference.md) - 详细的API参考文档
- [activation_scenarios.md](./activation_scenarios.md) - 各种激活场景和处理方式
- [error_handling.md](./error_handling.md) - 错误处理指南和故障排除

## 快速开始

### 1. 基本激活流程

```
客户端启动 → 检查本地激活状态 → 如果未激活，提示输入许可证密钥 → 调用激活API → 保存激活信息 → 正常使用
```

### 2. 关键API端点

- `GET /api/v1/licenses/info/<license_key>/` - 获取许可证信息
- `POST /api/v1/licenses/activate/` - 激活许可证
- `POST /api/v1/licenses/verify/` - 验证激活状态
- `POST /api/v1/licenses/heartbeat/` - 发送心跳检测

### 3. 必需的HTTP Header

所有API调用都需要包含以下Header：

```
Content-Type: application/json
X-Tenant-ID: <租户ID>
```

## 重要提示

1. **租户隔离**：所有API调用必须在Header中包含`X-Tenant-ID`
2. **频率限制**：激活API有频率限制（每小时10次）
3. **安全性**：硬件指纹用于防止许可证滥用
4. **心跳机制**：激活的软件应定期发送心跳检测

## 开发建议

1. 首先阅读[完整集成指南](./integration_guide.md)了解整体流程
2. 参考[API参考文档](./api_reference.md)了解具体参数
3. 根据你的应用场景查看[激活场景文档](./activation_scenarios.md)
4. 实现完整的[错误处理机制](./error_handling.md)

## 联系支持

如有技术问题，请参考各个文档中的故障排除部分，或联系技术支持团队。

---

**版本**: v1.0  
**更新时间**: 2025年9月28日  
**适用范围**: 所有客户端软件集成
