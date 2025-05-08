from fastapi import FastAPI, HTTPException, Header, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os
import hmac
import hashlib
from pydantic import BaseModel
from typing import Dict, Optional
from contextlib import asynccontextmanager

from events import process_github_webhook, handle_webhook_event

from utils import clone_git_repository, update_git_repository

@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理
    
    处理应用启动和关闭事件
    """
    # 启动事件处理
    print("\n" + "=" * 50)
    print("API文档已就绪，请访问以下链接：")
    print("Swagger UI: http://127.0.0.1:8000/docs")
    print("ReDoc: http://127.0.0.1:8000/redoc")
    print("=" * 50 + "\n")
    
    yield  # 应用运行期间
    
    # 关闭事件处理（如果需要）

app = FastAPI(
    title="Git仓库管理API",
    description="提供Git仓库克隆和更新的RESTful API接口",
    version="1.0.0",
    lifespan=lifespan
)


frontend_dir = os.path.join(os.path.dirname(__file__), "frontend")
if os.path.exists(frontend_dir):
    app.mount("/static", StaticFiles(directory=frontend_dir), name="static")

@app.get("/", include_in_schema=False)
async def read_index():
    index_path = os.path.join(frontend_dir, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    raise HTTPException(status_code=404, detail="Index.html not found")

class RepositoryReq(BaseModel):
    """Git仓库请求模型
    
    Attributes:
        git_url: Git仓库的URL地址，支持HTTPS和SSH格式
    """
    git_url: str
    
    class Config:
        schema_extra = {
            "example": {
                "git_url": "https://github.com/username/repository.git"
            }
        }

class RepositoryResponse(BaseModel):
    """API响应模型
    
    Attributes:
        message: 操作结果消息
        status: 操作状态
    """
    message: str
    status: str

@app.post(
    "/repository/clone",
    response_model=RepositoryResponse,
    tags=["仓库管理"],
    summary="克隆Git仓库",
    description="克隆指定的Git仓库到本地存储",
    response_description="仓库克隆操作的结果"
)
async def clone_repository(repo: RepositoryReq) -> Dict[str, str]:
    """克隆Git仓库到本地存储
    
    Args:
        repo: Git仓库信息，包含仓库URL
        
    Returns:
        Dict[str, str]: 包含操作结果的响应信息
        
    Raises:
        HTTPException: 当克隆操作失败时抛出500错误
    """
    try:
        clone_git_repository(repo.git_url)
        return {"message": "仓库克隆成功", "status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"仓库克隆失败: {str(e)}")

@app.get(
    "/repositories",
    tags=["仓库管理"],
    summary="获取仓库列表",
    description="获取data目录下所有已克隆的仓库列表",
    response_description="仓库列表"
)
async def list_repositories():
    """获取data目录下所有已克隆的仓库列表"""
    data_dir = os.path.join(os.path.dirname(__file__), "data")
    repositories = []
    if os.path.exists(data_dir):
        for root, dirs, files in os.walk(data_dir):
            if '.git' in dirs:
                relative_path = os.path.relpath(root, data_dir)
                repositories.append(relative_path.replace('\\', '/'))
                dirs[:] = [] 
    return repositories


@app.post(
    "/repository/update",
    response_model=RepositoryResponse,
    tags=["仓库管理"],
    summary="更新Git仓库",
    description="更新本地存储中的Git仓库到最新版本",
    response_description="仓库更新操作的结果"
)
async def update_repository(repo: RepositoryReq) -> Dict[str, str]:
    """更新本地Git仓库
    
    Args:
        repo: Git仓库信息，包含仓库URL
        
    Returns:
        Dict[str, str]: 包含操作结果的响应信息
        
    Raises:
        HTTPException: 当仓库不存在时抛出404错误，更新失败时抛出500错误
    """
    try:
        result = update_git_repository(repo.git_url)
        if result:
            return {"message": "仓库更新成功", "status": "success"}
        else:
            raise HTTPException(status_code=404, detail="仓库不存在或更新失败")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"仓库更新失败: {str(e)}")


@app.post(
    "/webhook/github",
    tags=["Webhook"],
    summary="GitHub Webhook接收器",
    description="接收并处理GitHub的webhook推送事件",
    response_description="webhook处理结果"
)
async def github_webhook(
    payload: str,
) -> Dict[str, str]:
    """处理GitHub webhook请求
    
    Args:
        payload: webhook回调的消息
        
    Returns:
        Dict[str, str]: 处理结果
        
    Raises:
        HTTPException: 当请求验证失败或处理出错时抛出相应的错误:
    """
    try:
        event = process_github_webhook(payload)
        print(event)
        if event:
            handle_webhook_event(event)
            return {"message": "webhook事件处理成功", "status": "success"}
        else:
            raise HTTPException(status_code=400, detail="无效的事件数据")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"处理webhook事件失败: {str(e)}")



def main():
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)

if __name__ == "__main__":
    main()