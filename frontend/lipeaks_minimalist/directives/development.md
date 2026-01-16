# 21天自律打卡 APP 开发指令

> 此项目的核心指令文档

## 项目概述

这是一个21天自律打卡 Web APP，采用前端纯静态方案实现。

## 技术栈

- **前端**: HTML5 + CSS3 + Vanilla JavaScript
- **存储**: localStorage 本地存储
- **部署**: 静态文件服务器 (serve)

## 目录结构

```
lipeaks_minimalist/
├── index.html          # 主入口
├── css/
│   └── style.css       # 设计系统 + 样式
├── js/
│   ├── data.js         # 21个主题数据
│   └── app.js          # SPA 应用逻辑
├── docs/
│   ├── prd.md          # PRD文档
│   └── ui-design.md    # UI设计文档
├── directives/         # 指令文档
├── execution/          # Python 执行脚本
└── .tmp/               # 临时文件
```

## 开发指令

### 1. 启动开发服务器

```bash
npx -y serve . -l 3000
```

### 2. 添加新主题

1. 编辑 `js/data.js` 中的 `THEMES` 数组
2. 添加新主题的 id, name, icon, color, goal, content, tip, quote
3. 如果需要特殊表单，在 `js/app.js` 的 `renderCheckin()` 中添加 case

### 3. 修改主题色

编辑 `css/style.css` 中的 `:root` 变量:
- `--primary-start`: 主渐变起始色
- `--primary-end`: 主渐变结束色

### 4. 数据持久化

所有数据通过 localStorage 存储:
- `selectedThemes`: 已选主题 ID 数组
- `records`: 打卡记录对象 (key: `${themeId}-${date}`)
- `cycleStartDate`: 周期开始日期

## 边界情况处理

1. **首次使用**: 显示欢迎页和主题选择流程
2. **周期结束**: 21天后可在个人中心重置周期
3. **离线使用**: localStorage 支持离线访问
4. **数据丢失**: 清空 localStorage 会重置所有数据
