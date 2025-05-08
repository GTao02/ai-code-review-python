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
        print(f"仓库目录不存在: {repo_dir}")
        return None
        
    try:
        repo = Repo(repo_dir)
        
        # 确保提交哈希存在
        try:
            before_commit = repo.commit(before)
            after_commit = repo.commit(after)
        except Exception as e:
            print(f"提交哈希不存在: {e}")
            return None
        
        # 获取两个提交之间的差异
        changes = {
            'files_changed': [],
            'total_additions': 0,
            'total_deletions': 0
        }
        
        # 使用 GitPython 获取提交之间的差异
        diffs = repo.git.diff(before, after, name_status=True)
        changed_file_list = []
        
        # 解析变更的文件列表
        for line in diffs.split('\n'):
            if not line.strip():
                continue
                
            parts = line.strip().split('\t')
            if len(parts) >= 2:
                change_type = parts[0]
                file_path = parts[1]
                changed_file_list.append((change_type, file_path))
        
        # 获取每个文件的详细变更
        for change_type, file_path in changed_file_list:
            try:
                # 获取文件的详细差异
                file_diff = repo.git.diff(before, after, file_path, unified=0)
                
                # 解析文件差异
                changes_content = []
                total_additions = 0
                total_deletions = 0
                
                for line in file_diff.split('\n'):
                    if line.startswith('+') and not line.startswith('+++'):
                        # 添加的行
                        if not (line.startswith('+++ ') or line.startswith('+@@')):
                            changes_content.append({
                                'type': 'addition',
                                'content': line[1:]
                            })
                            total_additions += 1
                    elif line.startswith('-') and not line.startswith('---'):
                        # 删除的行
                        if not (line.startswith('--- ') or line.startswith('-@@')):
                            changes_content.append({
                                'type': 'deletion',
                                'content': line[1:]
                            })
                            total_deletions += 1
                
                # 添加到变更列表
                file_change = {
                    'file_path': file_path,
                    'change_type': change_type,
                    'additions': total_additions,
                    'deletions': total_deletions,
                    'changes': changes_content,
                    'diff': file_diff
                }
                
                changes['files_changed'].append(file_change)
                changes['total_additions'] += total_additions
                changes['total_deletions'] += total_deletions
                
            except Exception as e:
                print(f"处理文件 {file_path} 变更时出错: {e}")
                import traceback
                traceback.print_exc()
        
        return changes
    except Exception as e:
        print(f"获取git变更失败: {e}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == '__main__':
    # 测试用例
    # links = [
    #     "https://github.com/GTao02/Al-Code-Review-Backend.git",
    #     "git@gitee.com:g-tao/automl.git"
    # ]
    # for link in links:
    #     clone_git_repository(link)
    #     # 测试更新仓库
    #     update_result = update_git_repository(link)
    #     print(f"更新仓库结果: {update_result}")

    # 测试 get_git_changes 方法
    changes = get_git_changes(
        "github.com/GTao02/Al-Code-Review-Backend",
        "25358c70e211cefadf12796449dfb0c5545417ba",  # 开始提交的hash
        "f6d0b801ffe96f7ef7654338d7e00f599ed3acda"   # 结束提交的hash
    )
    # print(changes)
    if changes:
        print(f"变更文件数: {changes['files_changed']}")
        print(f"总添加行数: {changes['total_additions']}")
        print(f"总删除行数: {changes['total_deletions']}")
