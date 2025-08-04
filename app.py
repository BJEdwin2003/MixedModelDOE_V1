from fastapi import FastAPI, UploadFile, File
from fastapi.responses import JSONResponse
import shutil
import os
from MixedModelDOE_Function_FollowOriginal_20250804 import run_mixed_model_doe

app = FastAPI(
    title="Mixed Model DOE Analysis API",
    description="API for performing Design of Experiments (DOE) analysis using Mixed Models. Analyzes L*a*b color space data with statistical modeling.",
    version="1.1.0"
)

@app.post("/runDOE")
async def run_doe(file: UploadFile = File(None)):
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

    # 调用 DOE 函数
    try:
        run_mixed_model_doe(file_path=input_path, output_dir=output_dir)
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"status": "error", "message": f"DOE analysis failed: {str(e)}"}
        )

    # 返回结果
    return {
        "status": "success",
        "input_file": input_path,
        "output_dir": output_dir,
        "files": os.listdir(output_dir)
    }

@app.get("/runDOE")
async def run_doe_get():
    return {"status": "ready"}
