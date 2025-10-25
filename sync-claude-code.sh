#!/bin/bash
# Claude가 작성한 코드를 현재 디렉토리로 복사하는 스크립트

CLAUDE_DIR="/home/claude/automation-platform"
CURRENT_DIR="$PWD"

echo "📥 Claude의 코드를 가져오는 중..."

# 특정 파일/디렉토리만 복사 (venv, cache 제외)
rsync -av --exclude='venv' --exclude='__pycache__' --exclude='*.pyc' \
    --exclude='*.log' --exclude='*.db' \
    "$CLAUDE_DIR/" "$CURRENT_DIR/"

echo "✅ 동기화 완료!"
echo ""
echo "변경사항:"
git status -s

echo ""
read -p "Git에 커밋하시겠습니까? (y/n): " answer
if [[ "$answer" == "y" ]]; then
    read -p "커밋 메시지: " msg
    git add .
    git commit -m "$msg"
    git push
    echo "✅ GitHub에 업로드 완료!"
fi
