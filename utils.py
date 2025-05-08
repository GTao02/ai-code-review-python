import os.path
import re

from git import Repo

from config import repository_dir_path


def extract_platform_and_username(git_url):
    # 匹配 HTTPS 格式: https://platform.com/username/repo.git
    https_match = re.match(r'https://([^/]+)/([^/]+)/([^/]+)(\.git)?', git_url)
    if https_match:
        platform = https_match.group(1)
        username = https_match.group(2)
        repo = https_match.group(3).replace('.git', '')
        return f"{platform}{os.sep}{username}{os.sep}{repo}"

    # 匹配 SSH 格式: git@platform.com:username/repo.git
    ssh_match = re.match(r'git@([^:]+):([^/]+)/([^/]+)(\.git)?', git_url)
    if ssh_match:
        platform = ssh_match.group(1)
        username = ssh_match.group(2)
        repo = ssh_match.group(3).replace('.git', '')
        return f"{platform}{os.sep}{username}{os.sep}{repo}"

    # 如果都不是合法的 Git 链接，返回 None
    return None


def clone_git_repository(git_url):
    """
    克隆git仓库
    :param git_url: git仓库地址
    :return:
    """
    platform_and_username = extract_platform_and_username(git_url)
    if platform_and_username:
        repo_dir = os.path.join(repository_dir_path, platform_and_username)
        print(repo_dir)
        # 执行克隆操作
        try:
            Repo.clone_from(git_url, repo_dir)
        except Exception as e:
            print(f"克隆失败: {e}")


def update_git_repository(repo_dir):
    """
    更新git仓库
    :param repo_dir: 仓库目录
    :return: bool, 更新是否成功
    """
        
    repo_dir = os.path.join(repository_dir_path, repo_dir)
    if not os.path.exists(repo_dir):
        return False
        
    try:
        repo = Repo(repo_dir)
        origin = repo.remotes.origin
        origin.pull()
        return True
    except Exception as e:
        print(f"更新仓库失败: {e}")
        return False


def get_git_changes(repo_url, before, after):
    """
    获取指定提交范围之间的git变更内容
    :param repo_url: git仓库地址
    :param before: 开始提交的hash值
    :param after: 结束提交的hash值
    :return: dict, 包含变更信息的字典，如果失败则返回None
    """
    # 先更新仓库
    update_git_repository(repo_url)
    repo_dir = os.path.join(repository_dir_path, repo_url)
    if not os.path.exists(repo_dir):
        return None
        
    try:
        repo = Repo(repo_dir)
        # 获取两个提交之间的差异
        diff = repo.commit(after).diff(repo.commit(before))
        
        changes = {
            'files_changed': [],
            'total_additions': 0,
            'total_deletions': 0
        }
        
        for item in diff:
            file_change = {
                'file_path': item.a_path,
                'change_type': item.change_type,
                'additions': item.stats.get('insertions', 0),
                'deletions': item.stats.get('deletions', 0)
            }
            changes['files_changed'].append(file_change)
            changes['total_additions'] += file_change['additions']
            changes['total_deletions'] += file_change['deletions']
            
        return changes
    except Exception as e:
        print(f"获取git变更失败: {e}")
        return None


if __name__ == '__main__':
    # 测试用例
    links = [
        "https://github.com/GTao02/Al-Code-Review-Backend.git",
        "git@gitee.com:g-tao/automl.git"
    ]
    for link in links:
        clone_git_repository(link)
        # 测试更新仓库
        update_result = update_git_repository(link)
        print(f"更新仓库结果: {update_result}")

    # 测试 get_git_changes 方法
    changes = get_git_changes(
        "https://github.com/username/repo.git",
        "abc123",  # 开始提交的hash
        "def456"   # 结束提交的hash
    )
    if changes:
        print(f"变更文件数: {len(changes['files_changed'])}")
        print(f"总添加行数: {changes['total_additions']}")
        print(f"总删除行数: {changes['total_deletions']}")
