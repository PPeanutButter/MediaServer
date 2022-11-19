# Starts from 0 setup

> 使用刷机工具刷机后...


## 1.磁盘共享服务
> 将树莓派本地硬盘挂载到下载服务器上

### 安装 Samba

`sudo apt-get install samba samba-common-bin`

### 配置 Samba

`sudo gedit /etc/samba/smb.conf`，在文件末尾加上

```txt
[NAS]
    comment = NAS Hard Driver
    path = /media/pi/NAS500
    valid users = pi
    read only = no
    create mask = 0777
    directory mask = 0777
    guest ok = no
    browseable = yes
```

### 添加 Samba 用户并重启服务

```
sudo smbpasswd -a pi
sudo samba restart
```

## 2.开机后台自启服务

### 安装screen

`sudo apt-get install screen vim`

### 保存screen.sh

```bash
#!/bin/bash

# dir name cmd
run_screen()
{
	screen -dmS $2
	#screen -x -S $2 -p 0 -X stuff "cd $1"
	#screen -x -S $2 -p 0 -X stuff '\n'

	#screen -x -S $2 -p 0 -X stuff "$3"
	#screen -x -S $2 -p 0 -X stuff '\n'
	screen_exe "$2" "cd $1"
	screen_exe "$2" "$3"
}

# name cmd
screen_exe()
{
	screen -x -S $1 -p 0 -X stuff "$2"
	screen -x -S $1 -p 0 -X stuff '\n'
}

run_screen "/home/pi/MediaServer" "NAS" "sudo python3 app.py /media/pi/NAS500"
# run_screen "cd to path" "name" "action"
```

### 添加自启

`sudo vim /etc/rc.local` 

```bash
#!/bin/sh -e
#
# rc.local
#
# This script is executed at the end of each multiuser runlevel.
# Make sure that the script will "exit 0" on success or any other
# value on error.
#
# In order to enable or disable this script just change the execution
# bits.
#
# By default this script does nothing.

# Print the IP address
_IP=$(hostname -I) || true
if [ "$_IP" ]; then
  printf "My IP address is %s\n" "$_IP"
fi
sudo sh home/pi/MediaServer/screen.sh
exit 0
```

## 3.迅雷云盘代理

> 拦截迅雷的下载请求，发送到本地aria2

### 安装依赖

```bash
sudo apt-get install aria2 mitmproxy
touch aria2.session
```

### 配置手机端

```bash
# 运行mitmproxy后设置代理到树莓派8080
# 访问mitm.it
# 下载证书
# 安装
mv -f /data/misc/user/0/cacerts-added/* /system/etc/security/cacerts/
```

### 配置aria2

```bash
## '#'开头为注释内容, 选项都有相应的注释说明, 根据需要修改 ##
## 被注释的选项填写的是默认值, 建议在需要修改时再取消注释  ##

## 文件保存相关 ##

# 文件的保存路径(可使用绝对路径或相对路径), 默认: 当前启动位置
dir=/media/pi/NAS500/Download
# 启用磁盘缓存, 0为禁用缓存, 需1.16以上版本, 默认:16M
disk-cache=512M
# 文件预分配方式, 能有效降低磁盘碎片, 默认:prealloc
# 预分配所需时间: none < falloc ? trunc < prealloc
# falloc和trunc则需要文件系统和内核支持
# NTFS建议使用falloc, EXT3/4建议trunc, MAC 下需要注释此项
file-allocation=falloc
# 断点续传
continue=true

## 下载连接相关 ##

# 最大同时下载任务数, 运行时可修改, 默认:5
max-concurrent-downloads=2
# 同一服务器连接数, 添加时可指定, 默认:1
max-connection-per-server=8
# 最小文件分片大小, 添加时可指定, 取值范围1M -1024M, 默认:20M
# 假定size=10M, 文件为20MiB 则使用两个来源下载; 文件为15MiB 则使用一个来源下载
min-split-size=64M
# 单个任务最大线程数, 添加时可指定, 默认:5
split=4
# 整体下载速度限制, 运行时可修改, 默认:0
#max-overall-download-limit=0
# 单个任务下载速度限制, 默认:0
#max-download-limit=0
# 整体上传速度限制, 运行时可修改, 默认:0
#max-overall-upload-limit=0
# 单个任务上传速度限制, 默认:0
#max-upload-limit=0
# 禁用IPv6, 默认:false
#disable-ipv6=true
# 连接超时时间, 默认:60
#timeout=60
# 最大重试次数, 设置为0表示不限制重试次数, 默认:5
max-tries=5
# 设置重试等待的秒数, 默认:0
retry-wait=30
check-certificate=false

## 进度保存相关 ##

# 从会话文件中读取下载任务
input-file=/home/pi/Program/MediaServer/aria2.session
# 在Aria2退出时保存`错误/未完成`的下载任务到会话文件
save-session=/home/pi/Program/MediaServer/aria2.session
# 定时保存会话, 0为退出时才保存, 需1.16.1以上版本, 默认:0
save-session-interval=60

## RPC相关设置 ##

# 启用RPC, 默认:false
enable-rpc=true
# 允许所有来源, 默认:false
rpc-allow-origin-all=true
# 允许非外部访问, 默认:false
rpc-listen-all=true
# 事件轮询方式, 取值:[epoll, kqueue, port, poll, select], 不同系统默认值不同
#event-poll=select
# RPC监听端口, 端口被占用时可以修改, 默认:6800
#rpc-listen-port=6800
# 设置的RPC授权令牌, v1.18.4新增功能, 取代 --rpc-user 和 --rpc-passwd 选项
rpc-secret=0930
# 设置的RPC访问用户名, 此选项新版已废弃, 建议改用 --rpc-secret 选项
#rpc-user=<USER>
# 设置的RPC访问密码, 此选项新版已废弃, 建议改用 --rpc-secret 选项
#rpc-passwd=<PASSWD>
# 是否启用 RPC 服务的 SSL/TLS 加密,
# 启用加密后 RPC 服务需要使用 https 或者 wss 协议连接
#rpc-secure=true
# 在 RPC 服务中启用 SSL/TLS 加密时的证书文件,
# 使用 PEM 格式时，您必须通过 --rpc-private-key 指定私钥
#rpc-certificate=/path/to/certificate.pem
# 在 RPC 服务中启用 SSL/TLS 加密时的私钥文件
#rpc-private-key=/path/to/certificate.key

## BT/PT下载相关 ##

# 当下载的是一个种子(以.torrent结尾)时, 自动开始BT任务, 默认:true
#follow-torrent=true
# BT监听端口, 当端口被屏蔽时使用, 默认:6881-6999
listen-port=51413
# 单个种子最大连接数, 默认:55
#bt-max-peers=55
# 打开DHT功能, PT需要禁用, 默认:true
enable-dht=false
# 打开IPv6 DHT功能, PT需要禁用
#enable-dht6=false
# DHT网络监听端口, 默认:6881-6999
#dht-listen-port=6881-6999
# 本地节点查找, PT需要禁用, 默认:false
#bt-enable-lpd=false
# 种子交换, PT需要禁用, 默认:true
enable-peer-exchange=false
# 每个种子限速, 对少种的PT很有用, 默认:50K
#bt-request-peer-speed-limit=50K
# 客户端伪装, PT需要
peer-id-prefix=-TR2770-
user-agent=Transmission/2.77
peer-agent=Transmission/2.77
# 当种子的分享率达到这个数时, 自动停止做种, 0为一直做种, 默认:1.0
seed-ratio=0
# 强制保存会话, 即使任务已经完成, 默认:false
# 较新的版本开启后会在任务完成后依然保留.aria2文件
#force-save=false
# BT校验相关, 默认:true
#bt-hash-check-seed=true
# 继续之前的BT任务时, 无需再次校验, 默认:false
bt-seed-unverified=true
# 保存磁力链接元数据为种子文件(.torrent文件), 默认:false
bt-save-metadata=true
```

## 4.Python 依赖包

```bash
# requirements.txt
Flask >= 2.0.2
ffmpeg
tensorboard
tensorboardX
pyaria2
```

## 5.Whats more.

> see readme.md

