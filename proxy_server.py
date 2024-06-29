import json
import os
import sys
from typing import Optional

from anthropic import AnthropicVertex
from dotenv import load_dotenv
from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel
from secrets import compare_digest

# 初始化 FastAPI 应用程序
app = FastAPI()

# 获取环境变量 DOCKER_ENV，如果没有设置，默认为 False
is_docker = os.environ.get('DOCKER_ENV', 'False').lower() == 'true'

#加载文件目录
def get_base_path():
    if getattr(sys, 'frozen', False):
        # 如果是打包后的可执行文件
        return os.path.dirname(sys.executable)
    else:
        # 如果是从Python运行
        return os.path.dirname(os.path.abspath(__file__))

# 加载环境变量
env_path = os.path.join(get_base_path(), '.env')
load_dotenv(env_path)

os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = os.path.join(get_base_path(), 'auth', 'auth.json')
hostaddr = '0.0.0.0' if is_docker else os.getenv('HOST', '127.0.0.1')
lsnport = int(os.getenv('PORT', 5000))
project_id = os.getenv('PROJECT_ID')
region = os.getenv('REGION')
password = os.getenv('PASSWORD')

# VertexAI 配置
vertex_client = AnthropicVertex(project_id=project_id, region=region)

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class MessageRequest(BaseModel):
    model: str
    stream: Optional[bool] = False
    # 添加其他可能的字段

def vertex_model(original_model):
    # 定义模型名称映射
    mapping_file = os.path.join(get_base_path(), 'model_mapping.json')
    with open(mapping_file, 'r') as f:
        model_mapping = json.load(f)    
    return model_mapping[original_model]

# 比较密码
def check_auth(api_key: Optional[str]) -> bool:
    if not password:  # 如果密码未设置或为空字符串
        return True
    return api_key and compare_digest(api_key, password)

@app.post("/v1/messages")
async def proxy_request(request: Request, x_api_key: Optional[str] = Header(None)):
    # 密码验证
    if not check_auth(x_api_key):
        raise HTTPException(status_code=401, detail="Unauthorized")

    # 获取原始请求数据
    data = await request.json()
    
#    print("Original request:")
#    print(data)

    # 准备发送到 VertexAI 的请求
    try:
        # 创建一个新的字典来存储请求参数
        vertex_request = {}
        
        # 遍历原始请求中的所有键值对
        for key, value in data.items():
            if key == 'model':
                # 对模型名称进行转换
                vertex_request[key] = vertex_model(value)
            else:
                # 直接复制其他所有参数
                vertex_request[key] = value
                
        # 输出处理后的请求
#        print("Processed request:")
#        print(json.dumps(vertex_request, indent=2))

        # 发送请求到 VertexAI
        # 检查是否为流式请求
        if vertex_request.get('stream', False):
            def generate():
                yield 'event: ping\ndata: {"type": "ping"}\n\n'
                for chunk in vertex_client.messages.create(**vertex_request):
                    response = f"event: {chunk.type}\ndata: {json.dumps(chunk.model_dump())}\n\n"
#                    print(f"{response}")
                    yield response

            return StreamingResponse(generate(), media_type='text/event-stream', headers={'X-Accel-Buffering': 'no'})
        else:
            response = vertex_client.messages.create(**vertex_request)
#            print(f"{response}")
            return JSONResponse(content=response.model_dump(), status_code=200)

    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)
