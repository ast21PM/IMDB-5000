import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os
from io import StringIO
import uuid

st.set_page_config(page_title="IMDB 5000 Movie Analytics", layout="wide")

@st.cache_data
def load_data():
    try:
        file_path = 'data/movie_metadata.csv'
        if not os.path.exists(file_path):
            st.error(f"Файл {file_path} не найден!")
            return pd.DataFrame()
        df = pd.read_csv(file_path)
        # Очистка данных
        df['genres'] = df['genres'].fillna('Unknown')
        df['actor_1_name'] = df['actor_1_name'].fillna('Unknown')
        df['actor_2_name'] = df['actor_2_name'].fillna('Unknown')
        df['actor_3_name'] = df['actor_3_name'].fillna('Unknown')
        df['title_year'] = df['title_year'].fillna(0).astype(int)
        df['budget'] = df['budget'].fillna(0)
        df['gross'] = df['gross'].fillna(0)
        df['imdb_score'] = df['imdb_score'].fillna(0)
        return df
    except Exception as e:
        st.error(f"Ошибка загрузки: {str(e)}")
        return pd.DataFrame()

df = load_data()

if not isinstance(df, pd.DataFrame) or df.empty:
    st.error("Критическая ошибка: Не удалось инициализировать DataFrame")
    st.stop()

st.title("🎬 IMDB 5000 Movie Analytics Dashboard")
st.markdown("""
Анализ данных о фильмах из датасета IMDB 5000.
* Источник данных: [IMDB 5000 Movie Dataset](https://www.kaggle.com/datasets/carolzhangdc/imdb-5000-movie-dataset)
* Автор: [ast_57]
""")

with st.sidebar:
    st.header("Фильтры")
    
    min_year = 1900
    max_year = 2020
    if 'title_year' in df.columns:
        min_year = int(df[df['title_year'] > 0]['title_year'].min())
        max_year = int(df[df['title_year'] > 0]['title_year'].max())

    year_range = st.slider(
        "Год выпуска",
        min_year, max_year,
        (min_year, max_year)
    )
    
    genres = ['All'] + sorted(set([genre.strip() for genres in df['genres'].str.split('|') for genre in genres if genre]))
    selected_genres = st.multiselect(
        "Жанры",
        options=genres,
        default=['All']
    )
    
    actors = ['All'] + sorted(set(df['actor_1_name'].tolist() + df['actor_2_name'].tolist() + df['actor_3_name'].tolist()))
    selected_actors = st.multiselect(
        "Актеры",
        options=actors,
        default=['All']
    )
    
    search_query = st.text_input("Поиск по названию фильма")
    show_stats = st.checkbox("Показать статистику")

try:
    filtered_data = df.copy()
    
    filtered_data = filtered_data[filtered_data['title_year'].between(year_range[0], year_range[1])]
    
    if 'All' not in selected_genres:
        filtered_data = filtered_data[
            filtered_data['genres'].str.contains('|'.join(selected_genres), case=False, na=False)
        ]
    
    if 'All' not in selected_actors:
        filtered_data = filtered_data[
            (filtered_data['actor_1_name'].isin(selected_actors)) |
            (filtered_data['actor_2_name'].isin(selected_actors)) |
            (filtered_data['actor_3_name'].isin(selected_actors))
        ]
    
    if search_query:
        filtered_data = filtered_data[
            filtered_data['movie_title'].str.contains(search_query, case=False, na=False)
        ]

except Exception as e:
    st.error(f"Ошибка фильтрации: {str(e)}")
    filtered_data = df.copy()

col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Всего фильмов", len(filtered_data))

with col2:
    avg_score = filtered_data['imdb_score'].mean()
    st.metric("Средний рейтинг IMDB", f"{avg_score:.1f}" if pd.notna(avg_score) else "Нет данных")

with col3:
    try:
        roi = ((filtered_data['gross'] - filtered_data['budget']) / filtered_data['budget'].replace(0, 1)).mean() * 100
        st.metric("Средний ROI", f"{roi:.1f}%" if pd.notna(roi) else "Нет данных")
    except Exception:
        st.metric("Средний ROI", "Нет данных")

if show_stats and not filtered_data.empty:
    st.subheader("Дополнительная статистика")
    st.write(f"**Самый популярный жанр:** {pd.Series([genre for genres in filtered_data['genres'].str.split('|') for genre in genres]).value_counts().index[0]}")
    st.write(f"**Самый частый актер:** {pd.concat([filtered_data['actor_1_name'], filtered_data['actor_2_name'], filtered_data['actor_3_name']]).value_counts().index[0]}")
    st.write(f"**Средний бюджет:** ${filtered_data['budget'].mean():,.0f}")
    st.write(f"**Средние сборы:** ${filtered_data['gross'].mean():,.0f}")

st.subheader("Зависимость бюджета и сборов")
if not filtered_data.empty and 'budget' in filtered_data.columns and 'gross' in filtered_data.columns:
    try:
        fig, ax = plt.subplots(figsize=(10, 6))
        sns.scatterplot(data=filtered_data, x='budget', y='gross', hue='imdb_score', size='imdb_score', ax=ax)
        ax.set_title("Бюджет vs Сборы (цвет и размер — рейтинг IMDB)", fontsize=16)
        ax.set_xlabel("Бюджет ($)", fontsize=12)
        ax.set_ylabel("Сборы ($)", fontsize=12)
        ax.grid(True, linestyle='--', alpha=0.7)
        plt.tight_layout()
        st.pyplot(fig)
    except Exception as e:
        st.warning(f"Не удалось построить график: {str(e)}")

st.subheader("Распределение рейтингов IMDB")
if not filtered_data.empty and 'imdb_score' in filtered_data.columns:
    try:
        fig, ax = plt.subplots(figsize=(10, 6))
        sns.histplot(data=filtered_data, x='imdb_score', bins=20, kde=True, color='teal', ax=ax)
        ax.set_title("Распределение рейтингов IMDB", fontsize=16)
        ax.set_xlabel("Рейтинг IMDB", fontsize=12)
        ax.set_ylabel("Количество фильмов", fontsize=12)
        ax.grid(True, linestyle='--', alpha=0.7)
        plt.tight_layout()
        st.pyplot(fig)
    except Exception as e:
        st.warning(f"Не удалось построить график: {str(e)}")

st.subheader("Результаты поиска")
if not filtered_data.empty:
    st.write(f"Найдено {len(filtered_data)} фильмов")
    st.dataframe(filtered_data[['movie_title', 'genres', 'actor_1_name', 'actor_2_name', 'actor_3_name', 'imdb_score', 'budget', 'gross']])
    
    csv = filtered_data.to_csv(index=False)
    st.download_button(
        label="Скачать отфильтрованные данные (CSV)",
        data=csv,
        file_name="imdb_filtered_data.csv",
        mime="text/csv"
    )
else:
    st.write("Нет данных, соответствующих фильтрам.")
