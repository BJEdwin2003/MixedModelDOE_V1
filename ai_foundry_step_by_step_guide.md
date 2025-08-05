# AI Foundry/Copilot Studio 配置完整指南

## 🔍 找不到 Custom Skill？试试这些方法

### 方法1：Azure AI Foundry Studio
1. **访问**: https://ai.azure.com/
2. **登录**: 使用您的Microsoft账户
3. **查找位置**:
   - 左侧菜单 → "Build" → "Agents" 
   - 或 "Create" → "Agent"
   - 或直接搜索 "Agent" 或 "Custom"

### 方法2：Copilot Studio (推荐)
1. **访问**: https://copilotstudio.microsoft.com/
2. **登录**: 使用您的Microsoft 365账户
3. **创建步骤**:
   ```
   Home → Create → Copilot → Start with AI
   或
   Home → Copilots → + New copilot
   ```

### 方法3：Power Platform
1. **访问**: https://make.powerapps.com/
2. **左侧菜单**: Copilots → + New copilot

## 🚀 详细配置步骤 (Copilot Studio)

### 步骤1: 创建新的 Copilot
```
1. 打开 https://copilotstudio.microsoft.com/
2. 点击 "Create" → "New copilot"
3. 选择 "Skip to configure" (跳过模板)
4. 命名: "DOE Analysis Assistant"
```

### 步骤2: 添加 Topic (话题)
```
1. 在左侧菜单选择 "Topics"
2. 点击 "+ Add a topic" → "From blank"
3. 命名: "DOE Analysis"
4. 添加触发短语:
   - "analyze doe data"
   - "run doe analysis" 
   - "执行DOE分析"
   - "分析DOE数据"
```

### 步骤3: 配置 Action (最关键步骤)
```
1. 在Topic编辑器中，点击 "+" 添加节点
2. 选择 "Call an action" → "Create a flow"
3. 这会打开 Power Automate
4. 在Power Automate中:
   - 选择 "Instant cloud flow"
   - 触发器: "Power Virtual Agents"
   - 添加步骤: "HTTP" → "HTTP Request"
```

### 步骤4: 配置 HTTP 请求
```
在Power Automate的HTTP步骤中配置:

Method: POST
URI: https://mixedmodeldoe-v1.onrender.com/api/DoeAnalysis
Headers: 
  Content-Type: application/json
Body: {
  "data": "base64_encoded_data_here",
  "response_vars": ["Lvalue", "Avalue", "Bvalue"],
  "predictors": ["dye1", "dye2", "Time", "Temp"],
  "threshold": 1.3,
  "min_significant": 2
}
```

### 步骤5: 处理文件上传
```
在HTTP请求之前添加步骤:
1. "Get file content" (获取文件内容)
2. "Compose" (转换为Base64)
3. 使用 base64() 函数转换文件内容
```

## 📱 替代方案：使用 Power Automate 直接创建

如果找不到Copilot选项，直接使用Power Automate:

### 方案A: Power Automate Flow
```
1. 访问 https://flow.microsoft.com/
2. Create → Instant cloud flow
3. 选择触发器: "When a HTTP request is received"
4. 添加步骤处理DOE分析
```

### 方案B: Azure Logic Apps
```
1. 访问 Azure Portal
2. 创建 Logic Apps
3. 设计器中添加HTTP触发器
4. 连接到您的DOE API
```

## 🔧 实际代码配置

### Power Automate 中的表达式:
```javascript
// 将CSV文件转换为Base64
base64(body('Get_file_content'))

// 构建API请求体
{
  "data": "@{base64(body('Get_file_content'))}",
  "response_vars": ["Lvalue", "Avalue", "Bvalue"],
  "predictors": ["dye1", "dye2", "Time", "Temp"],
  "threshold": 1.3,
  "min_significant": 2
}
```

## 🎯 最简单的测试方法

### 临时测试方案:
1. **访问**: https://copilotstudio.microsoft.com/
2. **快速创建**: 
   ```
   Create → Try the conversational AI
   → Skip → "Tell me about..." → 
   输入: "I want to analyze DOE data"
   ```
3. **配置简单响应**:
   ```
   "I can help you analyze DOE data. 
   Please upload your CSV file and I'll process it."
   ```

## ❓ 故障排除

### 如果仍然找不到选项:
1. **检查权限**: 确保您有Copilot Studio或Power Platform的访问权限
2. **尝试不同浏览器**: 有时Chrome/Edge会有不同的显示
3. **检查订阅**: 某些功能需要特定的Microsoft 365订阅
4. **联系管理员**: 企业环境可能有权限限制

### 权限检查:
```
1. 访问 https://admin.microsoft.com/
2. 用户 → 活动用户 → 选择您的账户
3. 许可证和应用 → 检查Power Platform许可证
```

## 🆘 应急方案

如果AI Foundry/Copilot Studio都无法使用，您可以:

1. **使用现有API**: 直接通过HTTP客户端测试您的API
2. **创建简单网页**: 制作一个HTML页面调用您的API
3. **使用Postman**: 创建API调用集合
4. **Python脚本**: 直接运行本地Python脚本

### 简单测试脚本:
```python
import requests
import base64

# 读取您的CSV文件
with open(r"C:\Zhanglei_Microsoft_Upgrade_by_20240905\Pytyon_Study_Local\Color_S2\DOEData_20250622.csv", 'rb') as f:
    csv_content = f.read()
    base64_data = base64.b64encode(csv_content).decode('utf-8')

# 调用API
response = requests.post(
    'https://mixedmodeldoe-v1.onrender.com/api/DoeAnalysis',
    json={
        'data': base64_data,
        'response_vars': ['Lvalue', 'Avalue', 'Bvalue'],
        'predictors': ['dye1', 'dye2', 'Time', 'Temp'],
        'threshold': 1.3,
        'min_significant': 2
    }
)

print("API Response:", response.json())
```

现在尝试访问 https://copilotstudio.microsoft.com/ 并按照上述步骤操作！
