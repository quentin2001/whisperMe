# whisperMe Web Frontend

whisperMe 的现代响应式 Web 工作台界面，基于 React 19、Vite 与 Tailwind CSS 构建。

---

## 技术栈 (Tech Stack)

- **框架**: [React 19](https://react.dev/) + [Vite](https://vite.dev/)
- **样式**: [Tailwind CSS](https://tailwindcss.com/)
- **图标**: [Lucide React](https://lucide.dev/)
- **状态管理**: Zustand
- **音频交互**: Web Audio API / Custom Waveform Player
- **国际化 (i18n)**: 中英双语 (Simplified Chinese / English)
- **单元测试**: Vitest

---

## 开发与构建 (Development & Build)

### 安装依赖
```bash
npm install
```

### 启动本地前端开发服务器 (带热重载)
```bash
npm run dev
```
> 开发服务器默认运行于 `http://localhost:5173`，并通过 Vite 代理将 `/api` 与 `/mcp` 请求转发至后端 `http://127.0.0.1:9101`。

### 代码检查与测试
```bash
npm run lint
npm run test
```

### 生产环境打包
```bash
npm run build
```
打包输出目录为 `dist/`，后端静态资源服务会自动托管该目录。
