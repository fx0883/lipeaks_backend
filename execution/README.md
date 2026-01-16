# Execution 目录

此目录包含确定性的 Python 脚本，用于执行实际操作。

## 设计原则

1. **确定性** - 相同输入产生相同输出
2. **可测试** - 每个脚本都应该可以独立测试
3. **清晰注释** - 代码注释清晰，便于理解
4. **错误处理** - 完善的错误处理和日志记录

## 脚本规范

每个脚本应该：

1. 使用 argparse 处理命令行参数
2. 从 .env 文件读取敏感配置
3. 提供清晰的使用帮助 (`--help`)
4. 返回适当的退出码 (0=成功, 非0=失败)
5. 将日志输出到 stderr，结果输出到 stdout

## 模板

```python
#!/usr/bin/env python
# -*- coding: utf-8 -*-
\"\"\"
脚本描述

使用方法:
    python execution/script_name.py --arg1 value1

作者: [Author]
日期: [Date]
\"\"\"

import argparse
import logging
import sys
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    stream=sys.stderr
)
logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(description='脚本描述')
    parser.add_argument('--arg1', required=True, help='参数1描述')
    args = parser.parse_args()
    
    try:
        # 执行逻辑
        result = process(args.arg1)
        print(result)  # 输出到 stdout
        return 0
    except Exception as e:
        logger.error(f"执行失败: {e}")
        return 1


def process(arg1):
    \"\"\"处理逻辑\"\"\"
    # TODO: 实现
    pass


if __name__ == '__main__':
    sys.exit(main())
```

## 可用脚本

| 脚本 | 描述 |
|------|------|
| (暂无脚本) | |
