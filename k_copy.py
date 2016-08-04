# encoding=utf8
import os
import time
import random
import string
from datetime import datetime
from fabric.api import run, env, put
from fabric import state

state.output['everything'] = False  # 设置不输出任何日志
# 三种机器：
# 1. 客户端，client
# 2. 跳板机 jump
# 3. 服务端 server
# 功能：把客户端中的文件，复制到跳板机，然后从跳板机复制到服务端
# 客户机复制到跳板机，使用fabric的put，跳板机复制到服务器使用scp,使用expect来自动输入密码
# 常量
# JUMP_HOST = 'kevinlu@10.16.2.64:32200'
# JUMP_PASSWORD = 'seafood.2880'
# SERVER_HOST = 'anchor@10.1.16.218'
# SERVER_PASSWORD = 'anchor'
# SERVER_PORT = '32200'
#
# CLIENT_ROOT = 'E:\\Sleep\\'
# CLIENT_ROOT = 'E:\\my_demo\\sleep_client\\demo\\'

# SERVER_ROOT = '/data1/anchor/SleepBackend/'
# SERVER_ROOT = '/data1/anchor/lujianxing/demo/'
JUMP_COPY_ROOT = '~/k_copy/'
COPY_SCRIPT_PATH = '%s%s' % (JUMP_COPY_ROOT, 'copy.sh')

COFFIG_KEYS = ['jump_host', 'jump_password', 'server_user', 'server_host', 'server_password', 'server_port',
               'client_root',
               'server_root', 'server_bak_dir']
CONFIG_NAMES = ['跳板机域名（USER@HOST:PORT）', '跳板机密码', '服务器用户名', '服务器域名',
                '服务器密码', '服务器端口', '客户端文件根路径(E:\Sleep\)', '服务器文件根路径(/data1/Sleep/)', '服务器文件备份目录(/data1/SleepBak)']


class KCopy():
    def __init__(self, update_log_func):
        self.update_log_func = update_log_func
        self.config = None

    def set_config(self, config):
        self.config = config
        env.host_string = self.config['jump_host']
        env.password = self.config['jump_password']

    def random_str(self, length):
        """生成随机字符串"""
        return ''.join(random.sample(string.ascii_letters + string.digits, length))

    def copy_file(self, rel_path):
        """复制一个文件，返回是否成功"""

        client_path = os.path.join(self.config['client_root'], rel_path).replace('/', os.sep)
        log = '[%s]START COPY %s' % (datetime.now().strftime('%X'), client_path)
        print log
        self.update_log_func(log)
        server_path = '%s%s' % (self.config['server_root'], rel_path)
        try:
            is_suc, reason = self.client_copy_to_server(client_path, server_path)
        except Exception, e:
            import traceback
            self.update_log_func(traceback.format_exc())
            is_suc, reason = (0, e)
        log = '[%s][%s] COPY %s %s' % (
            datetime.now().strftime('%X'), 'SUCCESS' if is_suc else 'FAIL', client_path, '' if is_suc else reason)
        print log
        self.update_log_func(log)
        return is_suc

    def client_copy_to_server(self, client_path, server_path):
        """从客户机复制文件到服务器，返回是否成功"""

        jump_filename = '%s.%s.%s' % (
            os.path.basename(client_path), datetime.now().strftime('%Y%m%d%H%M%S'), self.random_str(4))
        jump_path = '%s%s%s' % (JUMP_COPY_ROOT, 'tmp_file/', jump_filename)
        is_success = 0
        reason = 'copy to server fail'
        server_bak_path = '%s%s' % (self.config['server_bak_dir'], jump_filename)
        if not put(client_path, jump_path).failed:
            expect_cmd = ' '.join(['expect',
                                   COPY_SCRIPT_PATH, self.config['server_user'], self.config['server_host'],
                                   self.config['server_port'],
                                   self.config['server_password'], jump_path, server_path, server_bak_path,
                                   self.config['server_bak_dir']])
            is_success = not run(expect_cmd).failed
        else:
            reason = 'copy to jump fail'

        return is_success, reason

    def copy_files(self, files):
        """上传多个文件，如果文件不合法，返回不合法的文件列表，否则返回None"""
        start = time.time()
        invalid_file = []
        valid_file = []
        for file_ in files:
            if not file_.startswith(self.config['client_root']):
                invalid_file.append(file_)
            else:
                valid_file.append(file_.split(self.config['client_root'])[1].replace(os.sep, '/'))
        if invalid_file:
            return invalid_file
        suc_num = len([1 for file_ in valid_file if self.copy_file(file_)])
        log = '上传完成，成功%d个，失败%d个，用时%.2fs' % (suc_num, len(valid_file) - suc_num, time.time() - start)
        self.update_log_func(log)
        return len(valid_file) - suc_num

    def init_jump_file(self):
        """初始化跳板机的环境"""
        import about
        expect_tpl_file = 'C:\\expect_tpl.%s' % self.random_str(10)
        with open(expect_tpl_file, 'w') as f:
            f.write(about.EXPECT_TPL)
        run('mkdir -p %stmp_file' % JUMP_COPY_ROOT)
        put(expect_tpl_file, COPY_SCRIPT_PATH)
        os.remove(expect_tpl_file)
        return True


def get_change_files(root, timestamp):
    """获取root目录里面，修改时间在timestamp之后的绝对文件路径列表"""
    file_list = []
    for root, dirs, files in os.walk(root):
        for file_ in files:
            file_path = os.path.join(root, file_)
            mtime = os.path.getmtime(file_path)
            if mtime > timestamp:
                print mtime
                file_list.append(mtime)


if __name__ == '__main__':
    k = KCopy(lambda x: 1)
    valid_files = ['E:\\SleepBackend\\trunk\\test.txt']
    print k.copy_files(valid_files)
