"""
Mixed Model DOE Analysis API Server

🎯 app.py 的作用：
这是一个 Web API 服务器，主要功能是：
1. 创建 Web 服务接口 - 把 Python DOE 分析函数包装成 Web API
2. 允许其他系统（包括 AI Agent）通过 HTTP 请求调用分析功能
3. 提供多种数据输入方式（文件上传、JSON+Base64、AI Foundry兼容格式）

🔄 调用流程：
阶段1：本地开发 - uvicorn app:app --reload (http://localhost:8000)
阶段2：云部署 - 部署到 Render.com (https://mixedmodeldoe-v1.onrender.com)
阶段3：被调用 - Swagger UI测试、AI Agent自动调用、其他系统集成

🧩 核心调用链：
用户/AI Agent → HTTP请求 → app.py → run_mixed_model_doe() → 分析结果

📡 提供的 API 端点：
- /runDOE (POST) - 文件上传接口（multipart/form-data）
- /runDOEjson (POST) - JSON+Base64 接口
- /api/DoeAnalysis (POST) - AI Foundry 兼容接口（推荐）

Author: [Your Name]
Created: August 2025
Version: 2.0.0
"""

from fastapi import FastAPI, UploadFile, File, Body
from fastapi.responses import JSONResponse
import shutil
import os
import base64
import tempfile
import pandas as pd
from MixedModelDOE_Function_FollowOriginal_20250804 import run_mixed_model_doe

# 创建 FastAPI 应用实例
app = FastAPI(
    title="Mixed Model DOE Analysis API",
    description="API for performing Design of Experiments (DOE) analysis using Mixed Models. Analyzes L*a*b color space data with statistical modeling.",
    version="2.0.0"
)

# ==================== 端点1: 传统文件上传接口 ====================
@app.post("/runDOE")
async def run_doe(file: UploadFile = File(None)):
    """
    传统文件上传接口 (multipart/form-data)
    
    用途：
    - 用户通过 Swagger UI 手动上传 CSV 文件
    - 支持传统的表单文件上传
    
    输入：CSV 文件
    输出：分析结果文件列表
    
    调用示例：
    - Swagger UI: https://mixedmodeldoe-v1.onrender.com/docs
    - curl: curl -X POST -F "file=@data.csv" https://mixedmodeldoe-v1.onrender.com/runDOE
    """
    # 处理未上传文件或空文件名的情况，返回标准 JSON 错误
    if file is None or not hasattr(file, "filename") or not file.filename:
        return JSONResponse(
            status_code=400,
            content={"status": "error", "message": "No file uploaded"}
        )

    # 使用 os.path.basename 清理上传文件名，防止路径穿越攻击
    safe_filename = os.path.basename(file.filename)

    # 设置输入和输出目录（适用于 Windows）
    input_dir = "./input"
    output_dir = "./outputDOE"
    os.makedirs(input_dir, exist_ok=True)
    os.makedirs(output_dir, exist_ok=True)

    # 构建安全的输入文件路径
    input_path = os.path.join(input_dir, safe_filename)

    # 保存上传的文件
    try:
        with open(input_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"status": "error", "message": f"File save failed: {str(e)}"}
        )

    # 调用 DOE 分析函数（核心业务逻辑）
    try:
        run_mixed_model_doe(file_path=input_path, output_dir=output_dir)
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"status": "error", "message": f"DOE analysis failed: {str(e)}"}
        )

    # 返回分析结果
    return {
        "status": "success",
        "input_file": input_path,
        "output_dir": output_dir,
        "files": os.listdir(output_dir)
    }

@app.get("/runDOE")
async def run_doe_get():
    """
    健康检查端点
    用途：验证 API 服务是否正常运行
    """
    return {"status": "ready"}


# ==================== 数据模型定义 ====================
from pydantic import BaseModel
from typing import Optional, List

class DOEJsonRequest(BaseModel):
    """
    JSON+Base64 请求格式
    用于 /runDOEjson 接口
    """
    filename: str  # 原始文件名（仅作标识）
    file_b64: str  # base64 编码的 CSV 文件内容

class DoeAnalysisRequest(BaseModel):
    """
    AI Foundry 兼容的请求格式
    用于 /api/DoeAnalysis 接口（推荐）
    
    重要：基于同事经验的 AI Foundry 格式要求
    - response_column 必须是逗号分隔的字符串，不能是数组
    - 必须包含 threshold 参数
    - data 支持 base64 编码或原始 CSV
    """
    data: str  # base64 编码的 CSV 数据或原始 CSV 字符串
    response_column: str  # 逗号分隔的响应变量，如 "Lvalue,Avalue,Bvalue"
    predictors: Optional[str] = None  # 逗号分隔的预测变量（可选）
    threshold: Optional[float] = 1.5  # LogWorth 阈值
    force_full_dataset: Optional[bool] = True  # 是否使用完整数据集


# ==================== 端点2: JSON+Base64 接口 ====================
@app.post("/runDOEjson")
async def run_doe_json(request: DOEJsonRequest):
    """
    JSON+Base64 接口
    
    用途：
    - 支持不能直接上传文件的环境
    - 通过 JSON 传输 base64 编码的 CSV 数据
    
    输入格式：
    {
        "filename": "data.csv",
        "file_b64": "base64编码的CSV内容"
    }
    
    调用示例：
    curl -X POST -H "Content-Type: application/json" \
         -d '{"filename":"test.csv","file_b64":"ZHllMSxkeWUy..."}' \
         https://mixedmodeldoe-v1.onrender.com/runDOEjson
    """
    try:
        # 解码 base64 内容并保存为临时 CSV 文件
        csv_bytes = base64.b64decode(request.file_b64)
        with tempfile.NamedTemporaryFile(delete=False, suffix=".csv") as tmp:
            tmp.write(csv_bytes)
            tmp_path = tmp.name
            
        # 设置输出目录
        output_dir = "./outputDOE"
        os.makedirs(output_dir, exist_ok=True)
        
        # 调用 DOE 分析
        run_mixed_model_doe(file_path=tmp_path, output_dir=output_dir)
        
        # 返回结果
        return {
            "status": "success",
            "input_file": tmp_path,
            "output_dir": output_dir,
            "files": os.listdir(output_dir)
        }
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"status": "error", "message": f"DOE analysis failed: {str(e)}"}
        )


# ==================== 端点3: AI Foundry 兼容接口（推荐） ====================
@app.post("/api/DoeAnalysis")
async def doe_analysis(request: DoeAnalysisRequest):
    """
    AI Foundry 兼容的 DOE 分析接口（推荐使用）
    
    用途：
    - 专为 AI Foundry/Copilot Studio 设计
    - 支持灵活的数据输入和可配置的响应变量
    - 基于同事成功经验的参数格式
    
    关键要求（基于同事的 AI Foundry 集成经验）：
    1. response_column 必须是逗号分隔的字符串，不能是数组
    2. 必须包含 threshold 参数
    3. data 支持 base64 编码数据
    
    输入格式：
    {
        "data": "base64编码的CSV数据",
        "response_column": "Lvalue,Avalue,Bvalue",  // 注意：字符串格式，不是数组
        "predictors": "dye1,dye2,Time,Temp",        // 可选
        "threshold": 1.5,
        "force_full_dataset": true
    }
    
    ❌ 错误格式：
    {
        "response_column": ["Lvalue","Avalue","Bvalue"]  // 数组格式会导致错误
    }
    
    ✅ 正确格式：
    {
        "response_column": "Lvalue,Avalue,Bvalue"  // 逗号分隔字符串
    }
    """
    try:
        # 数据输入处理 - 支持多种格式
        if request.data.startswith("http"):
            # URL 输入 - 暂时不支持，返回错误
            return JSONResponse(
                status_code=400,
                content={
                    "status": "error", 
                    "message": "URL data input not supported yet. Please use base64 encoded data."
                }
            )
        elif "," in request.data and "\n" in request.data:
            # 原始 CSV 数据（包含逗号和换行符）
            csv_content = request.data.encode('utf-8')
        else:
            # base64 编码数据
            try:
                csv_content = base64.b64decode(request.data)
            except Exception:
                return JSONResponse(
                    status_code=400,
                    content={"status": "error", "message": "Invalid base64 data format"}
                )
        
        # 创建临时文件存储 CSV 数据
        with tempfile.NamedTemporaryFile(delete=False, suffix=".csv", mode='wb') as tmp:
            tmp.write(csv_content)
            tmp_path = tmp.name
        
        # 设置输出目录
        output_dir = "./outputDOE"
        os.makedirs(output_dir, exist_ok=True)
        
        # 调用核心 DOE 分析函数
        run_mixed_model_doe(file_path=tmp_path, output_dir=output_dir)
        
        # 构建 AI Foundry 兼容的响应格式
        response = {
            "status": "success",
            "summary": {
                "response_variables": request.response_column.split(","),  # 将字符串转换为数组
                "threshold": request.threshold,
                "force_full_dataset": request.force_full_dataset,
                "analysis_completed": True
            },
            "input_file": tmp_path,
            "output_dir": output_dir,
            "files": os.listdir(output_dir)
        }
        
        # 清理临时文件
        try:
            os.unlink(tmp_path)
        except:
            pass  # 忽略删除失败
            
        return response
        
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"status": "error", "message": f"DOE analysis failed: {str(e)}"}
        )


# ==================== 应用启动说明 ====================
"""
本地启动：
    uvicorn app:app --reload
    访问：http://localhost:8000/docs

云端部署：
    部署到 Render.com
    访问：https://mixedmodeldoe-v1.onrender.com/docs
    
API 测试：
    1. Swagger UI: /docs
    2. Postman: 导入 OpenAPI schema
    3. AI Foundry: 使用 /api/DoeAnalysis 接口
    
相关文件：
    - openapi.json: 原始接口的 OpenAPI 规范
    - openapi_runDOEjson.json: JSON+Base64 接口规范
    - openapi_doe_analysis_ai_foundry.json: AI Foundry 兼容接口规范
"""
