"""
CSV to Base64 Converter Tool
用于将 CSV 文件转换为 Base64 编码，供 AI Foundry/Copilot Studio 使用

🔍 关于文件路径的处理：
1. 手动指定路径 - 用户输入完整文件路径
2. 自动扫描路径 - 程序自动查找当前目录的 CSV 文件
3. API 自动处理 - 通过 HTTP 请求传递 Base64 数据，无需本地路径

Author: Zhang Lei
Created: August 2025
"""

import base64
import os
import json
import glob

def list_csv_files_in_directory(directory="."):
    """
    列出指定目录中的所有 CSV 文件
    
    Args:
        directory (str): 目录路径，默认为当前目录
        
    Returns:
        list: CSV 文件路径列表
    """
    csv_pattern = os.path.join(directory, "*.csv")
    csv_files = glob.glob(csv_pattern)
    return csv_files

def csv_to_base64(csv_file_path):
    """
    将 CSV 文件转换为 Base64 编码
    
    Args:
        csv_file_path (str): CSV 文件的完整路径
        
    Returns:
        str: Base64 编码的字符串
    """
    try:
        print(f"📁 正在读取文件：{csv_file_path}")
        with open(csv_file_path, 'rb') as file:
            csv_content = file.read()
            base64_encoded = base64.b64encode(csv_content).decode('utf-8')
            print(f"✅ 文件读取成功，大小：{len(csv_content)} 字节")
            print(f"🔄 Base64 编码成功，长度：{len(base64_encoded)} 字符")
            return base64_encoded
    except FileNotFoundError:
        print(f"❌ 错误：文件不存在 - {csv_file_path}")
        return None
    except PermissionError:
        print(f"❌ 错误：没有权限读取文件 - {csv_file_path}")
        return None
    except Exception as e:
        print(f"❌ 错误：无法读取文件 {csv_file_path}")
        print(f"📝 详细错误：{str(e)}")
        return None

def create_ai_foundry_json(csv_file_path, response_columns="Lvalue,Avalue,Bvalue", 
                          predictors=None, threshold=1.5):
    """
    创建 AI Foundry 兼容的 JSON 请求格式
    
    Args:
        csv_file_path (str): CSV 文件路径
        response_columns (str): 响应变量（逗号分隔）
        predictors (str): 预测变量（逗号分隔，可选）
        threshold (float): LogWorth 阈值
        
    Returns:
        dict: AI Foundry 请求格式的字典
    """
    base64_data = csv_to_base64(csv_file_path)
    if base64_data is None:
        return None
        
    request_json = {
        "data": base64_data,
        "response_column": response_columns,
        "threshold": threshold,
        "force_full_dataset": True
    }
    
    if predictors:
        request_json["predictors"] = predictors
        
    return request_json

def save_json_file(json_data, output_file_path):
    """
    保存 JSON 数据到文件
    
    Args:
        json_data (dict): 要保存的 JSON 数据
        output_file_path (str): 输出文件路径
    """
    try:
        with open(output_file_path, 'w', encoding='utf-8') as file:
            json.dump(json_data, file, indent=2, ensure_ascii=False)
        print(f"✅ JSON 文件已保存到：{output_file_path}")
    except Exception as e:
        print(f"❌ 保存 JSON 文件失败：{str(e)}")

def main():
    """
    主函数：交互式转换工具
    """
    print("🔄 CSV 转 Base64 转换工具")
    print("=" * 50)
    
    # 🔍 路径处理方式1：自动扫描当前目录
    print("📁 正在扫描当前目录的 CSV 文件...")
    current_dir = os.getcwd()
    print(f"📂 当前工作目录：{current_dir}")
    
    csv_files = list_csv_files_in_directory(current_dir)
    
    if csv_files:
        print(f"\n📋 发现 {len(csv_files)} 个 CSV 文件：")
        for i, file in enumerate(csv_files, 1):
            filename = os.path.basename(file)
            filesize = os.path.getsize(file)
            print(f"   {i}. {filename} ({filesize} 字节)")
        
        # 让用户选择文件
        print(f"\n请选择要转换的文件：")
        print(f"1-{len(csv_files)}. 选择上述文件")
        print(f"0. 手动输入文件路径")
        
        choice = input("请输入选择（1-{} 或 0）：".format(len(csv_files))).strip()
        
        if choice == "0":
            # 🔍 路径处理方式2：手动输入路径
            csv_file = input("请输入 CSV 文件的完整路径：").strip()
        else:
            try:
                file_index = int(choice) - 1
                if 0 <= file_index < len(csv_files):
                    csv_file = csv_files[file_index]
                else:
                    print("❌ 选择无效")
                    return
            except ValueError:
                print("❌ 输入无效")
                return
    else:
        print("⚠️ 当前目录没有找到 CSV 文件")
        # 🔍 路径处理方式3：手动输入路径
        csv_file = input("请输入 CSV 文件的完整路径：").strip()
    
    if not csv_file:
        print("❌ 请提供有效的文件路径")
        return
        
    if not os.path.exists(csv_file):
        print(f"❌ 文件不存在：{csv_file}")
        return
    
    print(f"\n📁 选择的文件：{csv_file}")
    
    # 获取响应变量
    response_cols = input("请输入响应变量（逗号分隔，默认：Lvalue,Avalue,Bvalue）：").strip()
    if not response_cols:
        response_cols = "Lvalue,Avalue,Bvalue"
    
    # 获取预测变量（可选）
    predictors = input("请输入预测变量（逗号分隔，可选）：").strip()
    if not predictors:
        predictors = None
    
    # 获取阈值
    threshold_input = input("请输入 LogWorth 阈值（默认：1.5）：").strip()
    try:
        threshold = float(threshold_input) if threshold_input else 1.5
    except ValueError:
        threshold = 1.5
        print("⚠️ 阈值输入无效，使用默认值 1.5")
    
    print("\n🔄 正在转换...")
    
    # 方式1：输出 Base64 字符串
    base64_result = csv_to_base64(csv_file)
    if base64_result:
        print(f"\n✅ Base64 编码成功！")
        
        # 保存 Base64 到文件
        base64_file = csv_file.replace('.csv', '_base64.txt')
        with open(base64_file, 'w') as f:
            f.write(base64_result)
        print(f"💾 Base64 字符串已保存到：{base64_file}")
    
    # 方式2：创建 AI Foundry JSON 格式
    json_result = create_ai_foundry_json(csv_file, response_cols, predictors, threshold)
    if json_result:
        json_file = csv_file.replace('.csv', '_ai_foundry_request.json')
        save_json_file(json_result, json_file)
        
        print(f"\n📋 AI Foundry 请求格式预览：")
        print(f"   data: [Base64 编码的 CSV 数据 - {len(json_result['data'])} 字符]")
        print(f"   response_column: {json_result['response_column']}")
        print(f"   threshold: {json_result['threshold']}")
        if 'predictors' in json_result:
            print(f"   predictors: {json_result['predictors']}")
    
    print(f"\n🎯 使用说明：")
    print(f"1. 将 Base64 字符串复制到 AI Agent 聊天窗口")
    print(f"2. 或者将整个 JSON 文件内容发送给 API")
    print(f"3. API 端点：https://mixedmodeldoe-v1.onrender.com/api/DoeAnalysis")
    
    print(f"\n📍 路径说明：")
    print(f"📂 工作目录：{current_dir}")
    print(f"📁 源文件：{csv_file}")
    print(f"💾 Base64文件：{base64_file}")
    print(f"📋 JSON文件：{json_file}")

if __name__ == "__main__":
    main()
