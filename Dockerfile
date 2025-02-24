# 使用官方的 Python 作为基础镜像
FROM python:3.11-slim

# 设置工作目录
WORKDIR /app

# 复制 Poetry 的 lock 文件和项目的 pyproject.toml 文件
COPY pyproject.toml poetry.lock /app/

# 安装 Poetry
RUN pip install poetry

# 安装依赖并将虚拟环境设置为项目内
RUN poetry config virtualenvs.in-project true \
    && poetry install --no-root

# 复制 Django 项目代码到容器中
COPY . /app/

# 设置环境变量
ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONPATH=/app

# 暴露 Django 默认的端口
EXPOSE 8000

# 运行 Django 开发服务器（或者 Gunicorn 等）
CMD ["poetry", "run", "python", "manage.py", "runserver", "0.0.0.0:8000"]
