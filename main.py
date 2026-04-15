import streamlit as st
import pandas as pd
import requests
import json
import time
from datetime import datetime


class RapidAPICollector:
    def __init__(self, proxy=None):
        self.api_key = "1fbdbc3795msh0eac6fabad71ee3p170a89jsnf8f2e835d6b9"
        self.api_host = "instagram-best-experience.p.rapidapi.com"
        self.headers = {
            "x-rapidapi-key": self.api_key,
            "x-rapidapi-host": self.api_host,
            "Content-Type": "application/json"
        }
        self.proxies = None
        if proxy:
            self.proxies = {"http": proxy, "https": proxy}

    def search_by_hashtag(self, tag, max_results=20, debug_container=None):
        tag_clean = tag.replace("#", "").strip()
        url = f"https://{self.api_host}/hashtag_section"
        params = {"tag": tag_clean, "section": "clips"}

        if debug_container:
            debug_container.write(f"🔗 URL: `{url}`")
            debug_container.write(f"📋 Params: `{params}`")

        all_reels = []

        try:
            response = requests.get(
                url, headers=self.headers, params=params,
                proxies=self.proxies, timeout=30
            )

            if debug_container:
                debug_container.write(f"📡 Status Code: **{response.status_code}**")

            if response.status_code != 200:
                if debug_container:
                    debug_container.error(f"❌ Ошибка {response.status_code}: {response.text[:500]}")
                return []

            data = response.json()

            if debug_container:
                debug_container.write(f"📦 Status в ответе: `{data.get('status')}`")
                debug_container.write(f"📦 Ключи ответа: `{list(data.keys())}`")

            if data.get("status") != "ok":
                return []

            sections = data.get("data", {}).get("sections", [])

            if debug_container:
                debug_container.write(f"📦 Количество sections: **{len(sections)}**")

            media_count = 0
            skipped_none = 0

            for sec_idx, section in enumerate(sections):
                layout = section.get("layout_content", {})

                # medias может быть None!
                medias = layout.get("medias")
                if medias is None:
                    skipped_none += 1
                    # Попробуем другие ключи
                    if debug_container and sec_idx == 0:
                        debug_container.write(f"⚠️ Section {sec_idx}: medias = None")
                        debug_container.write(f"   Ключи layout_content: `{list(layout.keys())}`")
                        # Покажем что есть в layout
                        for key in layout:
                            val = layout[key]
                            if val is not None:
                                debug_container.write(f"   `{key}` = тип: {type(val).__name__}, значение: `{str(val)[:200]}`")
                    continue

                if not isinstance(medias, list):
                    if debug_container:
                        debug_container.write(f"⚠️ Section {sec_idx}: medias тип = {type(medias).__name__}")
                    continue

                if debug_container and sec_idx == 0:
                    debug_container.write(f"✅ Section {sec_idx}: **{len(medias)}** медиа")
                    if medias:
                        # Покажем структуру первого элемента
                        first = medias[0]
                        debug_container.write(f"   Ключи первого элемента: `{list(first.keys())}`")
                        if "media" in first:
                            m = first["media"]
                            debug_container.write(f"   Ключи media: `{list(m.keys())[:15]}`")
                            debug_container.write(f"   product_type: `{m.get('product_type')}`")
                            debug_container.write(f"   code: `{m.get('code')}`")
                            debug_container.write(f"   play_count: `{m.get('play_count')}`")
                            debug_container.write(f"   like_count: `{m.get('like_count')}`")
                            debug_container.write(f"   user: `{m.get('user', {}).get('username')}`")

                for item in medias:
                    media = item.get("media") if isinstance(item, dict) else None
                    if not media:
                        continue

                    code = media.get("code", "")
                    if not code:
                        continue

                    media_count += 1
                    play_count = media.get("play_count") or media.get("view_count") or 0
                    like_count = media.get("like_count") or 0
                    comment_count = media.get("comment_count") or 0
                    username = media.get("user", {}).get("username", "unknown")
                    full_name = media.get("user", {}).get("full_name", "")
                    is_verified = media.get("user", {}).get("is_verified", False)

                    caption = ""
                    cap_obj = media.get("caption")
                    if isinstance(cap_obj, dict):
                        caption = cap_obj.get("text", "")
                    elif isinstance(cap_obj, str):
                        caption = cap_obj

                    video_duration = media.get("video_duration") or 0

                    thumbnail = ""
                    candidates = media.get("image_versions2", {}).get("candidates", [])
                    if candidates and isinstance(candidates, list):
                        thumbnail = candidates[0].get("url", "")

                    reel = {
                        "shortcode": code,
                        "username": username,
                        "full_name": full_name,
                        "is_verified": is_verified,
                        "thumbnail_url": thumbnail,
                        "reel_url": f"https://www.instagram.com/reel/{code}/",
                        "profile_url": f"https://www.instagram.com/{username}/",
                        "views": int(play_count),
                        "likes": int(like_count),
                        "comments": int(comment_count),
                        "duration": round(float(video_duration), 1),
                        "caption": caption[:500] if caption else "",
                        "hashtag": tag_clean,
                        "engagement_rate": round(
                            (like_count + comment_count) / play_count * 100, 2
                        ) if play_count > 0 else 0
                    }
                    all_reels.append(reel)

            if debug_container:
                debug_container.write(f"📊 Sections с medias=None: **{skipped_none}**")
                debug_container.write(f"📊 Всего медиа обработано: **{media_count}**")
                debug_container.success(f"✅ Итого рилсов: **{len(all_reels)}**")

        except Exception as e:
            if debug_container:
                debug_container.error(f"💥 {type(e).__name__}: {e}")
            else:
                st.error(f"Ошибка: {e}")

        return all_reels[:max_results]


# ==========================================
# STREAMLIT
# ==========================================
st.set_page_config(page_title="Viral Reels Finder", page_icon="🎬", layout="wide")

st.sidebar.title("🎬 Viral Reels Finder")
st.sidebar.divider()

st.sidebar.subheader("🛡 Подключение")
use_proxy = st.sidebar.checkbox("Прокси")
proxy_url = None
if use_proxy:
    proxy_url = st.sidebar.text_input("Прокси URL", placeholder="http://user:pass@ip:port")
    if not proxy_url:
        proxy_url = None

st.sidebar.divider()
page = st.sidebar.radio("Навигация", [
    "🔍 Поиск по хэштегу",
    "📊 Обзор",
    "🔥 Топ вирусных",
    "🚀 Быстрорастущие",
    "📈 Трендовые хэштеги",
    "📋 Источники"
])

collector = RapidAPICollector(proxy=proxy_url)

if page == "🔍 Поиск по хэштегу":
    st.title("🔍 Поиск вирусных Reels по хэштегу")
    st.write("Введите хэштег и найдите самые вирусные Reels!")
    st.divider()

    col1, col2, col3 = st.columns([5, 2, 2])
    with col1:
        hashtag = st.text_input("Введите хэштег", placeholder="travel, fitness, food...")
    with col2:
        count = st.selectbox("Количество", [10, 20, 50, 100], index=1)
    with col3:
        st.write("")
        st.write("")
        search_btn = st.button("🔍 Найти", type="primary", use_container_width=True)

    st.write("🔥 **Популярные:**")
    popular_tags = ["travel", "fitness", "food", "fashion", "motivation", "nature", "art", "music"]
    tag_cols = st.columns(len(popular_tags))
    selected_tag = None
    for i, tag in enumerate(popular_tags):
        with tag_cols[i]:
            if st.button(f"#{tag}", key=f"pop_{i}", use_container_width=True):
                selected_tag = tag

    if selected_tag:
        hashtag = selected_tag
        search_btn = True

    st.divider()

    if search_btn and hashtag:
        hashtag_clean = hashtag.replace("#", "").strip()
        if not hashtag_clean:
            st.warning("⚠️ Введите хэштег!")
        else:
            debug = st.expander("🐛 Отладка API", expanded=True)

            with st.spinner(f"🔍 Ищем рилсы по #{hashtag_clean}..."):
                reels = collector.search_by_hashtag(hashtag_clean, max_results=count, debug_container=debug)

            if not reels:
                st.error("❌ Ничего не найдено. Смотрите отладку выше ☝️")
            else:
                st.success(f"✅ Найдено **{len(reels)}** рилсов по #{hashtag_clean}")
                st.balloons()

                # Метрики
                m1, m2, m3, m4 = st.columns(4)
                avg_views = sum(r["views"] for r in reels) // len(reels)
                m1.metric("📊 Всего", len(reels))
                m2.metric("👁 Ср. просмотры", f"{avg_views:,}")
                m3.metric("❤️ Лайков", f"{sum(r['likes'] for r in reels):,}")
                avg_er = sum(r["engagement_rate"] for r in reels) / len(reels)
                m4.metric("📈 Ср. ER", f"{avg_er:.2f}%")

                st.divider()

                # Сортировка
                sort_by = st.selectbox("Сортировка", [
                    "👁 По просмотрам", "❤️ По лайкам", "💬 По комментариям", "📈 По ER"
                ])
                sort_map = {
                    "👁 По просмотрам": "views",
                    "❤️ По лайкам": "likes",
                    "💬 По комментариям": "comments",
                    "📈 По ER": "engagement_rate"
                }
                reels.sort(key=lambda x: x[sort_map[sort_by]], reverse=True)

                st.divider()

                # Карточки
                for i, reel in enumerate(reels):
                    with st.container():
                        col_num, col_thumb, col_info, col_stats, col_link = st.columns([0.4, 1.2, 3.5, 3, 1.5])

                        with col_num:
                            st.markdown(f"### {i + 1}")

                        with col_thumb:
                            if reel.get("thumbnail_url"):
                                st.image(reel["thumbnail_url"], width=120)

                        with col_info:
                            v = " ✅" if reel["is_verified"] else ""
                            st.markdown(f"**@{reel['username']}**{v}")
                            if reel.get("full_name"):
                                st.caption(reel["full_name"])
                            if reel["caption"]:
                                cap = reel["caption"][:120] + "..." if len(reel["caption"]) > 120 else reel["caption"]
                                st.write(cap)
                            if reel.get("duration"):
                                st.caption(f"⏱ {reel['duration']} сек")

                        with col_stats:
                            s1, s2, s3, s4 = st.columns(4)
                            s1.metric("👁", f"{reel['views']:,}")
                            s2.metric("❤️", f"{reel['likes']:,}")
                            s3.metric("💬", f"{reel['comments']:,}")
                            s4.metric("📈", f"{reel['engagement_rate']}%")

                        with col_link:
                            st.link_button("▶️ Смотреть", reel["reel_url"], use_container_width=True)
                            st.link_button("👤 Профиль", reel["profile_url"], use_container_width=True)

                    st.divider()

                # Экспорт
                st.subheader("💾 Экспорт")
                df = pd.DataFrame(reels)
                c1, c2 = st.columns(2)
                with c1:
                    st.download_button(
                        "📥 Скачать CSV",
                        df.to_csv(index=False).encode("utf-8-sig"),
                        f"reels_{hashtag_clean}_{datetime.now().strftime('%Y%m%d')}.csv",
                        "text/csv",
                        use_container_width=True
                    )
                with c2:
                    st.download_button(
                        "📥 Скачать JSON",
                        json.dumps(reels, ensure_ascii=False, indent=2),
                        f"reels_{hashtag_clean}_{datetime.now().strftime('%Y%m%d')}.json",
                        "application/json",
                        use_container_width=True
                    )

elif page == "📋 Источники":
    st.title("📋 Источники данных")
    st.success("✅ API: Instagram Best Experience (RapidAPI)")
    st.write("Требуется VPN для доступа из некоторых регионов")
else:
    st.title(page)
    st.info("🔜 В разработке")