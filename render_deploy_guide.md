# Render 部署指南

## 1. 准备工作
确保您的 GitHub 仓库包含：
- ✅ `app.py` (FastAPI 应用)
- ✅ `MixedModelDOE_Function_FollowOriginal_20250804.py` (修复版本)
- ✅ `requirements.txt` (依赖包列表)

## 2. 创建 Web Service

### 在 Render Dashboard:
1. 点击 "New +" → "Web Service"
2. 连接您的 GitHub 仓库: `MixedModelDOE_V1`
3. 配置设置：
   - **Name**: `mixedmodel-doe-api`
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn app:app --host 0.0.0.0 --port $PORT`
   - **Instance Type**: `Free` (或选择付费套餐避免 sleep)

## 3. 环境变量 (如果需要)
在 "Environment" 标签页添加：
- 无特殊环境变量需求

## 4. 部署
- 点击 "Create Web Service"
- 等待构建和部署完成
- 获取服务 URL: `https://your-service-name.onrender.com`

## 5. 测试 API
部署完成后测试：
- GET: `https://your-service-name.onrender.com/runDOE`
- POST: `https://your-service-name.onrender.com/runDOE` (上传 CSV 文件)

## 6. 避免 Sleep (可选)
- 升级到付费套餐 ($7/月)
- 或使用 cron job 定期 ping 服务保持活跃
