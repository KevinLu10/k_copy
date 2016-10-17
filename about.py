# encoding=utf8
ABOUT_TEXT='''一、功能介绍
机器角色：
1. 客户端
2. 跳板机
3. 服务端
KCopy功能：把客户端中的文件，复制到跳板机，然后从跳板机复制到服务端

二、修改配置
使用前需要点击“修改配置”按钮进行配置设置。需要设置的配置有：
跳板机域名：格式为USER@HOST:PORT，例如kevinlu@192.168.1.1:22
跳板机密码：登录到跳板机的密码
服务器用户名：登录服务器的用户名，例如kevinlu
服务器域名：服务器的IP地址，例如192.168.10.1
服务器密码：服务器用户名对应的密码
服务器端口：登录到服务器的端口，例如22
客户端文件根路径：客户机的文件夹路径，复制到服务端的文件，必须在改文件夹里面
服务器文件根路径：客户机的文件夹对应在服务端的文件夹
服务器文件备份目录：服务器的备份目录，如果复制的时候，服务器一样同样路径的文件，KCopy会将该文件备份在该目录下，文件名：原文件名.时间日期.随机数

假如：
客户端文件根路径=E:/work/
服务器文件根路径=/data/work/
上传的文件路径中填写：
E:/work/test.txt
那么KCopy会将该文件上传到服务器中的路径/data/work/test.txt

三、初始化跳板机环境
点击按钮“初始化跳板机环境”KCopy会在跳板机的家目录下建立工作目录k_copy

四、上传文件
在“上传的文件路径”输入框中，填入需要上传的文件路径（在客户端的路径）。
然后点击“上传到服务器”。如果想忽略一个文件，请在前面加#号。
可以使用拖动文件的方式，快速输入文件路径。
可以通过“获取文件”按钮来获取在指定时间后被修改过的文件。

'''
EXPECT_TPL='''
#!/usr/bin/expect
set remote_user [lindex $argv 0]
set remote_host [lindex $argv 1]
set remote_port [lindex $argv 2]
set remote_pwd [lindex $argv 3]
set local_path [lindex $argv 4]
set remote_path [lindex $argv 5]
set remote_bak_path [lindex $argv 6]
set remote_bak_dir [lindex $argv 7]

spawn ssh -l $remote_user  $remote_host  -p $remote_port
expect "*password:"
send "$remote_pwd\r"
expect "*$ "
send "ls $remote_path\n"
expect {
    "No such file or directory" {

    }
    "*$ " {
         send "mkdir -p $remote_bak_dir\n"
         expect "*$ "
         send "cp $remote_path $remote_bak_path\n"
         expect "*$ "
    }
}
send "exit\r"
expect eof

spawn /usr/bin/scp -P$remote_port  $local_path  $remote_user@$remote_host:$remote_path
expect "*password:"
send "$remote_pwd\r"
expect "*$ "
'''
if __name__ == '__main__':
    pass