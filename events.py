import os
import typing
from enum import Enum
from typing import Optional

from pydantic import BaseModel

from utils import get_git_changes


class GitPlatform(Enum):
    """Git平台枚举
    
    支持的Git平台类型
    """
    GITHUB = "github.com"
    GITEE = "gitee.com"


from typing import Dict


class WebhookEvent(BaseModel):
    """Webhook事件模型

    统一的Webhook事件数据结构

    Attributes:
        platform: Git平台类型
        payload: 原始事件数据（JSON对象）
    """
    platform: GitPlatform
    repo_url: str
    before: str
    after: str
    payload: dict[str, typing.Any]


def process_github_webhook(payload: Dict[str, any]) -> Optional[WebhookEvent]:
    """处理GitHub webhook事件
    
    Args:
        payload: webhook负载数据
        
    Returns:
        WebhookEvent: 标准化的事件数据
    """
    if not payload:
        return None

    # 获取仓库链接
    full_name = payload.get("repository").get("full_name")
    repo_url = f"{GitPlatform.GITHUB.value}{'/'}{full_name}"
    # print(repo_url)

    return WebhookEvent(
        platform=GitPlatform.GITHUB,
        repo_url=repo_url,
        before=payload.get("before"),
        after=payload.get("after"),
        payload=payload
    )


def handle_webhook_event(event: WebhookEvent) -> None:
    """处理webhook事件
    
    这里实现具体的事件处理逻辑，比如：
    1. 更新本地仓库
    2. 触发代码审查
    3. 发送通知等
    
    Args:
        event: 标准化的webhook事件数据
    """
    # TODO: 实现具体的事件处理逻辑
    print(event.repo_url)
    print(event.before)
    print(event.after)
    changes = get_git_changes(event.repo_url, event.before, event.after)
    print(changes)
