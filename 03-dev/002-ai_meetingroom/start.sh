#!/bin/bash
# 会议室系统启动脚本

echo "====================================="
echo "      AI开发团队会议室系统"
echo "====================================="

# 检查Node.js是否安装
if ! command -v node &> /dev/null; then
    echo "错误: Node.js未安装，请先安装Node.js"
    exit 1
fi

# 检查npm是否安装
if ! command -v npm &> /dev/null; then
    echo "错误: npm未安装，请先安装npm"
    exit 1
fi

# 检查依赖是否安装
if [ ! -d "node_modules" ]; then
    echo "正在安装依赖包..."
    npm install
    if [ $? -ne 0 ]; then
        echo "依赖包安装失败"
        exit 1
    fi
fi

# 检查端口是否被占用
PORT=3000
if netstat -tlnp | grep -q ":$PORT "; then
    echo "错误: 端口 $PORT 已被占用"
    exit 1
fi

# 启动服务器
echo "正在启动会议室系统..."
echo "服务器将运行在 http://localhost:$PORT"
echo "按 Ctrl+C 停止服务"
echo

node index.js