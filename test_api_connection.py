import requests
import base64
import json

def test_doe_api():
    """
    直接测试DOE API - 不依赖AI Foundry
    """
    print("🔬 测试DOE API连接...")
    
    # 读取您的CSV文件
    csv_path = r"C:\Zhanglei_Microsoft_Upgrade_by_20240905\Pytyon_Study_Local\Color_S2\DOEData_20250622.csv"
    
    try:
        with open(csv_path, 'rb') as f:
            csv_content = f.read()
            base64_data = base64.b64encode(csv_content).decode('utf-8')
        
        print("✅ CSV文件读取成功")
        print(f"📁 文件大小: {len(csv_content)} bytes")
        
        # 准备API请求 - 使用DoEAgent2兼容格式
        payload = {
            'data': base64_data,
            'response_vars': ['Lvalue', 'Avalue', 'Bvalue'],  # 数组格式
            'predictors': ['dye1', 'dye2', 'Time', 'Temp'],   # 数组格式
            'threshold': 1.3,                                 # 数字格式
            'min_significant': 2
        }
        
        print("🚀 发送API请求...")
        response = requests.post(
            'https://mixedmodeldoe-v1.onrender.com/api/DoeAnalysis',
            json=payload,
            headers={'Content-Type': 'application/json'},
            timeout=60
        )
        
        print(f"📡 响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ API调用成功!")
            print("📊 分析结果:")
            print(json.dumps(result, indent=2, ensure_ascii=False))
            return True
        else:
            print(f"❌ API调用失败: {response.status_code}")
            print(f"错误信息: {response.text}")
            return False
            
    except FileNotFoundError:
        print(f"❌ 找不到CSV文件: {csv_path}")
        return False
    except Exception as e:
        print(f"❌ 执行错误: {str(e)}")
        return False

def test_with_original_format():
    """
    测试原始格式的API调用
    """
    print("\n🔄 测试原始格式...")
    
    csv_path = r"C:\Zhanglei_Microsoft_Upgrade_by_20240905\Pytyon_Study_Local\Color_S2\DOEData_20250622.csv"
    
    try:
        with open(csv_path, 'rb') as f:
            csv_content = f.read()
            base64_data = base64.b64encode(csv_content).decode('utf-8')
        
        # 原始格式
        payload = {
            'data': base64_data,
            'response_column': 'Lvalue,Avalue,Bvalue',  # 字符串格式
            'predictors': 'dye1,dye2,Time,Temp',        # 字符串格式
            'threshold': '1.5',                         # 字符串格式
            'force_full_dataset': 'true'
        }
        
        response = requests.post(
            'https://mixedmodeldoe-v1.onrender.com/api/DoeAnalysis',
            json=payload,
            headers={'Content-Type': 'application/json'},
            timeout=60
        )
        
        print(f"📡 原始格式响应: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ 原始格式也成功!")
            return True
        else:
            print(f"❌ 原始格式失败: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ 原始格式错误: {str(e)}")
        return False

if __name__ == "__main__":
    print("🔬 DOE API 连接测试")
    print("=" * 50)
    
    # 测试DoEAgent2兼容格式
    success1 = test_doe_api()
    
    # 测试原始格式
    success2 = test_with_original_format()
    
    print("\n" + "=" * 50)
    print("📋 测试总结:")
    print(f"DoEAgent2格式: {'✅ 成功' if success1 else '❌ 失败'}")
    print(f"原始格式: {'✅ 成功' if success2 else '❌ 失败'}")
    
    if success1 or success2:
        print("\n🎉 恭喜！您的API正常工作")
        print("💡 现在可以继续配置AI Foundry集成")
    else:
        print("\n⚠️  API需要调试，请检查:")
        print("1. 网络连接")
        print("2. API端点URL")
        print("3. CSV文件格式")
        print("4. 服务器状态")
