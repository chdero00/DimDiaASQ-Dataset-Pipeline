import json
from collections import defaultdict
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# 【請替換為您的 API Key】
DEVELOPER_KEY = "AIzaSyCjj0V96TCZiui8JA94wZdJEBF3wEou4jU"
YOUTUBE_API_SERVICE_NAME = "youtube"
YOUTUBE_API_VERSION = "v3"

def get_videos_from_playlist(youtube, playlist_id, domain_name):
    """
    透過播放清單 ID 抓取清單內的所有影片，並自動標記領域。
    """
    print(f"📂 正在讀取【{domain_name}】領域的播放清單 (ID: {playlist_id})...")
    video_list = []
    next_page_token = None

    try:
        while True:
            playlist_response = youtube.playlistItems().list(
                part="snippet",
                playlistId=playlist_id,
                maxResults=50,  # 每次最多抓取 50 筆
                pageToken=next_page_token
            ).execute()

            for item in playlist_response.get("items", []):
                video_id = item["snippet"]["resourceId"]["videoId"]
                title = item["snippet"]["title"]
                
                # 過濾掉已經被 YouTube 刪除或隱藏的私人影片
                if title != "Private video" and title != "Deleted video":
                    video_list.append({
                        "id": video_id,
                        "title": title,
                        "domain": domain_name
                    })

            next_page_token = playlist_response.get("nextPageToken")
            if not next_page_token:
                break
                
        print(f"✅ 成功載入 {len(video_list)} 支【{domain_name}】相關影片。")
        return video_list

    except HttpError as e:
        print(f"❌ 讀取播放清單時發生 API 錯誤: {e}")
        return []

def fetch_raw_youtube_dialogues(youtube, video_list, max_threads_per_video=300, min_replies=4):
    """
    【階段一：寬鬆抓取】
    負責把有潛力的長留言串抓下來，原汁原味保留 text，不做結構解析。
    :param min_replies: 最少回覆數 (設為4代表：1主留言 + 4回覆 = 總節點至少5)
    """
    dataset = []
    dialogue_counter = 1 

    for video in video_list:
        video_id = video["id"]
        video_title = video["title"]
        domain = video["domain"]
        print(f"\n影片: {video_title} (ID: {video_id}) [{domain}]")

        try:
            threads_checked = 0
            thread_count = 0
            next_page_token = None
            
            while threads_checked < max_threads_per_video:
                threads_response = youtube.commentThreads().list(
                    part="snippet", 
                    videoId=video_id,
                    textFormat="plainText",
                    maxResults=100,
                    pageToken=next_page_token
                ).execute()

                items = threads_response.get("items", [])
                if not items:
                    break 

                for thread in items:
                    threads_checked += 1
                    if threads_checked > max_threads_per_video:
                        break

                    top_comment = thread["snippet"]["topLevelComment"]
                    reply_count = thread["snippet"]["totalReplyCount"]
                    thread_id = thread["id"]
                    
                    # 【寬鬆過濾】：直接捨棄回覆數太少的，避免浪費 API Quota
                    if reply_count < min_replies:
                        continue

                    dialogue_id = f"RAW_DIA_{dialogue_counter:05d}"
                    utterances = []
                    
                    top_author = top_comment["snippet"]["authorDisplayName"]
                    top_text = top_comment["snippet"]["textDisplay"].replace('\u200b', '').strip()
                    
                    # 紀錄主留言 (utt_id: 0)
                    utterances.append({
                        "utt_id": 0,
                        "speaker": top_author,
                        "reply_to": -1,
                        "text": top_text
                    })

                    try:
                        replies_response = youtube.comments().list(
                            part="snippet",
                            parentId=thread_id,
                            textFormat="plainText",
                            maxResults=100 
                        ).execute()
                        
                        replies = replies_response.get("items", [])
                        # 確保留言是依照時間先後排序，這對第二階段建樹非常重要
                        replies.sort(key=lambda x: x["snippet"]["publishedAt"])
                        
                        utt_id = 1
                        for reply in replies:
                            reply_author = reply["snippet"]["authorDisplayName"]
                            reply_text = reply["snippet"]["textDisplay"].replace('\u200b', '').strip()
                            
                            # 不在此處解析 @，全部預設指向主留言 (reply_to: 0)
                            utterances.append({
                                "utt_id": utt_id,
                                "speaker": reply_author,
                                "reply_to": 0,  
                                "text": reply_text
                            })
                            utt_id += 1
                            
                    except HttpError as e:
                        print(f"  ⚠️ 抓取子留言時發生錯誤，略過此討論串: {e}")
                        continue

                    # 🌟 【重要改動】：加入影片標題，解決隱含實體 (Implicit Target) 問題
                    dialogue_data = {
                        "dialogue_id": dialogue_id,
                        "domain": domain,
                        "source_video_id": video_id,        # 改名為 _id 更加精確
                        "source_video_title": video_title,  # 新增影片標題欄位
                        "total_turns": len(utterances),
                        "utterances": utterances,
                    }
                    
                    dataset.append(dialogue_data)
                    dialogue_counter += 1
                    thread_count += 1

                next_page_token = threads_response.get("nextPageToken")
                if not next_page_token:
                    break
                
            print(f"  -> 檢查了 {threads_checked} 個留言串。")
            print(f"  -> 📦 成功抓取 {thread_count} 筆原始對話語料！")

        except HttpError as e:
            print(f"❌ 抓取影片 {video_id} 留言串時發生錯誤: {e}")
            continue 

    return dataset

if __name__ == "__main__":
    youtube_client = build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION, developerKey=DEVELOPER_KEY)
    
    # 這裡你可以設定多個播放清單，程式會自動把它們合併處理
    # 記得：抓過的就註解掉，避免重複浪費 API 額度！
    playlists_to_scrape = {
        "PLxCMPsfHTCwSEWm_WOCrb7UDUTHRzsHlb": "手機",
        # "PLxxxxxx_YOUR_LAPTOP_PLAYLIST_ID_xxxx": "筆電",
        # "PLxxxxxx_YOUR_HOTEL_PLAYLIST_ID_xxxx": "飯店",
        # "PLxxxxxx_YOUR_RESTAURANT_PLAYLIST_ID_xxxx": "餐廳",
    }
    
    # 定義領域的中英文對照表，用於輸出全英文檔名
    domain_to_english = {
        "手機": "Mobile",
        "筆電": "Laptop",
        "飯店": "Hotel",
        "餐廳": "Restaurant"
    }
    
    # 將影片依據領域分組
    videos_by_domain = defaultdict(list)
    
    print("\n--- 準備階段：讀取播放清單 ---")
    for playlist_id, domain_name in playlists_to_scrape.items():
        videos_in_playlist = get_videos_from_playlist(youtube_client, playlist_id, domain_name)
        videos_by_domain[domain_name].extend(videos_in_playlist)
    
    # 依序針對每個領域進行抓取與獨立存檔
    for domain_name, target_videos in videos_by_domain.items():
        if not target_videos:
            continue
            
        print(f"\n--- 開始執行第一階段：寬鬆抓取 (領域: {domain_name}) ---")
        raw_dataset = fetch_raw_youtube_dialogues(
            youtube_client, 
            target_videos, 
            max_threads_per_video=300,
            min_replies=4 # 設定最少 4 個回覆 (總節點 >= 5)
        )
        
        # 取得英文領域名稱，若遇到未知領域預設為 Unknown
        eng_domain = domain_to_english.get(domain_name, "Unknown")
        output_filename = f"Stage1_Raw_{eng_domain}.json"
        
        with open(output_filename, "w", encoding="utf-8") as f:
            json.dump(raw_dataset, f, ensure_ascii=False, indent=4)
            
        print(f"\n🎉 【{domain_name}】抓取完成！總共收集了 {len(raw_dataset)} 筆對話，已儲存至 {output_filename}")

    print("\n✅ 所有指定的播放清單皆已處理完畢！")