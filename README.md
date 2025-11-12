# BiBi_music - B站收藏夹导出工具

自动抓取B站用户公开收藏夹的视频信息，生成标准化的 JSON 文件，支持导入到哔哔音乐。

## 功能特点

- **精准抓取** - 获取B站用户公开收藏夹的完整视频信息
- **双模式输出** - 支持独立文件输出和合并文件输出
- **哔哔音乐兼容** - 生成符合哔哔音乐导入标准的 JSON 格式
- **智能续传** - 支持同一账号多次操作，避免重复导出
- **进度显示** - 实时显示抓取进度和统计信息
- **错误处理** - 完善的异常处理和网络重试机制


## 使用教程

1.[点此获取自己账号的mid](https://space.bilibili.com/ "".com/"之后的一串数字即对应账号的mid") ,".com/"之后的一串数字即对应账号的mid，即下图框选部分。

![mid位置](https://i.imgur.com/h8EVJxH.png)

2.运行_Fav___getlist.py_，按程序要求依次输入目标账号mid、目标收藏夹（支持模糊查找与重复导出检测）。

3.程序运行结束后，会在_Fav___getlist.py_所在目录下生成对应JSON文件。

## 输出格式

生成的 JSON 文件包含以下标准字段：

    "id": "预定义ID",
    "name": "收藏夹名称",
    "desc": "收藏夹描述",
    "author": "创建者名称",
    "cover": "封面图片URL",
    "createdAt": null,
    "updatedAt": null,
    "musicList": 
    [
      {
        "id": "avid_bvid_cid",
        "avid": "视频AV号",
        "bvid": "视频BV号",
        "cid": "分P视频CID",
        "name": "视频标题",
        "duration": 时长(秒),
        "cover": "视频封面",
        "author": "UP主名称",
        "origin": "bili"
      }
    ]

## 鸣谢

 感谢[阿炸克斯](https://github.com/lvyueyang  "你们的存在，让社区更美好")提供的[哔哔音乐歌单云同步详细教程](https://juejin.cn/post/7428849498019053587 "如何使用哔哔音乐的歌单云同步功能")以及 [SocialSisterYi](https://github.com/SocialSisterYi/bilibili-API-collect "你们的存在，让社区更美好") 整理的[B 站接口文档](https://github.com/SocialSisterYi/bilibili-API-collect) 。