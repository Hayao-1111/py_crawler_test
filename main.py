import requests
import json
import time
import argparse

def get_info_by_BV(bvid:str, info_file_path:str):
    ''' 获取视频信息 
    
    输入: 
    - `bvid` B站视频的BVID; 
    - `info_file_path` 视频信息存储路径;  

    输出: 若成功获取视频，则返回视频信息，并将其中的部分关键信息存储; 否则返回`None`
    '''
    headers = {"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.132 Safari/537.36"}
    url = "https://api.bilibili.com/x/web-interface/view?bvid={}".format(bvid)
    response = requests.get(url=url, headers=headers)

    if response.status_code == 200:
        content = response.content.decode()
        data = json.loads(content)
        
        # 如果请求失败, 则显示错误信息和退出代码
        try:
            assert data["code"] == 0
        except:
            code = data["code"]
            message = data["message"]
            print("Error: {} with exit code {}".format(message, code))
            return None
        
        data = data["data"]

        # 获取视频信息
        info = ""
        info += "视频的BVID为 {}, AVID为 {}, 共 {} P".format(data['bvid'], data['aid'], data['videos'])
        info += ", 属于{}子分区".format(data['tname'])
        info += "\n 视频标题: {}".format(data['title'])
        info += "\n 视频简介: {}".format(data["desc"])
        info += "\n 此视频UP主的名字: {}, mid = {}".format(data["owner"]["name"], data["owner"]["mid"])

        pubdate_time = data["pubdate"]
        ctime_time = data["ctime"]
        # import time
        info += "\n 视频的投稿时间: {}".format(
            time.strftime("%Y年%m月%d日 %H时%M分%S秒", 
                        time.localtime(ctime_time))
            )
        info += "\n 视频的发稿时间: {}".format(
            time.strftime("%Y年%m月%d日 %H时%M分%S秒", 
                        time.localtime(pubdate_time))
            )

        now_time = time.strftime("%Y年%m月%d日 %H时%M分%S秒", time.localtime())
        info += "\n 截至{}, 本视频{}播放量, {}弹幕, {}评论, {}收藏, {}投币, {}分享, 获{}赞".format(
            now_time,
            data["stat"]["view"],
            data["stat"]["danmaku"],
            data["stat"]["reply"],
            data["stat"]["favorite"],
            data["stat"]["coin"],
            data["stat"]["share"],
            data["stat"]["like"]
        )

        # 将视频信息返回到文件中
        with open(info_file_path, "w", encoding="utf-8") as f:
            f.write(info)
        
        return data
    else:
        print("Can NOT access the information of video with BVID {}".format(bvid))
        return None


def get_playurl_by_BVID(bvid:str, qn:int=80, needCookie:bool=True, cookie_path:str="Cookie"):
    ''' 获取视频的播放地址 
    
    输入: 
    - `bvid` 视频的BVID; 
    - `qn` 视频清晰度, 默认为80, 对应1080P; 其他常用选择包括：
        * `qn = 16` 对应 360P(在无Cookie时的默认选择)
        * `qn = 32` 对应 480P
        * `qn = 64` 对应 720P 
    - `needCookie` 是否选择使用Cookie, 默认为 `True`;
    - `cookie_path` Cookie文件路径, 默认为 `./Cookie`;

    输出: 若成功获取, 则返回包含视频播放地址的字典数据; 否则报错并返回None
    '''
    # 获取视频信息
    data = get_info_by_BV(bvid=bvid, info_file_path="{}_info.txt".format(bvid))

    try:
        assert data != None
    except:
        print("Error: Can NOT access the information of the video with BVID {}".format(bvid))
        print("Please check if the BVID is right.")
        return None
    
    
    # 下载视频封面图片
    front_page_url = data['pic']
    r = requests.get(front_page_url)
    with open("{}_front_image.{}".format(data['bvid'], front_page_url.split(".")[-1]), "wb") as f:
        f.write(r.content)

    # 下载UP主头像图片
    onwer_face_image_url = data["owner"]["face"]
    r = requests.get(onwer_face_image_url)
    with open("{}_onwer_face_image.{}".format(data['bvid'], onwer_face_image_url.split(".")[-1]), "wb") as f:
        f.write(r.content)

    cid = data["cid"]

    # 请求URL
    # url = "https://api.bilibili.com/x/player/playurl?bvid={}&cid={}".format(bvid, cid)
    url_1080P = "https://api.bilibili.com/x/player/playurl?bvid={}&cid={}&qn={}".format(bvid, cid, qn)
    
    headers_playurl={
        "User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.132 Safari/537.36"
    }

    # 如果用户需要Cookie
    if needCookie == True:
        try:
            with open(cookie_path, "r", encoding="utf-8") as f:
                my_cookie = f.read()
        except Exception as e:
            print("Error: {}".format(e))
            return None
        
        headers_playurl["Cookie"] = my_cookie
    
    response = requests.get(url=url_1080P, headers=headers_playurl)

    try:
        assert response.status_code == 200
    except:
        print("Error: Can NOT get the playurl of the video with BVID {}".format(bvid))
        return None

    content = response.content.decode()
    data = json.loads(content)

    return data


def download_video_from_playurl(data):
    ''' 下载视频 '''
    download_url = data["data"]["durl"][0]["url"]
    headers_download={
            "User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.132 Safari/537.36",
            "referer":'https://www.bilibili.com'
            }
    
    print("Downloading the video ... ")

    r = requests.get(download_url, headers=headers_download)

    try:
        assert r.status_code == 200
    except:
        print("Error: Download Failed!")
        return -1

    with open("{}_video.mp4".format(bvid), "wb") as f:
        f.write(r.content)

    print("Successfully downloaded the video!")
    return 0


def startup():
    ''' 接受命令行参数启动 '''
    parser = argparse.ArgumentParser(description='Get Bilibili Video')
    parser.add_argument('--bvid', type=str, default="BV1JQ4y1e7jV",
        help='BVID of the video in the Bilibili website')
    parser.add_argument('--qn', type=int, default=80,
        help='Video Clarity Selection, 80 for 1080P(by default), 32 for 480P, 16 for 360P. NOTE: If you really need 1080P, you should login and get the Cookie')
    parser.add_argument("--needCookie", type=int, default=1, 
        help="If you need Cookie to get videos with higher quality, please choose 1, or you choose 0")
    parser.add_argument("--cookie_path", type=str, default="Cookie",
        help="Path of Cookie file. The Cookie file should ONLY contain your Cookie that you login the Bilibili website")
    args = parser.parse_args()

    return args


if __name__ == "__main__":
    args = startup()
    bvid = args.bvid
    qn = args.qn
    needCookie = True if args.needCookie == 1 else False
    cookie_path = args.cookie_path

    data = get_playurl_by_BVID(bvid, qn=qn, needCookie=needCookie, cookie_path=cookie_path)

    if data != None:
        result = download_video_from_playurl(data)

    