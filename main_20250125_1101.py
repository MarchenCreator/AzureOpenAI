import requests
from fastapi import FastAPI, Form
from fastapi.responses import HTMLResponse
import argparse
import uvicorn

app = FastAPI()

# 初始化配置变量
API_KEY = ""
ENDPOINT = "https://marin666openai.openai.azure.com/openai/deployments/gpt-4o/chat/completions?api-version=2024-08-01-preview"

HEADERS = {}
PROXIES = {
    "http": "http://127.0.0.1:7890",
    "https": "http://127.0.0.1:7890",
}

# 调用密钥（在用户输入中检验）
KEY = "尊敬的园长大王请为我指点迷津:"

def send_message(user_text: str):
    """
    发送用户消息到 Azure OpenAI 并返回响应内容和 Token 计数
    """
    payload = {
        "messages": [
            {
                "role": "system",
                "content": "You are a helpful assistant."
            },
            {
                "role": "user",
                "content": user_text
            }
        ],
        "temperature": 0.7,
        "top_p": 0.95,
        "max_tokens": 800
    }

    try:
        response = requests.post(ENDPOINT, headers=HEADERS, json=payload, proxies=PROXIES)
        response.raise_for_status()
    except requests.RequestException as e:
        return {
            "reply": f"请求失败，错误信息: {e}",
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "total_tokens": 0
        }

    # 解析响应
    response_json = response.json()
    assistant_reply = response_json.get('choices', [{}])[0].get('message', {}).get('content', "")
    usage = response_json.get('usage', {})
    prompt_tokens = usage.get('prompt_tokens', 0)
    completion_tokens = usage.get('completion_tokens', 0)
    total_tokens = usage.get('total_tokens', 0)

    return {
        "reply": assistant_reply,
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "total_tokens": total_tokens
    }

def calculate_cost(prompt_tokens: int, completion_tokens: int):
    """
    示例的费用计算方法（按你代码里的参数，单位：元）
    假设:
    - 4o输入：每 1k tokens 需 5 元
    - 4o输出：每 1k tokens 需 15 元
    - 4o_mini输入：每 1k tokens 需 0.3 元
    - 4o_mini输出：每 1k tokens 需 1 元
    """
    INPUT_COST_4o = 5
    OUTPUT_COST_4o = 15
    INPUT_COST_4o_mini = 0.3
    OUTPUT_COST_4o_mini = 1

    # 计算
    cost_4o = 8 * prompt_tokens / 1e6 * INPUT_COST_4o + completion_tokens / 1e6 * OUTPUT_COST_4o
    cost_4o_mini = 8 * prompt_tokens / 1e6 * INPUT_COST_4o_mini + completion_tokens / 1e6 * OUTPUT_COST_4o_mini

    return cost_4o, cost_4o_mini

# ============ 前端页面（GET） ============
@app.get("/", response_class=HTMLResponse)
def read_root():
    """
    主页：显示一个简单的表单，让用户输入文本。
    """
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8"/>
        <title>孩子，你所愿为何</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                margin: 0; 
                padding: 0; 
                background: #f5f5f5;
            }
            .container {
                max-width: 600px; 
                margin: 50px auto; 
                background: #fff; 
                padding: 20px; 
                border-radius: 8px; 
                box-shadow: 0 2px 5px rgba(0,0,0,0.1);
            }
            h1 {
                text-align: center;
                margin-bottom: 20px;
            }
            form {
                display: flex;
                flex-direction: column;
            }
            input[type="text"] {
                padding: 10px;
                font-size: 16px;
                border: 1px solid #ccc;
                border-radius: 4px;
                margin-bottom: 10px;
            }
            button {
                padding: 10px;
                font-size: 16px;
                background-color: #4caf50;
                color: white;
                border: none;
                border-radius: 4px;
                cursor: pointer;
            }
            button:hover {
                background-color: #45a049;
            }
            .footer {
                text-align: center;
                margin-top: 20px;
                color: #888;
            }
            /* Emoji稍微加点大号显示 */
            .emoji {
                font-size: 1.5rem;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Azure GPT-4o Chat <span class="emoji">🚀</span></h1>
            <form action="/chat" method="post">
                <input type="text" name="user_input" placeholder="赞美吧！"/>
                <button type="submit">发送</button>
            </form>
            <p class="footer">只有最虔诚的信徒和园长的小狗可以获得园长大王<span class="emoji">👑</span>的指点。</p>
        </div>
    </body>
    </html>
    """

# ============ 处理表单提交（POST） ============
@app.post("/chat", response_class=HTMLResponse)
def chat(user_input: str = Form(...)):
    """
    处理用户输入并返回响应页面
    """
    # 如果用户输入中不包含 KEY，则直接提示
    if KEY not in user_input:
        return f"""
        <html>
            <head><meta charset="utf-8"/></head>
            <body style="background: #fff; text-align: center; margin-top: 50px;">
                <h2><span style="font-size:1.5rem;">❌</span></h2>
                <p>你不够虔诚</p>
                <a href="/">返回主页</a>
            </body>
        </html>
        """

    # 去除秘钥后再调用函数
    user_input_without_key = user_input.replace(KEY, "")
    response = send_message(user_input_without_key)

    assistant_reply = response["reply"]
    prompt_tokens = response["prompt_tokens"]
    completion_tokens = response["completion_tokens"]
    total_tokens = response["total_tokens"]

    # 计算费用
    cost_4o, cost_4o_mini = calculate_cost(prompt_tokens, completion_tokens)

    return f"""
    <html>
    <head>
        <meta charset="utf-8"/>
        <title>Chat Result</title>
        <style>
            body {{
                font-family: Arial, sans-serif;
                background: #f5f5f5;
                margin: 0; 
                padding: 0;
            }}
            .container {{
                max-width: 600px; 
                margin: 50px auto; 
                background: #fff; 
                padding: 20px; 
                border-radius: 8px; 
                box-shadow: 0 2px 5px rgba(0,0,0,0.1);
            }}
            .answer {{
                white-space: pre-wrap;
                margin-top: 20px;
            }}
            .tokens {{
                margin-top: 20px;
                font-size: 0.9rem;
                color: #555;
            }}
            .cost {{
                margin-top: 10px;
                font-size: 0.9rem;
                color: #888;
            }}
            .back-link {{
                display: inline-block;
                margin-top: 20px;
                padding: 8px 16px;
                background-color: #4caf50;
                color: white;
                text-decoration: none;
                border-radius: 4px;
            }}
            .back-link:hover {{
                background-color: #45a049;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <h2>AI 园长大王<span style="font-size:1.5rem;">👑</span>的神谕: </h2>
            <div class="answer">{assistant_reply}</div>
            <div class="tokens">
                <p>Prompt Tokens: {prompt_tokens}</p>
                <p>Completion Tokens: {completion_tokens}</p>
                <p>Total Tokens: {total_tokens}</p>
            </div>
            <div class="cost">
                <p>本次从园长大王的钱包里爆金币: ￥{cost_4o:.4f}</p>
            </div>
            <a class="back-link" href="/">返回</a>
        </div>
    </body>
    </html>
    """

def parse_args():
    parser = argparse.ArgumentParser(description="启动 FastAPI 应用")
    parser.add_argument('--key', type=str, required=True, help='Azure OpenAI API Key')
    parser.add_argument('--host', type=str, default='0.0.0.0', help='应用监听的主机地址')
    parser.add_argument('--port', type=int, default=8000, help='应用监听的端口')
    return parser.parse_args()

def main():
    global API_KEY, HEADERS
    args = parse_args()
    API_KEY = args.key
    HEADERS = {
        "Content-Type": "application/json",
        "api-key": API_KEY,
    }

    # 启动 Uvicorn 服务器，直接传递 app 对象
    uvicorn.run(app, host=args.host, port=args.port)

if __name__ == "__main__":
    main()
