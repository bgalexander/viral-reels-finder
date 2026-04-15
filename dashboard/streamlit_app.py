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
        response = requests.get(f"{API_BASE_URL}/{endpoint}", timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"Ошибка загрузки данных: {e}")
        return []


def fetch_stats() -> Dict:
    """Получить статистику"""
    try:
        response = requests.get(f"{API_BASE_URL}/stats", timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"Ошибка загрузки статистики: {e}")
        return {}


def trigger_collection_by_hashtag(hashtag: str, limit: int = 30):
    """Запустить сбор по хэштегу через API"""
    try:
        # Сначала добавляем источник
        response = requests.post(
            f"{API_BASE_URL}/sources",
            json={"source_type": "hashtag", "name": hashtag},
            timeout=10
        )

        # Затем запускаем сбор
        with st.spinner(f'🔍 Собираем Reels по #{hashtag}... Это может занять 1-2 минуты...'):
            response = requests.post(
                f"{API_BASE_URL}/collect/trigger",
                timeout=300  # 5 минут
            )
            response.raise_for_status()
            return True
    except requests.exceptions.Timeout:
        st.warning("⏱️ Сбор занимает больше времени чем ожидалось. Данные будут доступны через несколько минут.")
        return True
    except Exception as e:
        st.error(f"Ошибка сбора: {e}")
        return False


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
                st.image("https://via.placeholder.com/300x400?text=Instagram+Reel", use_column_width=True)

        with col2:
            # Кликабельная ссылка на Reel
            st.markdown(f"### 🎬 [{reel['reel_id']}]({reel['url']})")

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

            # Прямая ссылка
            st.markdown(f"🔗 [Открыть в Instagram]({reel['url']})")

        st.divider()


# Боковая панель


st.sidebar.title("🎬 Viral Reels Finder")
st.sidebar.markdown("---")

# Навигация
page = st.sidebar.radio(
    "Навигация",
    ["🔍 Поиск по хэштегу", "📊 Обзор", "🔥 Топ вирусных", "🚀 Быстрорастущие", "📈 Трендовые хэштеги", "⚙️ Источники"]
)

st.sidebar.markdown("---")

# Статистика в боковой панели
stats = fetch_stats()

if stats:
    st.sidebar.metric("Всего Reels", format_number(stats.get('total_reels', 0)))
    st.sidebar.metric("Вирусных Reels", format_number(stats.get('viral_reels', 0)))
    st.sidebar.metric("Avg Engagement", f"{stats.get('avg_engagement_rate', 0):.2%}")

st.sidebar.markdown("---")
st.sidebar.info("💡 Введите хэштег для поиска вирусных Reels")


# Главная область


# 🔍 ПОИСК ПО ХЭШТЕГУ (НОВАЯ СТРАНИЦА!)
if page == "🔍 Поиск по хэштегу":
    st.title("🔍 Поиск вирусных Reels по хэштегу")
    st.markdown("Введите хэштег и найдите самые вирусные Reels прямо сейчас!")

    st.markdown("---")

    # Форма поиска
    col1, col2, col3 = st.columns([3, 1, 1])

    with col1:
        hashtag_input = st.text_input(
            "Введите хэштег",
            placeholder="путешествие, fitness, food...",
            help="Введите хэштег БЕЗ символа #"
        )

    with col2:
        limit = st.selectbox("Количество", [10, 20, 30, 50], index=1)

    with col3:
        st.write("")  # spacing
        search_button = st.button("🔍 Найти", type="primary", use_container_width=True)

    st.markdown("---")

    # Популярные хэштеги (быстрый доступ)
    st.markdown("**🔥 Популярные хэштеги:**")
    popular_hashtags = ["travel", "fitness", "food", "fashion", "motivation", "nature", "art", "music"]

    cols = st.columns(8)
    for idx, tag in enumerate(popular_hashtags):
        with cols[idx]:
            if st.button(f"#{tag}", key=f"popular_{tag}", use_container_width=True):
                hashtag_input = tag
                search_button = True

    st.markdown("---")

    # Обработка поиска
    if search_button and hashtag_input:
        hashtag = hashtag_input.strip().lower().replace('#', '')

        st.info(f"🔍 Ищем вирусные Reels по хэштегу **#{hashtag}**...")

        # Сначала проверяем есть ли уже данные в БД
        existing_reels = fetch_data(f"hashtags/{hashtag}?limit={limit}")

        if existing_reels:
            st.success(f"✅ Найдено {len(existing_reels)} Reels по #{hashtag} в базе данных!")

            # Кнопка для обновления данных
            if st.button("🔄 Собрать свежие данные из Instagram"):
                if trigger_collection_by_hashtag(hashtag, limit):
                    st.success("✅ Сбор завершён! Обновите страницу.")
                    st.rerun()

            st.markdown("---")

            # Сортировка
            sort_by = st.selectbox(
                "Сортировать по:",
                ["Viral Score", "Просмотрам", "Лайкам", "Engagement Rate", "Дате публикации"]
            )

            # Применяем сортировку
            df = pd.DataFrame(existing_reels)
            if sort_by == "Viral Score":
                df = df.sort_values('viral_score', ascending=False)
            elif sort_by == "Просмотрам":
                df = df.sort_values('views', ascending=False)
            elif sort_by == "Лайкам":
                df = df.sort_values('likes', ascending=False)
            elif sort_by == "Engagement Rate":
                df = df.sort_values('engagement_rate', ascending=False)
            elif sort_by == "Дате публикации":
                df = df.sort_values('publish_date', ascending=False)

            sorted_reels = df.to_dict('records')

            # Показываем результаты
            for reel in sorted_reels:
                display_reel_card(reel)

        else:
            # Данных нет - предлагаем собрать
            st.warning(f"⚠️ Данных по #{hashtag} пока нет в базе")

            st.markdown("### Собрать данные из Instagram?")
            st.info(f"Мы соберём {limit} самых популярных Reels по хэштегу **#{hashtag}**")

            col1, col2 = st.columns([1, 3])
            with col1:
                if st.button("✅ Да, собрать!", type="primary", use_container_width=True):
                    if trigger_collection_by_hashtag(hashtag, limit):
                        st.success("✅ Сбор завершён! Обновляем страницу...")
                        time.sleep(2)
                        st.rerun()

            with col2:
                st.markdown("*Сбор займёт 1-2 минуты*")


# 📊 Обзор
elif page == "📊 Обзор":
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
        st.info("💡 Перейдите на страницу '🔍 Поиск по хэштегу' чтобы собрать данные")


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
        st.info("💡 Перейдите на страницу '🔍 Поиск по хэштегу' чтобы собрать данные")


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

        if hashtag_counts:
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

            # Поиск по хэштегу - ссылка на новую страницу
            st.markdown("---")
            st.info("💡 Хотите найти Reels по конкретному хэштегу? Перейдите на страницу '🔍 Поиск по хэштегу'")
        else:
            st.info("Данных о хэштегах пока нет")
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
                        response = requests.post(f"{API_BASE_URL}/collect/trigger", timeout=300)
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