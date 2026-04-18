#!/bin/bash
# MHH-Causality-Memory 初始化脚本
# 在 OpenClaw 环境下运行

set -e

echo "🔗 初始化 MHH-Causality Memory..."

# 1. 初始化向量数据库
echo "📦 初始化向量数据库..."
cd "$(dirname "$0")/gbrain"
python3 init.py

# 2. 建立 Wiki 四层目录
echo "📁 建立 Wiki 目录..."
WIKI_DIR="$(dirname "$0")/../wiki/main"
mkdir -p "$WIKI_DIR"/{events,timeline,relationships,abstracts}

# 3. 复制模板到 Wiki 层
echo "📋 复制 Wiki 模板..."
TEMPLATE_DIR="$(dirname "$0")/wiki/templates"
for f in "$TEMPLATE_DIR"/*.md; do
  [ -f "$f" ] && cp "$f" "$WIKI_DIR/"
done

echo "✅ 初始化完成！"
echo ""
echo "下一步："
echo "1. 在 OpenClaw 中配置 memory_search 指向 gbrain"
echo "2. 开始使用，记得每次 session 后沉淀事件"
