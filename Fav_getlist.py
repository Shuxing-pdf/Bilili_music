# B站用户公开收藏夹 → JSON（支持合并输出与独立输出）
# 修复输出格式：使用 musicList 并确保 duration 字段存在

import os
import time
import json
import requests
import uuid
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Referer": "https://www.bilibili.com"
}

# ==========  状态变量  ==========
current_mid = None
current_folders = None

# ==========  ID管理变量  ==========
PREDEFINED_IDS = [
    "Rg3SbSqZPOusCUbQDTF-8",
    "7BE3J6_KdrUSmKHgnExQ2",
    "n1TC8Ft8ktFLNZ2uAFXOr",
    "72fafecd-4b56-47fd-a1f9-547a58e9b811",
    "92e78b36-2ff6-4e18-8818-de61a270cd76",
    "06f4f5ff-011b-41fd-8406-82e2c998b89a",
    "4f14f3ba-f8aa-4617-908f-8f5e5236a184",
    "8f597787-84f8-49e6-b109-232c74d9da15",
    "8a1fba93-b973-4d7f-87d7-f8df27a26379",
    "e99c77e4-ee80-4d20-9417-6f41108d7776",
    "e3485032-cedc-4a83-8759-eb69cbe78bb3"
]
current_id_index = 0

# ==========  重复导出检测集合（新增） ==========
exported_folders = set()

# ==========  功能函数  ==========
def generate_id():
    """生成22位随机ID"""
    return uuid.uuid4().hex[:22]

def clean_filename(name: str):
    """清理文件名非法字符"""
    return "".join(c for c in name if c not in r'\/:*?"<>|')

def get_user_folders(mid: str):
    """返回用户所有公开收藏夹列表"""
    url = "https://api.bilibili.com/x/v3/fav/folder/created/list-all"
    params = {"up_mid": mid}
    resp = requests.get(url, params=params, headers=HEADERS, timeout=10)
    if resp.status_code != 200:
        raise RuntimeError(f"HTTP {resp.status_code}")
    data = resp.json()
    if data["code"] != 0:
        raise RuntimeError(f"API 错误 {data['code']}：{data['message']}")
    if data.get("data") is None:
        return []
    return data["data"].get("list", []) or []

def find_matching_folders(folders, keyword):
    """查找所有标题包含关键字的收藏夹，返回列表"""
    matches = []
    for f in folders:
        if keyword.lower() in f["title"].lower():  # 不区分大小写匹配
            matches.append({
                "id": str(f["id"]),
                "title": f["title"],
                "intro": f.get("intro", ""),
                "cover": f.get("cover", ""),
                "upper_name": f.get("upper", {}).get("name", "未知用户"),
                "media_count": f["media_count"]
            })
    return matches

def get_folder_info(folders, title: str):
    """根据标题模糊匹配收藏夹详细信息"""
    for f in folders:
        if title in f["title"]:
            return {
                "id": str(f["id"]),
                "title": f["title"],
                "intro": f.get("intro", ""),
                "cover": f.get("cover", ""),
                "upper_name": f.get("upper", {}).get("name", "未知用户"),
                "media_count": f["media_count"]
            }
    return None

def get_folder_detail(media_id: str):
    """获取单个收藏夹的完整元数据"""
    url = "https://api.bilibili.com/x/v3/fav/folder/info"
    params = {"media_id": media_id}
    resp = requests.get(url, params=params, headers=HEADERS, timeout=10)
    if resp.status_code != 200:
        raise RuntimeError(f"HTTP {resp.status_code}")
    data = resp.json()
    if data["code"] != 0:
        raise RuntimeError(f"API 错误 {data['code']}：{data['message']}")
    return data["data"]

def get_video_pages(bvid: str):
    """
    获取视频的分P详细信息
    返回: 分P对象列表，包含cid, part(分P标题), duration(分P时长)等
    """
    url = "https://api.bilibili.com/x/player/pagelist"
    params = {"bvid": bvid}
    try:
        resp = requests.get(url, params=params, headers=HEADERS, timeout=10)
        if resp.status_code != 200:
            print(f"⚠️ 获取 {bvid} 的分P信息失败: HTTP {resp.status_code}")
            return None
        
        data = resp.json()
        if data["code"] != 0:
            print(f"⚠️ 获取 {bvid} 的分P信息失败: API错误 {data['code']} - {data['message']}")
            return None
        
        return data.get("data")
    except Exception as e:
        print(f"⚠️ 获取 {bvid} 的分P信息时发生异常: {e}")
        return None

def fetch_all_videos(media_id: str, total_count: int):
    """拉取收藏夹全部视频，带进度条显示"""
    videos, page = [], 1
    page_size = 20
    calculated_total_pages = (total_count + page_size - 1) // page_size
    
    processed_videos = 0
    
    print(f"\n📊 该收藏夹共 {total_count} 个视频稿件，预计 {calculated_total_pages} 页")
    
    while True:
        progress = processed_videos / total_count * 100 if total_count > 0 else 0
        print(f"\r🔄 正在抓取第 {page}/{calculated_total_pages} 页 "
              f"(已处理 {processed_videos}/{total_count} 个稿件, "
              f"进度: {progress:.1f}%)", end="")
        
        url = "https://api.bilibili.com/x/v3/fav/resource/list"
        params = {"media_id": media_id, "pn": page, "ps": page_size, "platform": "web"}
        resp = requests.get(url, params=params, headers=HEADERS, timeout=10)
        if resp.status_code != 200:
            raise RuntimeError(f"HTTP {resp.status_code}")
        data = resp.json()
        if data["code"] != 0:
            raise RuntimeError(f"API 错误 {data['code']}：{data['message']}")
        if data.get("data") is None:
            break
        medias = data["data"].get("medias")
        if not medias:
            break
        
        for v in medias:
            # 修复：每个稿件只计数一次
            processed_videos += 1
            
            avid = v["id"]
            bvid = v["bvid"]
            
            pages = get_video_pages(bvid)
            if pages is None:
                print(f"\n⚠️ 跳过视频 {bvid} (标题: {v['title']}) - 无法获取分P信息")
                continue
            
            for idx, page_info in enumerate(pages):
                cid = page_info["cid"]
                page_title = page_info.get("part", "").strip() if page_info.get("part") else v["title"]
                # ✅ 修复：使用 get 方法获取 duration，默认值为 0
                page_duration = page_info.get("duration", 0)
                
                # ✅ 修改：调整视频对象结构，增加必需字段
                videos.append({
                    "id":f"{avid}_{bvid}_{cid}",
                    "avid":avid,                    # avid
                    "bvid":bvid,                    # bvid
                    "cid":cid,                      # cid
                    "name":page_title,
                    "duration":page_duration,       # ✅ 确保 duration 存在
                    "cover":v["cover"],
                    "author":v["upper"]["name"],
                    "origin":"bili"                 # origin
                })
        
        if not data["data"].get("has_more", False):
            break
        page += 1
        time.sleep(0.5)
    
    print(f"\r✅ 抓取完成！共 {len(videos)} 个分P条目，来自 {processed_videos}/{total_count} 个稿件  " + " " * 30)
    return videos

def save_json(folder_data: dict, folder_title: str):
    """保存单个收藏夹为独立JSON文件"""
    safe_title = clean_filename(folder_title)
    file_name = f"《{safe_title}》收藏夹.json"
    file_path = SCRIPT_DIR / file_name
    
    # ✅ 修改：生成字符串后替换格式，换行并额外缩进一格（2空格）
    json_str = json.dumps(folder_data, ensure_ascii=False, indent=2)
    json_str = json_str.replace('"musicList": [', '"musicList":\n    [')
    
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(json_str)
        f.flush()
        os.fsync(f.fileno())
    return file_path.resolve()

def save_merged_json(all_folders_data: list, folder_titles: list):
    """合并所有收藏夹为单个JSON文件"""
    if len(folder_titles) <= 3:
        merged_name = "+".join([f"《{t}》" for t in folder_titles])
    else:
        merged_name = "+".join([f"《{t}》" for t in folder_titles[:3]]) + " 等"
    
    file_name = f"{merged_name}收藏夹视频信息.json"
    file_path = SCRIPT_DIR / clean_filename(file_name)
    
    # ✅ 修改：生成字符串后替换格式，换行并额外缩进一格（2空格）
    json_str = json.dumps(all_folders_data, ensure_ascii=False, indent=2)
    json_str = json_str.replace('"musicList": [', '"musicList":\n    [')
    
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(json_str)
        f.flush()
        os.fsync(f.fileno())
    return file_path.resolve()

def ask_continue(prompt: str):
    """统一询问是否继续"""
    while True:
        choice = input(prompt).strip().lower()
        if choice == 'y':
            return True
        elif choice == 'n':
            return False
        print("请输入 Y 或 N")

# ==========  主流程  ==========
def main():
    global current_mid, current_folders, current_id_index, exported_folders
    
    print("==========  B站收藏夹 → JSON 工具  ==========")
    
    # 首次执行时询问输出模式
    if not hasattr(main, "separate_output"):
        print("\n📦 请选择输出模式：")
        print("  Y → 每个收藏夹单独输出一个JSON文件")
        print("  N → 所有收藏夹合并为单个JSON文件")
        while True:
            choice = input("您是否需要每个收藏夹单独输出文件？（Y/N）：").strip().lower()
            if choice in ['y', 'n']:
                main.separate_output = (choice == 'y')
                break
            print("❌ 请输入 Y 或 N")
    
    print("首次使用需输入用户ID，后续可选择复用或切换账号\n")
    
    # 用于合并模式的累积变量
    all_folders_data = []
    folder_titles = []
    
    while True:
        # ========== 步骤1: 账号信息处理 ==========
        if current_mid is None:
            mid = input("请输入B站用户ID（mid）：").strip()
        else:
            print(f"\n📌 当前账号 mid={current_mid}")
            if ask_continue("是否使用同一账号继续？（Y/N）："):
                mid = current_mid
            else:
                mid = input("请输入新的B站用户ID（mid）：").strip()
        
        if mid != current_mid:
            if not mid.isdigit():
                print("❌ 用户ID必须是数字")
                continue
            
            current_mid = mid
            try:
                current_folders = get_user_folders(current_mid)
            except RuntimeError as e:
                print(f"❌ 获取收藏夹列表失败：{e}")
                current_mid = None
                continue
                
            if not current_folders:
                print("⚠️ 该用户无公开收藏夹")
                current_mid = None
                continue
        
        # ========== 步骤2: 选择并导出收藏夹 ==========
        print(f"\n📂 共发现 {len(current_folders)} 个公开收藏夹：")
        for idx, f in enumerate(current_folders, 1):
            print(f"  {idx}. {f['title']}  (id:{f['id']}, 共{f['media_count']}个视频)")

        # 循环直到成功选择或用户取消
        selected_folder = None
        while selected_folder is None:
            title_key = input("\n请输入要导出的收藏夹【标题关键词】：").strip()
            if not title_key:
                print("❌ 关键词不能为空")
                continue
    
            # 查找所有匹配项
            matching_folders = find_matching_folders(current_folders, title_key)
    
            if len(matching_folders) == 0:
                print(f"❌ 未找到标题包含『{title_key}』的收藏夹")
                if not ask_continue("是否重新输入关键词？（Y/N）："):
                    break
                continue
    
            elif len(matching_folders) == 1:
                # 唯一匹配，直接确认
                selected_folder = matching_folders[0]
                print(f"\n✅ 找到唯一匹配：《{selected_folder['title']}》")
        
            else:
                # 多个匹配，展示列表供选择
                print(f"\n⚠️  找到 {len(matching_folders)} 个匹配的收藏夹：")
                for idx, folder in enumerate(matching_folders, 1):
                    print(f"  {idx}. {folder['title']}  (id:{folder['id']}, {folder['media_count']}个视频)")
        
                while True:
                    choice = input("\n请输入序号选择（或输入 0 重新输入关键词）：").strip()
                    if choice == "0":
                        break  # 跳出内层循环，重新输入关键词
                    if choice.isdigit() and 1 <= int(choice) <= len(matching_folders):
                        selected_folder = matching_folders[int(choice) - 1]
                        break
                    print("❌ 请输入有效序号或 0")

        # 检查是否成功选择
        if selected_folder is None:
            print("\n⚠️  未选择收藏夹，跳过本次操作")
            continue

        try:
            # 使用已选择的文件夹信息获取详情
            folder_detail = get_folder_detail(selected_folder["id"])
        except RuntimeError as e:
            print(f"\n❌ 获取收藏夹详情失败：{e}")
            continue

        # 检查重复导出
        folder_key = (current_mid, folder_detail["id"])
        if folder_key in exported_folders:
            print(f"\n⚠️ 该收藏夹《{folder_detail['title']}》已导出。")
            continue

        print(f"\n🎯 正在抓取收藏夹《{folder_detail['title']}》...")
        try:
            videos = fetch_all_videos(folder_detail["id"], folder_detail["media_count"])
        except RuntimeError as e:
            print(f"\n❌ 抓取视频失败：{e}")
            continue
        
        # ✅ 修改：检查ID是否用尽
        if current_id_index >= len(PREDEFINED_IDS):
            print(f"\n⚠️ 警告：预定义的ID列表已用尽（最多支持{len(PREDEFINED_IDS)}个收藏夹）")
            print("将无法继续处理更多收藏夹")
            break
        
        # ✅ 修改：分配ID并增加索引
        assigned_id = PREDEFINED_IDS[current_id_index]
        current_id_index += 1
        
        # ✅ 修改：构建标准化收藏夹数据对象（包含 musicList）
        folder_data = {
            "id": assigned_id,              # ✅ 使用预定义的ID
            "name": folder_detail["title"],
            "desc": folder_detail.get("intro", ""),
            "author": folder_detail["upper"]["name"],
            "cover": folder_detail.get("cover", ""),
            "createdAt": None,              # ✅ 设置为null
            "updatedAt": None,              # ✅ 设置为null
            "musicList": videos             # ✅ 修改键名为 musicList
        }
        
        if main.separate_output:
            # 独立模式：立即保存并标记为已导出
            saved = save_json(folder_data, folder_detail["title"])
            exported_folders.add(folder_key)  # ✅ 标记已导出
            print(f"\n💾 JSON 文件已生成 → {saved}")
            print(f"📊 共导出 {len(videos)} 条记录")
        else:
            # 合并模式：累积数据并标记为已导出
            all_folders_data.append(folder_data)
            folder_titles.append(folder_detail["title"])
            exported_folders.add(folder_key)  # ✅ 标记已导出
            # 修复：计算累积总数
            total_videos = sum(len(f['musicList']) for f in all_folders_data)
            print(f"\n📥 已累积 {len(folder_titles)} 个收藏夹，共 {total_videos} 个视频条目")
        
        # ========== 步骤3: 询问是否继续 ==========
        if not ask_continue("\n是否继续导出其他收藏夹？（Y/N）："):
            break
    
    # 合并模式最终保存
    if not main.separate_output and all_folders_data:
        print(f"\n📝 正在合并 {len(folder_titles)} 个收藏夹并保存...")
        saved = save_merged_json(all_folders_data, folder_titles)
        print(f"\n💾 合并JSON文件已生成 → {saved}")
        print(f"📊 共导出 {sum(len(f['musicList']) for f in all_folders_data)} 条记录")

if __name__ == "__main__":
    main()