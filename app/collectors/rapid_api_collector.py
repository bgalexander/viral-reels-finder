import requests
import time


class RapidAPICollector:
    """Сбор рилсов через RapidAPI"""

    def __init__(self):
        self.api_key = "1fbdbc3795msh0eac6fabad71ee3p170a89jsnf8f2e835d6b9"
        self.api_host = "instagram-best-experience.p.rapidapi.com"
        self.headers = {
            "x-rapidapi-key": self.api_key,
            "x-rapidapi-host": self.api_host,
            "Content-Type": "application/json"
        }

    def search_by_hashtag(self, tag, max_results=20):
        """Поиск рилсов по хэштегу"""
        url = f"https://{self.api_host}/hashtag_section"

        all_reels = []
        max_id = None
        page = 0

        while len(all_reels) < max_results:
            params = {
                "tag": tag.replace("#", ""),
                "section": "clips"
            }

            if max_id:
                params["max_id"] = max_id

            try:
                response = requests.get(url, headers=self.headers, params=params)

                if response.status_code == 429:
                    time.sleep(60)
                    continue

                if response.status_code != 200:
                    break

                data = response.json()

                if data.get("status") != "ok":
                    break

                sections = data.get("data", {}).get("sections", [])

                found = 0
                for section in sections:
                    medias = section.get("layout_content", {}).get("medias") or []
                    for item in medias:
                        media = item.get("media", {})

                        if media.get("product_type") != "clips":
                            continue

                        code = media.get("code", "")
                        play_count = media.get("play_count", 0) or 0
                        like_count = media.get("like_count", 0) or 0
                        comment_count = media.get("comment_count", 0) or 0
                        username = media.get("user", {}).get("username", "")
                        full_name = media.get("user", {}).get("full_name", "")
                        is_verified = media.get("user", {}).get("is_verified", False)
                        profile_pic = media.get("user", {}).get("profile_pic_url", "")
                        caption = ""
                        if media.get("caption") and media["caption"].get("text"):
                            caption = media["caption"]["text"]
                        video_duration = media.get("video_duration", 0) or 0
                        taken_at = media.get("taken_at", 0)

                        # Превью картинка
                        thumbnail = ""
                        candidates = media.get("image_versions2", {}).get("candidates", [])
                        if candidates:
                            thumbnail = candidates[0].get("url", "")

                        reel = {
                            "shortcode": code,
                            "username": username,
                            "full_name": full_name,
                            "is_verified": is_verified,
                            "profile_pic_url": profile_pic,
                            "thumbnail_url": thumbnail,
                            "reel_url": f"https://www.instagram.com/reel/{code}/",
                            "profile_url": f"https://www.instagram.com/{username}/",
                            "views": play_count,
                            "likes": like_count,
                            "comments": comment_count,
                            "duration": round(video_duration, 1),
                            "caption": caption,
                            "timestamp": taken_at,
                            "hashtag": tag.replace("#", ""),
                            "engagement_rate": round(
                                (like_count + comment_count) / play_count * 100, 2
                            ) if play_count > 0 else 0
                        }

                        all_reels.append(reel)
                        found += 1

                # Пагинация
                more = data.get("data", {}).get("more_available", False)
                next_id = data.get("data", {}).get("next_max_id")

                if not more or not next_id or found == 0:
                    break

                max_id = next_id
                page += 1
                time.sleep(2)

            except Exception as e:
                print(f"Error: {e}")
                break

        return all_reels[:max_results]