import os.path
from pathlib import Path

repository_dir_path = os.path.join(Path(__file__).parent, "data")

if __name__ == '__main__':
    print(repository_dir_path)
