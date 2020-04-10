import socket
import sys
from pathlib import Path
import hashlib
import zipfile
# 发送方
# 使用示例：
# python3 E:\Project_for_VS\FileTransport-master\src\client\client.py E:\background 193.112.59.84 1234
# argv[1]: abcd 可以是任意文件或文件夹的相对或绝对路径
# argv[2]: 123.123.123.123 是发送目的地的地址
# argv[3]: 1234 是目的地端口

# f 为文件到提供的文件夹的相对目录，用于传输报头
# source 为提供的文件夹，用于读取文件
########


def GetFileMd5(filepath):
    # 获取文件的md5
    myhash = hashlib.md5()
    f = open(filepath, "rb")
    while True:
        b = f.read(8096)
        if not b:
            break
        myhash.update(b)
    f.close()
    return myhash.hexdigest()
######## 获取MD5码

def transportFile(sock, f, source):
    absolute = Path(source).parent.joinpath(f)  # 本地可访问文件路径

    header = getHeader(f, absolute)  # 生成头部
    sock.send(header[0])  # 传输文件名大小
    sock.send(header[1])  # 传输文件名
    sock.send(header[2])  # 传输文件大小 
    sock.send(header[3])    ### 传输md5码
    recv_data=sock.recv(1)  ### 这里用于接收文件在对方的存在情况
    ######### recv_data 2|已传  1|追加  0|未穿
    if(int(recv_data)==2):  ###已传
        return
    if(int(recv_data)==1):  ###追加
        recv_data= int.from_bytes(sock.recv(10), byteorder="big") ### 获取
        fp=open(absolute,'rb')
        fp.read(recv_data)
    if(int(recv_data)==0):### 包括两种情况新文件或者更新覆盖,但都是直接发送整个文件
        fp = open(absolute, 'rb')
    while True:             # 连续传送文件
        data = fp.read(1024)
        if not data:
            break
        sock.send(data)
    print(f"already transport {absolute}")
    #########


def getHeader(__p, __s):
    file_name = str(__p).encode('utf-8')  # (路径)文件名
    file_name_size = len(file_name).to_bytes(
        4, byteorder="big")  # 文件名长度(4Byte),
    file_size = Path(__s).stat().st_size.to_bytes(
        10, byteorder="big")  # 文件大小(32Byte)
    file_md5 = GetFileMd5(Path(__s)).encode('utf-8')  ### md5码(32Byte)
    return [file_name_size, file_name, file_size,file_md5]


def getListOfFiles(__s):
    __p = Path(__s)
    if __p.is_file():
        return [__p.name]   # 如果是文件则直接返回单元素列表
    else:
        return [__f.parent.relative_to(__p.parent).joinpath(__f.name)  # 将文件名加上文件夹的相对路径
                for __f in __p.rglob('*')   # 选择所有文件和文件夹
                if __f.is_file()]   # 仅选择文件


def getAllZipFiles(__s):
    __p = Path(__s)
    if __p.is_file() and __p.match("*.zip"):
        return [__p.name]  # 如果是文件则直接返回单元素列表
    else:
        return [__f.parent.relative_to(__p.parent).joinpath(__f.name)  # 将文件名加上文件夹的相对路径
            for __f in __p.rglob('*.zip')  # 选择所有文件和文件夹
                if __f.is_file()]  # 仅选择文件

if __name__ == '__main__':
    source = sys.argv[1]
    remoteAddr = sys.argv[2]
    remotePort = int(sys.argv[3])
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # 建立TCP连接
    s.connect((remoteAddr, remotePort))  # 发起连接
    relative_files = getListOfFiles(source)  # 获得所有需要发送的所有文件

    for f in relative_files:
        transportFile(s, f, source)
    endByte = 0
    endFlag=endByte.to_bytes(4, byteorder="big")
    s.send(endFlag)

    s.close()
