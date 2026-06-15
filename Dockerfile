# ================================================================
# 百工 — 多场景 AI 面试模拟平台 Docker 镜像
# ================================================================

FROM python:3.11-slim

LABEL maintainer="zhousirui0714"
LABEL description="AI Interview Simulation Platform"

# 设置工作目录
WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libc6-dev \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt .

# 安装 Python 依赖
RUN pip install --no-cache-dir -r requirements.txt \
    && pip install --no-cache-dir gunicorn gevent

# 复制项目代码
COPY . .

# 创建数据目录（SQLite 持久化）
RUN mkdir -p /app/data

# 暴露端口
EXPOSE 5000

# 健康检查
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:5000/api/health')" || exit 1

# 默认使用 gunicorn 生产服务器
CMD ["gunicorn", "--worker-class", "gevent", "--workers", "2", \
     "--bind", "0.0.0.0:5000", "--timeout", "120", \
     "--log-level", "info", "wsgi:app"]
