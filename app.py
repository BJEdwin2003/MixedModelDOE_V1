from fastapi import FastAPI, UploadFile, File
import shutil
import os
from MixedModelDOE_Mean_and_Var_as_Function_to_Github_20250802 import run_mixed_model_doe

app = FastAPI()

@app.post("/runDOE")
async def run_doe(file: UploadFile = File(...)):
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
    with open(input_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # 调用 DOE 函数
    run_mixed_model_doe(file_path=input_path, output_dir=output_dir)

    # 返回结果
    return {
        "status": "success",
        "input_file": input_path,
        "output_dir": output_dir,
        "files": os.listdir(output_dir)
    }
