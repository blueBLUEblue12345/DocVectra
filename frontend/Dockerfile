# 前端多阶段构建 — 构建阶段
FROM node:20-alpine AS build

WORKDIR /app
COPY package.json package-lock.json* ./
RUN npm ci --only=production

COPY . .
RUN npm run build

# 生产阶段 — Nginx 托管静态文件
FROM nginx:1.27-alpine

# 复制构建产物
COPY --from=build /app/dist /usr/share/nginx/html

# 复制 Nginx 配置
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]