import json
import os
import sys
import re
import ast
import random
from typing import Optional, Dict, Any

from anthropic import AsyncAnthropicVertex
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

hostaddr = '0.0.0.0' if is_docker else os.getenv('HOST', '127.0.0.1')
lsnport = int(os.getenv('PORT', 5000))
project_ids = os.getenv('PROJECT_ID').split(', ')
region = os.getenv('REGION')
password = os.getenv('PASSWORD')
debug_mode = os.getenv('DEBUG', 'False').lower() == 'true'

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

#负载均衡加权算法
class WeightedRandomSelector:
    def __init__(self, project_ids):
        self.projects = {pid: 1 for pid in project_ids}

    def get_project(self):
        if len(self.projects) <= 1:
            return next(iter(self.projects))

        total_weight = sum(self.projects.values())
        r = random.uniform(0, total_weight)
        for pid, weight in self.projects.items():
            r -= weight
            if r <= 0:
                self._update_weights(pid)
                return pid
        return list(self.projects.keys())[-1]

    def _update_weights(self, selected_pid):
        decrease = min(self.projects[selected_pid], 0.5)
        increase = decrease / (len(self.projects) - 1)
        
        for pid in self.projects:
            if pid == selected_pid:
                self.projects[pid] -= decrease
            else:
                self.projects[pid] += increase
        
    def print_weights(self):
        print("Current project weights:")
        for pid, weight in self.projects.items():
            print(f"  {pid}: {weight:.4f}")
        print()  # 添加一个空行，使输出更易读    

# 创建一个全局的 WeightedRandomSelector 实例
global_selector = WeightedRandomSelector(project_ids)

def load_balance_selector():
    default_auth_file = os.path.join(os.path.join(get_base_path(), 'auth'), 'auth.json')
    # 检查是否存在 auth.json
    if os.path.exists(default_auth_file):
        # 如果存在 auth.json，返回第一个 project_id 和 auth.json
        return project_ids[0], default_auth_file
    else:
        # 如果不存在 auth.json，加权随机选择
        project_id = global_selector.get_project()
        auth_file = os.path.join(get_base_path(), 'auth', f'{project_id}.json')
        if not os.path.exists(auth_file):
            # 如果文件不存在，抛出 HTTPException
            raise HTTPException(
                status_code=500,
                detail="No valid authentication file found. Please check your configuration."
            )
        return project_id, auth_file

def vertex_model(original_model):
    # 定义模型名称映射
    mapping_file = os.path.join(get_base_path(), 'model_mapping.json')
    with open(mapping_file, 'r') as f:
        model_mapping = json.load(f)    
    return model_mapping[original_model]

# 比较密码
def check_auth(api_key: Optional[str]) -> bool:
    if not password:  # 如果密码未设置或为空字符串
        debug_mode and print("No password set. Skipping...")
        return True
    return api_key and compare_digest(api_key, password)

def prepare_vertex_request(data: Dict[Any, Any]) -> Dict[Any, Any]:
    vertex_request = {}
    for key, value in data.items():
        if key == 'model':
            vertex_request[key] = vertex_model(value)
        else:
            vertex_request[key] = value
    return vertex_request

def parse_vertex_error(error_string):
    # 将错误信息分为两部分
    parts = error_string.split(' - ', 1)
    
    # 从第一部分提取错误代码
    error_code_match = re.search(r'Error code: (\d+)', parts[0])
    error_code = int(error_code_match.group(1)) if error_code_match else 500

    # 使用 ast.literal_eval 解析第二部分
    try:
        error_json = ast.literal_eval(parts[1])
        error_message = error_json[0]['error'].get('message', 'Unknown error')
        error_type = error_json[0]['error'].get('status') or error_json[0]['error'].get('type') or 'UNKNOWN_ERROR'
    except Exception as e:
        print(e)
        # 如果解析失败，使用默认值
        error_message = "Failed to parse error details"
        error_type = "PARSE_ERROR"

    error_content = {
        "type": "error",
        "error": {
            "type": error_type,
            "message": error_message
        }
    }

    return error_code, error_content

async def handle_stream_request(vertex_client, vertex_request: Dict[Any, Any]):
    try:
        message_iterator = await vertex_client.messages.create(**vertex_request)
        async def generate():
            try:
                is_first_chunk = True
                debug_mode and print("Start streaming:")
                async for chunk in message_iterator:
                    response = f"event: {chunk.type}\ndata: {json.dumps(chunk.model_dump())}\n\n"
                    yield response
                    # debug mode下输出响应
                    debug_mode and print(response)
                    if is_first_chunk:
                        is_first_chunk = False
                await vertex_client.close()
                debug_mode and print("Stream ended.")
            except Exception as e:
                error_code, error_content = parse_vertex_error(str(e))
                print(e)
                yield f"event: error\ndata: {json.dumps(error_content)}\n\n"
                await vertex_client.close()

        return generate()
    except Exception as e:
        print(e)
        error_code, error_content = parse_vertex_error(str(e))
        await vertex_client.close()
        return error_code, error_content

async def handle_non_stream_request(vertex_client, vertex_request: Dict[Any, Any]):
    try:
        response = await vertex_client.messages.create(**vertex_request)
        # debug mode下输出响应
        debug_mode and print(response)
        await vertex_client.close()
        return JSONResponse(content=response.model_dump(), status_code=200)
    except Exception as e:
        # 捕获初始化时的任何异常并返回错误信息
        print(e)
        error_code, error_content = parse_vertex_error(str(e))
        await vertex_client.close()
        return JSONResponse(content=error_content, status_code=error_code) 

@app.post("/v1/messages")
async def proxy_request(request: Request, x_api_key: Optional[str] = Header(None)):
    if not check_auth(x_api_key):
        raise HTTPException(status_code=401, detail="Unauthorized")

    data = await request.json()
    debug_mode and print(f"received request: {data}")

    try:
        vertex_request = prepare_vertex_request(data)
        project_id, auth_file = load_balance_selector()
        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = auth_file
        vertex_client = AsyncAnthropicVertex(project_id=project_id, region=region)
        print(f"accessing VertexAI via project {project_id}")

        if vertex_request.get('stream', False):
            result = await handle_stream_request(vertex_client=vertex_client, vertex_request=vertex_request)
            
            if isinstance(result, tuple):
                error_code, error_content = result
                return JSONResponse(content=error_content, status_code=error_code)
            else:
                return StreamingResponse(result, media_type='text/event-stream', headers={'X-Accel-Buffering': 'no'})
        else:
            return await handle_non_stream_request(vertex_client=vertex_client, vertex_request=vertex_request)
    except Exception as e:
        print(e)
        return JSONResponse(content={"error": str(e)}, status_code=500)
    finally:
        # 打印当前权重,重置文件变量
        debug_mode and global_selector.print_weights()
        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = ""