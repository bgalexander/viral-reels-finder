"""
Streamlit дашборд для визуализации вирусных Reels
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import requests
from typing import List, Dict
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Конфигурация страницы
st.set_page_config(
    page_title="Viral Reels Finder",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# API URL
API_BASE_URL = "http://localhost:8000/api/v1"


# Функции для работы с API


def fetch_data(endpoint: str) -> List[Dict]:
    """Получить данные из API"""
    try:
        response = requests.get(f"{API_BASE_URL}/{endpoint}")
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"Ошибка загрузки данных: {e}")
        return []


def fetch_stats() -> Dict:
    """Получить статистику"""
    try:
        response = requests.get(f"{API_BASE_URL}/stats")
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"Ошибка загрузки статистики: {e}")
        return {}


def format_number(num: int) -> str:
    """Форматировать большие числа"""
    if num >= 1_000_000:
        return f"{num / 1_000_000:.1f}M"
    elif num >= 1_000:
        return f"{num / 1_000:.1f}K"
    return str(num)


def display_reel_card(reel: Dict):
    """Отобразить карточку Reel"""
    with st.container():
        col1, col2 = st.columns([1, 2])

        with col1:
            # Превью видео
            if reel.get('video_url'):
                st.video(reel['video_url'])
            else:
                st.image("https://via.placeholder.com/300x400?text=No+Preview", use_column_width=True)

        with col2:
            # Информация о Reel
            st.markdown(f"### [{reel['reel_id']}]({reel['url']})")

            # Описание
            if reel.get('caption'):
                caption_preview = reel['caption'][:150] + "..." if len(reel['caption']) > 150 else reel['caption']
                st.markdown(f"*{caption_preview}*")

            # Метрики в колонках
            metric_col1, metric_col2, metric_col3, metric_col4 = st.columns(4)

            with metric_col1:
                st.metric("👁️ Просмотры", format_number(reel['views']))

            with metric_col2:
                st.metric("❤️ Лайки", format_number(reel['likes']))

            with metric_col3:
                st.metric("💬 Комментарии", format_number(reel['comments']))

            with metric_col4:
                st.metric("🔥 Viral Score", f"{reel['viral_score']:,.0f}")

            # Дополнительные метрики
            sub_col1, sub_col2, sub_col3 = st.columns(3)

            with sub_col1:
                st.metric("📊 Engagement", f"{reel['engagement_rate']:.2%}")

            with sub_col2:
                st.metric("🚀 Growth Score", f"{reel['growth_score']:,.0f}")

            with sub_col3:
                publish_date = datetime.fromisoformat(reel['publish_date'].replace('Z', '+00:00'))
                hours_ago = (datetime.now(publish_date.tzinfo) - publish_date).total_seconds() / 3600
                st.metric("⏰ Опубликовано", f"{int(hours_ago)}ч назад")

            # Хэштеги
            if reel.get('hashtags'):
                hashtags_str = " ".join([f"#{tag}" for tag in reel['hashtags'][:5]])
                st.markdown(f"**Хэштеги:** {hashtags_str}")

            # Аудио
            if reel.get('audio_name'):
                st.markdown(f"🎵 **Аудио:** {reel['audio_name']}")

            # Статус вирусности
            if reel['is_viral']:
                st.success("✅ ВИРУСНЫЙ КОНТЕНТ")

        st.divider()


# Боковая панель


st.sidebar.title("🎬 Viral Reels Finder")
st.sidebar.markdown("---")

# Навигация
page = st.sidebar.radio(
    "Навигация",
    ["📊 Обзор", "🔥 Топ вирусных", "🚀 Быстрорастущие", "📈 Трендовые хэштеги", "🎵 Трендовое аудио", "⚙️ Источники"]
)

st.sidebar.markdown("---")

# Статистика в боковой панели
stats = fetch_stats()

if stats:
    st.sidebar.metric("Всего Reels", format_number(stats.get('total_reels', 0)))
    st.sidebar.metric("Вирусных Reels", format_number(stats.get('viral_reels', 0)))
    st.sidebar.metric("Avg Engagement", f"{stats.get('avg_engagement_rate', 0):.2%}")

st.sidebar.markdown("---")
st.sidebar.info("Обновляется автоматически каждые 30 минут")

# Главная область


# 📊 Обзор
if page == "📊 Обзор":
    st.title("📊 Обзор системы")

    if stats:
        # Метрики в верхней части
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric(
                "🎬 Всего Reels",
                format_number(stats['total_reels']),
                delta=None
            )

        with col2:
            st.metric(
                "🔥 Вирусных",
                format_number(stats['viral_reels']),
                delta=f"{stats['viral_reels'] / max(stats['total_reels'], 1) * 100:.1f}%"
            )

        with col3:
            st.metric(
                "👁️ Всего просмотров",
                format_number(stats['total_views'])
            )

        with col4:
            st.metric(
                "❤️ Всего лайков",
                format_number(stats['total_likes'])
            )

        st.markdown("---")

        # Графики
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("📈 Топ 10 вирусных Reels")
            viral_reels = fetch_data("viral?limit=10")

            if viral_reels:
                df = pd.DataFrame(viral_reels)
                fig = px.bar(
                    df,
                    x='reel_id',
                    y='viral_score',
                    title='Viral Score по Reels',
                    labels={'viral_score': 'Viral Score', 'reel_id': 'Reel ID'}
                )
                st.plotly_chart(fig, use_container_width=True)

        with col2:
            st.subheader("🚀 Топ 10 быстрорастущих")
            trending_reels = fetch_data("trending?limit=10")

            if trending_reels:
                df = pd.DataFrame(trending_reels)
                fig = px.bar(
                    df,
                    x='reel_id',
                    y='growth_score',
                    title='Growth Score по Reels',
                    labels={'growth_score': 'Growth Score', 'reel_id': 'Reel ID'},
                    color='growth_score',
                    color_continuous_scale='Reds'
                )
                st.plotly_chart(fig, use_container_width=True)

        # Распределение engagement
        st.subheader("📊 Распределение Engagement Rate")
        all_reels = fetch_data("viral?limit=100")

        if all_reels:
            df = pd.DataFrame(all_reels)
            fig = px.histogram(
                df,
                x='engagement_rate',
                nbins=30,
                title='Распределение Engagement Rate',
                labels={'engagement_rate': 'Engagement Rate', 'count': 'Количество'}
            )
            st.plotly_chart(fig, use_container_width=True)


# 🔥 Топ вирусных
elif page == "🔥 Топ вирусных":
    st.title("🔥 Топ вирусных Reels")
    st.markdown("Reels с наивысшим viral score")
    st.markdown("---")

    # Фильтры
    col1, col2 = st.columns([3, 1])
    with col1:
        limit = st.slider("Количество Reels", 10, 100, 20, step=10)
    with col2:
        if st.button("🔄 Обновить"):
            st.rerun()

    st.markdown("---")

    # Загрузка данных
    reels = fetch_data(f"viral?limit={limit}")

    if reels:
        st.info(f"Найдено {len(reels)} вирусных Reels")

        for reel in reels:
            display_reel_card(reel)
    else:
        st.warning("Нет данных для отображения")


# 🚀 Быстрорастущие
elif page == "🚀 Быстрорастущие":
    st.title("🚀 Быстрорастущие Reels")
    st.markdown("Reels с наибольшей скоростью роста просмотров")
    st.markdown("---")

    # Фильтры
    col1, col2 = st.columns([3, 1])
    with col1:
        limit = st.slider("Количество Reels", 10, 100, 20, step=10)
    with col2:
        if st.button("🔄 Обновить"):
            st.rerun()

    st.markdown("---")

    # Загрузка данных
    reels = fetch_data(f"trending?limit={limit}")

    if reels:
        st.info(f"Найдено {len(reels)} быстрорастущих Reels")

        for reel in reels:
            display_reel_card(reel)
    else:
        st.warning("Нет данных для отображения")


# 📈 Трендовые хэштеги
elif page == "📈 Трендовые хэштеги":
    st.title("📈 Трендовые хэштеги")
    st.markdown("Самые популярные хэштеги среди вирусных Reels")
    st.markdown("---")

    # Получаем все вирусные Reels
    reels = fetch_data("viral?limit=100")

    if reels:
        # Собираем все хэштеги
        hashtag_counts = {}
        hashtag_scores = {}

        for reel in reels:
            if reel.get('hashtags'):
                for tag in reel['hashtags']:
                    hashtag_counts[tag] = hashtag_counts.get(tag, 0) + 1
                    if tag not in hashtag_scores:
                        hashtag_scores[tag] = []
                    hashtag_scores[tag].append(reel['viral_score'])

        # Создаем DataFrame
        hashtag_data = []
        for tag, count in hashtag_counts.items():
            avg_score = sum(hashtag_scores[tag]) / len(hashtag_scores[tag])
            hashtag_data.append({
                'hashtag': tag,
                'count': count,
                'avg_viral_score': avg_score
            })

        df = pd.DataFrame(hashtag_data)
        df = df.sort_values('count', ascending=False).head(20)

        # График
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("Топ 20 хэштегов по частоте")
            fig = px.bar(
                df,
                x='hashtag',
                y='count',
                title='Количество использований',
                labels={'count': 'Количество', 'hashtag': 'Хэштег'}
            )
            fig.update_xaxis(tickangle=-45)
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            st.subheader("Топ 20 хэштегов по Viral Score")
            df_sorted = df.sort_values('avg_viral_score', ascending=False)
            fig = px.bar(
                df_sorted,
                x='hashtag',
                y='avg_viral_score',
                title='Средний Viral Score',
                labels={'avg_viral_score': 'Avg Viral Score', 'hashtag': 'Хэштег'},
                color='avg_viral_score',
                color_continuous_scale='Reds'
            )
            fig.update_xaxis(tickangle=-45)
            st.plotly_chart(fig, use_container_width=True)

        # Таблица
        st.subheader("Детальная статистика")
        st.dataframe(
            df.sort_values('count', ascending=False),
            use_container_width=True,
            hide_index=True
        )

        # Поиск по хэштегу
        st.markdown("---")
        st.subheader("🔍 Поиск Reels по хэштегу")

        selected_hashtag = st.selectbox(
            "Выберите хэштег",
            options=df['hashtag'].tolist()
        )

        if st.button("Показать Reels"):
            hashtag_reels = fetch_data(f"hashtags/{selected_hashtag}")

            if hashtag_reels:
                st.success(f"Найдено {len(hashtag_reels)} Reels с хэштегом #{selected_hashtag}")

                for reel in hashtag_reels[:10]:  # Показываем первые 10
                    display_reel_card(reel)
    else:
        st.warning("Нет данных для отображения")


# 🎵 Трендовое аудио
elif page == "🎵 Трендовое аудио":
    st.title("🎵 Трендовое аудио")
    st.markdown("Самые популярные аудиодорожки среди вирусных Reels")
    st.markdown("---")

    # Получаем все вирусные Reels
    reels = fetch_data("viral?limit=100")

    if reels:
        # Собираем все аудио
        audio_counts = {}
        audio_scores = {}

        for reel in reels:
            audio = reel.get('audio_name')
            if audio and audio.strip():
                audio_counts[audio] = audio_counts.get(audio, 0) + 1
                if audio not in audio_scores:
                    audio_scores[audio] = []
                audio_scores[audio].append(reel['viral_score'])

        if audio_counts:
            # Создаем DataFrame
            audio_data = []
            for audio, count in audio_counts.items():
                avg_score = sum(audio_scores[audio]) / len(audio_scores[audio])
                audio_data.append({
                    'audio': audio[:50] + "..." if len(audio) > 50 else audio,
                    'full_audio': audio,
                    'count': count,
                    'avg_viral_score': avg_score
                })

            df = pd.DataFrame(audio_data)
            df = df.sort_values('count', ascending=False).head(20)

            # График
            st.subheader("Топ 20 аудиодорожек")
            fig = px.bar(
                df,
                y='audio',
                x='count',
                orientation='h',
                title='Количество использований',
                labels={'count': 'Количество', 'audio': 'Аудио'},
                color='avg_viral_score',
                color_continuous_scale='Viridis'
            )
            st.plotly_chart(fig, use_container_width=True)

            # Таблица
            st.subheader("Детальная статистика")
            display_df = df[['full_audio', 'count', 'avg_viral_score']].copy()
            display_df.columns = ['Аудио', 'Использований', 'Avg Viral Score']
            st.dataframe(
                display_df,
                use_container_width=True,
                hide_index=True
            )
        else:
            st.info("Информация об аудио не доступна для текущих Reels")
    else:
        st.warning("Нет данных для отображения")


# ⚙️ Источники
elif page == "⚙️ Источники":
    st.title("⚙️ Управление источниками")
    st.markdown("Добавляйте и управляйте источниками для сбора Reels")
    st.markdown("---")

    # Форма добавления нового источника
    st.subheader("➕ Добавить новый источник")

    with st.form("add_source_form"):
        col1, col2, col3 = st.columns([2, 2, 1])

        with col1:
            source_type = st.selectbox(
                "Тип источника",
                ["hashtag", "account"]
            )

        with col2:
            source_name = st.text_input(
                "Название",
                placeholder="travel (для хэштега) или username (для аккаунта)"
            )

        with col3:
            st.write("")  # Spacing
            st.write("")  # Spacing
            submit = st.form_submit_button("Добавить", use_container_width=True)

        if submit and source_name:
            try:
                response = requests.post(
                    f"{API_BASE_URL}/sources",
                    json={"source_type": source_type, "name": source_name}
                )
                response.raise_for_status()
                st.success(f"✅ Источник {source_type}:{source_name} добавлен!")
                st.rerun()
            except Exception as e:
                st.error(f"Ошибка добавления источника: {e}")

    st.markdown("---")

    # Список источников
    st.subheader("📋 Текущие источники")

    sources = fetch_data("sources")

    if sources:
        for source in sources:
            with st.container():
                col1, col2, col3, col4, col5 = st.columns([2, 2, 2, 2, 1])

                with col1:
                    icon = "📌" if source['source_type'] == 'hashtag' else "👤"
                    st.markdown(f"**{icon} {source['name']}**")

                with col2:
                    st.text(f"Тип: {source['source_type']}")

                with col3:
                    st.text(f"Собрано: {source['total_reels_collected']}")

                with col4:
                    if source['last_scraped_at']:
                        last_scraped = datetime.fromisoformat(source['last_scraped_at'].replace('Z', '+00:00'))
                        st.text(f"Обновлено: {last_scraped.strftime('%d.%m %H:%M')}")
                    else:
                        st.text("Еще не собирали")

                with col5:
                    status = "🟢" if source['is_active'] else "🔴"
                    if st.button(status, key=f"toggle_{source['id']}"):
                        try:
                            response = requests.post(
                                f"{API_BASE_URL}/sources/{source['id']}/toggle"
                            )
                            response.raise_for_status()
                            st.rerun()
                        except Exception as e:
                            st.error(f"Ошибка: {e}")

                st.divider()

        # Управление сбором
        st.markdown("---")
        st.subheader("🔄 Управление сбором")

        col1, col2 = st.columns(2)

        with col1:
            if st.button("▶️ Запустить сбор вручную", use_container_width=True):
                with st.spinner("Идет сбор данных..."):
                    try:
                        response = requests.post(f"{API_BASE_URL}/collect/trigger")
                        response.raise_for_status()
                        st.success("✅ Сбор данных завершен!")
                    except Exception as e:
                        st.error(f"Ошибка: {e}")

        with col2:
            if st.button("🔄 Обновить метрики", use_container_width=True):
                with st.spinner("Обновление метрик..."):
                    try:
                        response = requests.post(f"{API_BASE_URL}/metrics/update")
                        response.raise_for_status()
                        st.success("✅ Метрики обновлены!")
                    except Exception as e:
                        st.error(f"Ошибка: {e}")
    else:
        st.info("Источники еще не добавлены. Добавьте первый источник выше!")

# Футер
st.sidebar.markdown("---")
st.sidebar.markdown("Made with ❤️ using Streamlit")