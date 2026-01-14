# 部署指令

## 本地开发

```bash
# 启动本地服务器
npx -y serve . -l 3000

# 访问
http://localhost:3000
```

## 生产部署

### 静态托管

本项目是纯静态站点，可部署到以下平台:

1. **GitHub Pages**
   ```bash
   git add .
   git commit -m "deploy"
   git push origin main
   ```
   然后在 GitHub 仓库设置中启用 Pages

2. **Vercel**
   ```bash
   npx vercel
   ```

3. **Netlify**
   直接拖拽文件夹到 Netlify

### 环境变量

本项目无需环境变量，所有配置在代码中。

## 构建检查清单

- [ ] 检查 `js/data.js` 中的主题数据完整性
- [ ] 确认 `css/style.css` 中的主题色设置
- [ ] 测试所有页面的功能
- [ ] 清除 localStorage 测试首次使用流程
- [ ] 检查移动端响应式布局
