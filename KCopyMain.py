#!/usr/bin/env python
# -*- encoding:utf-8 -*-
import time
import os
import sys
import json
import datetime
import fabric
from fabric import state

# fabric.state.output['status']=False
# fabric.state.output['aborts']=False
# fabric.state.output['warnings']=False
# fabric.state.output['running']=False
# fabric.state.output['stdout']=False
# fabric.state.output['stderr']=False

reload(sys)
sys.setdefaultencoding('utf-8')
import wx
import k_copy
from threading import RLock
from collections import OrderedDict
"""
生成GUI界面
"""

CONFIG_PATH = 'C:\KCopy.conf'


class MyApp(wx.App):
    pass

def merge_files(old_files, new_files):
    '''合并文件路径'''
    ignore_files = [f.strip('# ') for f in old_files if f.strip().startswith('#')]
    old_files = [f.strip('# ') for f in old_files]
    old_files.extend(new_files)
    od = OrderedDict()
    for f in old_files:
        od[f] = None
    old_files = ['#' + f if f in ignore_files else f for f in od.keys() if f]
    return old_files

class FileDropTarget(wx.FileDropTarget):
    """拖拽文件"""

    def __init__(self, files_box):
        wx.FileDropTarget.__init__(self)
        self.files_text_ctrl = files_box

    def OnDropFiles(self, x, y, fileNames):
        old_files = self.files_text_ctrl.GetValue().split('\n')
        self.files_text_ctrl.SetValue('\n'.join(merge_files(old_files,fileNames)))


def load_config(config_path):
    if os.path.exists(config_path):
        with open(config_path, 'r') as f:
            config = json.loads(f.read())
            if any([k not in config.keys() for k in k_copy.COFFIG_KEYS]):
                return None
            return config
    return None



class ConfigFrame(wx.Frame):
    """配置管理界面"""

    def __init__(self, parent, id):
        self.config_path = CONFIG_PATH
        self.k_copy = k_copy
        wx.Frame.__init__(self, parent, id, title=u'KCopy配置', pos=(600, 250), size=(940, 650))
        self.SetBackgroundColour('#f5f5f5')
        self.Bind(wx.EVT_CLOSE, self.hide_window)
        # panel = wx.Panel(self)
        config_keys = k_copy.COFFIG_KEYS
        config_names = k_copy.CONFIG_NAMES
        self.config_obj = dict()
        boxes = [self.get_config_box(config_keys[i], config_names[i]) for i in range(len(config_keys))]
        self.layout(boxes)

    def set_k_copy(self, k_copy):
        self.k_copy = k_copy

    def hide_window(self, event):
        self.Hide()

    def get_config_box(self, key, name):
        box = wx.BoxSizer(wx.HORIZONTAL)
        name = wx.StaticText(self, -1, name, size=(200, 30), style=wx.ALIGN_RIGHT)
        value = wx.TextCtrl(self, -1, size=(300, 30))
        box.Add(name, 0, wx.ALL)
        box.Add((10, 10), 0, wx.ALL)

        box.Add(value, 0, wx.ALL)
        self.config_obj[key] = (name, value)
        return box

    def layout(self, config_item_boxes):  # 3 合并网格
        box = wx.BoxSizer(wx.VERTICAL)
        for c_box in config_item_boxes:
            box.Add(c_box, 0, wx.ALL, 5)
        save_btn = wx.Button(self, -1, label=u'保存', size=(500, 30))
        box.Add(save_btn, 0, wx.ALIGN_CENTER | wx.ALL, 5)
        self.Bind(wx.EVT_BUTTON, self.save_config, save_btn)  # 绑定点击事件
        self.SetSizer(box)
        box.Fit(self)

    def save_config(self, event):
        """保存配置文件"""
        config = {key: value.GetValue() for key, (name, value) in self.config_obj.items()}
        if not config['client_root'].endswith('\\'):
            config['client_root'] = config['client_root'] + '\\'
        if not config['server_root'].endswith('/'):
            config['server_root'] = config['server_root'] + '/'
        if not config['server_bak_dir'].endswith('/'):
            config['server_bak_dir'] = config['server_bak_dir'] + '/'
        with open(self.config_path, 'w') as f:
            f.write(json.dumps(config))
        self.k_copy.set_config(config)
        self.hide_window(event)

    def load_config(self):
        config = load_config(self.config_path)
        if config:
            {value.SetValue(config.get(key, '')) for key, (name, value) in self.config_obj.items()}


class AboutFrame(wx.Frame):
    """介绍界面"""

    def __init__(self, parent, id):
        self.config_path = CONFIG_PATH
        self.k_copy = k_copy
        wx.Frame.__init__(self, parent, id, title=u'KCopy说明', pos=(600, 250), size=(1040, 650))
        self.SetBackgroundColour('#f5f5f5')
        self.Bind(wx.EVT_CLOSE, self.hide_window)
        from about import ABOUT_TEXT
        box = wx.BoxSizer(wx.VERTICAL)
        box.Add(wx.StaticText(self, -1, ABOUT_TEXT, size=(600, 700)), 0, wx.ALL, 5)
        self.SetSizer(box)
        box.Fit(self)

    def hide_window(self, event):
        self.Hide()


class MainFrame(wx.Frame):
    STATUS_ING = 1
    STATUS_SUC = 2
    STATUS_READY = 3
    STATUS_ERROR = 4

    def __init__(self, parent, id):
        self.logs = ''
        self.logs_lock = RLock()
        self.k_copy = k_copy.KCopy(self.update_log)
        wx.Frame.__init__(self, parent, 8, title=u'KCopy', pos=(500, 200), size=(940, 650))
        self.Bind(wx.EVT_CLOSE, self.close_window)
        self.SetBackgroundColour('#f5f5f5')
        # panel = wx.Panel(self)
        panel = self
        self.left_box = wx.BoxSizer(wx.VERTICAL)
        self.right_box = wx.BoxSizer(wx.VERTICAL)
        self.files_text_ctrl = wx.TextCtrl(panel, size=(800, 300), style=wx.TE_MULTILINE)
        dropTarget = FileDropTarget(self.files_text_ctrl)
        self.files_text_ctrl.SetDropTarget(dropTarget)
        # 第一列
        self.left_box.Add((10, 10), 0, wx.ALL)
        text = u'上传的文件路径（拖放文件到下面的输入框，如果想忽略一个文件，请在前面加#号）:'
        self.left_box.Add(wx.StaticText(panel, -1, text, size=(500, 20)), 0, wx.ALL)
        self.left_box.Add(self.files_text_ctrl, 0, wx.ALL)
        self.left_box.Add((10, 10), 0, wx.ALL)
        self.left_box.Add(wx.StaticText(panel, -1, u'日志：', size=(80, 20)), 0, wx.ALL)
        self.log_ctrl = wx.TextCtrl(panel, size=(800, 200), style=wx.TE_MULTILINE | wx.TE_READONLY)
        self.left_box.Add(self.log_ctrl, 0, wx.ALL)
        self.left_box.Add((10, 10), 0, wx.ALL)
        # 第二列
        self.upload_btn = wx.Button(panel, label=u'上传到服务器', size=(120, 45))
        self.upload_btn.SetForegroundColour('white')
        self.change_upload_btn_status(self.STATUS_READY)

        self.Bind(wx.EVT_BUTTON, self.upload, self.upload_btn)  # 绑定点击事件
        self.config_btn = wx.Button(panel, label=u'修改配置', size=(120, 45))
        self.Bind(wx.EVT_BUTTON, self.change_config, self.config_btn)  # 绑定点击事件
        self.about_btn = wx.Button(panel, label=u'使用教程', size=(120, 45))
        self.Bind(wx.EVT_BUTTON, self.show_about, self.about_btn)  # 绑定点击事件
        self.init_jump_btn = wx.Button(panel, label=u'初始化跳板机环境', size=(120, 45))
        self.Bind(wx.EVT_BUTTON, self.init_jump, self.init_jump_btn)  # 绑定点击事件
        self.get_change_file_btn = wx.Button(panel, label=u'获取文件', size=(120, 45))
        self.Bind(wx.EVT_BUTTON, self.get_change_file, self.get_change_file_btn)  # 绑定点击事件
        # upload_types = ['文件路径', '文件修改时间']
        # self.upload_type_raido = wx.RadioBox(panel, -1, "上传类型", (10, 10), wx.DefaultSize,
        #                                      upload_types, 1, wx.RA_SPECIFY_COLS)

        self.right_box.Add((10, 10), 0, wx.ALL)

        self.right_box.Add(self.about_btn, 0, wx.ALL, 10)
        self.right_box.Add(self.config_btn, 0, wx.ALL, 10)
        self.right_box.Add(self.init_jump_btn, 0, wx.ALL, 10)

        self.right_box.Add(wx.StaticText(panel, -1, u'此时间后修改的文件:', size=(120, 20)), 0, wx.LEFT, 10)
        self.upload_mtime = wx.TextCtrl(panel, -1, size=(130, 20))

        self.upload_mtime.SetValue(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        self.right_box.Add(self.upload_mtime, 0, wx.ALL, 10)
        self.right_box.Add(self.get_change_file_btn, 0, wx.ALL, 10)
        self.right_box.Add((10, 150), 0, wx.ALL)
        self.right_box.Add(self.upload_btn, 0, wx.ALL, 10)

        self.right_box.Add(wx.StaticText(panel, -1, u'Power By KevinLu', size=(120, 20), style=wx.ALIGN_RIGHT), 0,
                           wx.ALL)

        self.layout_box = wx.BoxSizer(wx.HORIZONTAL)

        self.layout_box.Add((10, 10), 0, wx.ALL)
        self.layout_box.Add(self.left_box, 0, wx.ALL)
        # self.layout_box.Add((10,10),0,wx.ALL)
        self.layout_box.Add(self.right_box, 0, wx.ALL)
        # self.layout_box.Add((10,10),0,wx.ALL)

        self.SetSizer(self.layout_box)
        self.layout_box.Fit(self)

        # wx.StaticText(panel, -1, u'日志：', (10, 360), size=(80, 20))

    def close_window(self, event):
        """关闭程序"""
        wx.Exit()
        # self.config_frame.Close(event)
        # self.about_frame.Close(event)
        # self.Close(event)

    def init_config_window(self):
        # 初始化配置窗口
        self.config_frame = ConfigFrame(parent=None, id=5)
        self.config_frame.set_k_copy(self.k_copy)
        config = load_config(CONFIG_PATH)
        if not config:
            self.alarm(u'找不到配置文件，请重新设置配置')
            self.change_config(None)
        else:
            self.k_copy.set_config(config)
        self.about_frame = AboutFrame(parent=None, id=5)

    def get_change_file(self, event):
        """获取在某个时间后，被修改的文件"""
        mtime_str = self.upload_mtime.GetValue()
        try:
            dt = datetime.datetime.strptime(mtime_str, '%Y-%m-%d %H:%M:%S')
        except ValueError:
            self.alarm(u'时间不符合格式%s' % '%Y-%m-%d %H:%M:%S')
            return
        mtime = int(time.mktime(dt.timetuple()))
        new_files = self.get_change_files(self.k_copy.config['client_root'], mtime)
        if not new_files:
            self.alarm(u'找不到文件')
        old_files = self.files_text_ctrl.GetValue().split('\n')
        new_files=merge_files(old_files,new_files)
        self.files_text_ctrl.SetValue('\n'.join(new_files))
        self.upload_mtime.SetValue(datetime.datetime.now().strftime('%Y-%m-%d %X'))

    def show_about(self, event):
        self.about_frame.Show(True)

    def update_log(self, new_log):
        """刷新日志"""
        # self.logs_lock.acquire()
        if self.logs:
            self.logs += '\n'
        self.logs = self.logs + new_log
        self.log_ctrl.SetValue(self.logs)
        self.log_ctrl.Update()
        self.log_ctrl.ScrollLines(len(self.logs.split('\n')))
        # self.logs_lock.release()

    def get_change_files(self, root, timestamp):
        """获取root目录里面，修改时间在timestamp之后的绝对文件路径列表"""
        file_list = []
        for root, dirs, files in os.walk(root):
            for file_ in files:
                file_path = os.path.join(root, file_)
                mtime = os.path.getmtime(file_path)
                if mtime > timestamp:
                    file_list.append(file_path)
        return file_list

    def change_upload_btn_status(self, status):
        """修改上传按钮的状态"""
        bg_color, text = {
            self.STATUS_READY: ('#5bc0de', '上传到服务器'),
            self.STATUS_ING: ('#f0ad4e', '上传中……'),
            self.STATUS_SUC: ('#5cb85c', '上传完成'),
            self.STATUS_ERROR: ('#d9534f', '上传错误'),
        }.get(status)

        self.upload_btn.SetBackgroundColour(bg_color)
        self.upload_btn.SetLabelText(text)
        self.upload_btn.Update()

    def upload(self, event):
        """上传文件到服务器"""
        files = [f.strip() for f in self.files_text_ctrl.GetValue().split('\n') if
                 f.strip() and not f.strip().startswith('#')]
        if not files:
            self.alarm('没有需要上传的文件')
            return
        self.change_upload_btn_status(self.STATUS_ING)
        self.logs = ''
        self.update_log('开始上传')
        invalid_files = self.k_copy.copy_files(files)
        if invalid_files and isinstance(invalid_files, list):
            self.update_log('上传错误')
            content = '文件：%s 不在根目录%s中' % (';'.join(invalid_files), self.k_copy.config['client_root'])
            self.alarm(content)
            self.change_upload_btn_status(self.STATUS_ERROR)
        elif invalid_files and isinstance(invalid_files, int):
            self.change_upload_btn_status(self.STATUS_ERROR)
        else:
            self.change_upload_btn_status(self.STATUS_SUC)

        time.sleep(3)
        self.change_upload_btn_status(self.STATUS_READY)
        return

    def change_config(self, event):
        """修改配置"""
        self.config_frame.Show(True)
        self.config_frame.load_config()

    def init_jump(self, event):
        """初始化跳板机环境"""
        try:
            if self.k_copy.init_jump_file(): self.alarm(u'初始化成功')
        except:
            import  traceback
            self.alarm(traceback.format_exc())

    def alarm(self, content, title='警告'):
        '''
        弹出消息对话框
        :param title:
        :param content:
        :return:
        '''
        dlg = wx.MessageDialog(None, content, title, wx.OK | wx.ICON_QUESTION)
        if dlg.ShowModal() == wx.OK:
            dlg.Destroy()

    def confirm(self, content, title='确认'):
        '''
        弹出消息确认框
        :param title:
        :param content:
        :return:
        '''
        dlg = wx.MessageDialog(None, content, title, wx.OK | wx.CANCEL | wx.ICON_QUESTION)
        result = dlg.ShowModal()
        dlg.Destroy()
        return result == 5100


def main():
    app = MyApp()
    frame = MainFrame(parent=None, id=-1)
    frame.Show(True)
    frame.init_config_window()
    app.MainLoop()


if __name__ == '__main__':
    # import win32api, win32gui
    # ct = win32api.GetConsoleTitle()
    # hd = win32gui.FindWindow(0,ct)
    # win32gui.ShowWindow(hd,0)
    # import os,subprocess
    # if os.name == 'nt':
    #     startupinfo = subprocess.STARTUPINFO()
    #     startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    #     startupinfo.wShowWindow = subprocess.SW_HIDE
    # else:
    #     startupinfo = None
    # subprocess.Popen(main, startupinfo=startupinfo)
    main()
