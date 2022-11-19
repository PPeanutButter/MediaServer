import os.path
import platform
import shutil
from tools import file_size_desc, path_join, name_from_path


class DiskManager:
    _disk_manager_dir = "_disk_manager_dir"
    _preview_cache_dir = "_preview_cache_dir"
    _bookmark_cache_dir = "_bookmark_cache_dir"
    # 树莓派4B有两个USB2.0口，降低其优先级
    # 3.0, 3.0, 2.0, 2.0
    _disk_weight = [3.0, 3.0, 1.0, 1.0]

    def __init__(self, disk_list: list):
        # 磁盘绝对路径数组，通过终端传参
        self.disk_list = disk_list
        self.disk_names = []
        if os.path.exists(self._disk_manager_dir):
            shutil.rmtree(self._disk_manager_dir)
        os.mkdir(self._disk_manager_dir)
        if not os.path.exists(self._preview_cache_dir):
            os.mkdir(self._preview_cache_dir)
        if not os.path.exists(self._bookmark_cache_dir):
            os.mkdir(self._bookmark_cache_dir)
        self.root = self._disk_manager_dir
        for path in self.disk_list:
            disk_name = name_from_path(path)
            self.disk_names.append(disk_name)
            if platform.system() == 'Windows':
                pass
            else:
                os.system(f'ln -s {path} {path_join(self._disk_manager_dir, disk_name)}')

    def listdir(self, path) -> list:
        li = []
        for disk in (self.disk_names if path == '/' else [path[1:]]):
            if os.path.exists(path_join(self.root, disk)):
                a = os.listdir(path_join(self.root, disk))
                a.sort()
                for f in a:
                    li.append(path_join(disk, f))
        return li

    def get_max_avl_disk(self, season_name):
        _max = (-1, '')
        for i, path in enumerate(self.disk_list):
            # 如果之前已经创建过了, 则导流到原来目录
            if os.path.exists(os.path.join(path, season_name)):
                return name_from_path(path)
            total, used, free = shutil.disk_usage(path)
            free = free * self._disk_weight[i]
            if free > _max[0]:
                _max = (free, name_from_path(path))
        return _max[1]

    def __print__(self):
        print('=======DiskManager=======')
        for disk in self.disk_list:
            total, used, free = shutil.disk_usage(disk)
            print(disk, '\t', file_size_desc(used), 'used\t', file_size_desc(free), 'free')
        print('=======DiskManager=======')

    @property
    def preview_cache_dir(self):
        return self._preview_cache_dir

    @property
    def bookmark_cache_dir(self):
        return self._bookmark_cache_dir

    @property
    def disk_manager_dir(self):
        return self._disk_manager_dir
