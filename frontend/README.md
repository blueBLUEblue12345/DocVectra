# DocVectra Frontend

基于 Vue 3 + Vite 的前端应用，参考 DeepSeek Chat 设计风格。

## 技术栈

- **Vue 3** - 渐进式 JavaScript 框架
- **Vite** - 下一代前端构建工具
- **Pinia** - Vue 状态管理库
- **Vue Router** - 官方路由管理器
- **Axios** - HTTP 客户端
- **Marked** - Markdown 解析器

## 项目结构

```
frontend/
├── src/
│   ├── components/       # 可复用组件
│   │   └── Sidebar.vue   # 侧边栏组件
│   ├── views/           # 页面视图
│   │   ├── ChatView.vue    # 智能问答页面
│   │   └── ImportView.vue  # 文档导入页面
│   ├── stores/          # Pinia 状态管理
│   │   └── chatStore.js    # 聊天状态
│   ├── services/        # API 服务
│   │   └── api.js          # API 接口封装
│   ├── styles/          # 全局样式
│   │   └── global.css      # 全局 CSS 变量和样式
│   ├── router/          # 路由配置
│   │   └── index.js
│   ├── App.vue          # 根组件
│   └── main.js          # 入口文件
├── index.html           # HTML 模板
├── package.json         # 依赖配置
└── vite.config.js       # Vite 配置
```

## 功能特性

### 智能问答
- 流式响应，实时显示 AI 回答
- Markdown 渲染，支持代码高亮
- 会话历史管理
- 新建/切换/删除会话

### 文档导入
- 拖拽上传文件
- 支持 PDF、Markdown 格式
- 实时显示上传进度
- 任务状态跟踪

## 安装和运行

### 安装依赖

```bash
cd frontend
npm install
```

### 开发模式

```bash
npm run dev
```

访问 http://localhost:3000

### 构建生产版本

```bash
npm run build
```

构建产物在 `dist/` 目录。

### 预览生产版本

```bash
npm run preview
```

## 环境变量

前端通过 Vite 代理与后端通信，配置在 `vite.config.js`：

- API 代理：`/api` → `http://localhost:8000`
- WebSocket 代理：`/ws` → `ws://localhost:8000`

确保后端服务运行在 8000 端口。

## 后端集成

前端需要后端提供以下 API：

### 查询相关
- `POST /api/query/query` - 发送查询
- `GET /api/query/stream/{session_id}` - 流式查询（SSE）
- `GET /api/query/history/{session_id}` - 获取历史记录
- `DELETE /api/query/history/{session_id}` - 清除历史

### 导入相关
- `POST /api/import/upload` - 上传文件
- `GET /api/import/status/{task_id}` - 查询任务状态

## 开发指南

### 添加新页面

1. 在 `src/views/` 创建新视图组件
2. 在 `src/router/index.js` 添加路由

### 添加新状态

在 `src/stores/` 创建新的 Pinia store：

```javascript
import { defineStore } from 'pinia'

export const useMyStore = defineStore('myStore', () => {
  // 状态逻辑
})
```

### 添加新 API

在 `src/services/api.js` 添加新的 API 方法。

## 样式规范

- 使用 CSS 变量定义主题色
- 遵循 DeepSeek Chat 的简洁设计风格
- 响应式布局，支持移动端

主要颜色变量：
- `--primary-color`: 主色调 #4f46e5
- `--text-primary`: 主文本 #1f2937
- `--bg-primary`: 主背景 #ffffff
- `--border-color`: 边框色 #e5e7eb

## 注意事项

1. 确保后端 CORS 配置允许前端访问
2. 流式响应使用 SSE（Server-Sent Events）
3. 文件上传使用 FormData
4. 会话 ID 使用 UUID 生成
