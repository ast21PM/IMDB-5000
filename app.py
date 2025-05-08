import streamlit as st
import pandas as pd
import importlib.util
import subprocess
import sys
import os
from io import StringIO


def install_library(library_name):
    try:

        if importlib.util.find_spec(library_name) is None:
            st.warning(f"Библиотека {library_name} не найдена. Устанавливаем...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", library_name])
            st.success(f"Библиотека {library_name} успешно установлена!")
        else:
            pass 
    except Exception as e:
        st.error(f"Ошибка при установке {library_name}: {str(e)}")
        st.stop()


required_libraries = ["plotly", "pandas", "streamlit"]


for lib in required_libraries:
    install_library(lib)


import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(page_title="IMDB 5000 Movie Analytics", layout="wide")

@st.cache_data
def load_data():
    try:
        file_path = 'data/movie_metadata.csv'
        if not os.path.exists(file_path):
            st.error(f"Файл {file_path} не найден!")
            return pd.DataFrame()
        df = pd.read_csv(file_path)

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
    

    plot_type = st.selectbox(
        "Выберите тип графика",
        ["Бюджет vs Сборы (Скаттер)", "Сборы по жанрам (Box)", "Тренды по годам (Линейный)", "Распределение рейтингов (Гистограмма)"]
    )

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
        roi_data = filtered_data[(filtered_data['budget'] >= 1000) & (filtered_data['gross'] > 0)]
        if not roi_data.empty:
            roi = ((roi_data['gross'] - roi_data['budget']) / roi_data['budget']).median() * 100
            st.metric("Медианный ROI", f"{roi:.1f}%" if pd.notna(roi) else "Нет данных")
        else:
            st.metric("Медианный ROI", "Нет данных")
    except Exception:
        st.metric("Медианный ROI", "Нет данных")

if show_stats and not filtered_data.empty:
    st.subheader("Дополнительная статистика")
    st.write(f"**Самый популярный жанр:** {pd.Series([genre for genres in filtered_data['genres'].str.split('|') for genre in genres]).value_counts().index[0]}")
    st.write(f"**Самый частый актер:** {pd.concat([filtered_data['actor_1_name'], filtered_data['actor_2_name'], filtered_data['actor_3_name']]).value_counts().index[0]}")
    st.write(f"**Средний бюджет:** ${filtered_data['budget'].mean():,.0f}")
    st.write(f"**Средние сборы:** ${filtered_data['gross'].mean():,.0f}")

st.subheader("Визуализация данных")
if not filtered_data.empty:
    try:
        if plot_type == "Бюджет vs Сборы (Скаттер)":
            fig = px.scatter(
                filtered_data,
                x='budget',
                y='gross',
                color='imdb_score',
                size='imdb_score',
                hover_data=['movie_title', 'budget', 'gross', 'imdb_score'],
                log_x=True,
                log_y=True,
                title="Бюджет vs Сборы (цвет и размер — рейтинг IMDB)",
                labels={'budget': 'Бюджет ($)', 'gross': 'Сборы ($)', 'imdb_score': 'IMDB Score'},
                color_continuous_scale='Viridis',
                template='plotly_dark'
            )
            fig.update_layout(
                xaxis_tickformat='$%,.0f',
                yaxis_tickformat='$%,.0f',
                showlegend=True,
                margin=dict(l=50, r=50, t=50, b=50)
            )

        elif plot_type == "Сборы по жанрам (Box)":
            genre_data = filtered_data[['gross', 'genres']].copy()
            genre_data['genres'] = genre_data['genres'].str.split('|')
            genre_data = genre_data.explode('genres')
            top_genres = genre_data['genres'].value_counts().head(10).index
            genre_data = genre_data[genre_data['genres'].isin(top_genres)]
            
            fig = px.box(
                genre_data,
                x='genres',
                y='gross',
                title="Распределение сборов по жанрам (Топ-10)",
                labels={'genres': 'Жанр', 'gross': 'Сборы ($)'},
                template='plotly_dark',
                color='genres',
                color_discrete_sequence=px.colors.qualitative.Set2
            )
            fig.update_layout(
                yaxis_tickformat='$%,.0f',
                showlegend=False,
                margin=dict(l=50, r=50, t=50, b=50)
            )

        elif plot_type == "Тренды по годам (Линейный)":
            yearly_data = filtered_data.groupby('title_year')[['budget', 'gross']].mean().reset_index()
            yearly_data = yearly_data[yearly_data['title_year'] > 0]
            
            fig = go.Figure()
            fig.add_trace(
                go.Scatter(
                    x=yearly_data['title_year'],
                    y=yearly_data['budget'],
                    name='Средний бюджет',
                    line=dict(color='blue')
                )
            )
            fig.add_trace(
                go.Scatter(
                    x=yearly_data['title_year'],
                    y=yearly_data['gross'],
                    name='Средние сборы',
                    line=dict(color='orange')
                )
            )
            fig.update_layout(
                title="Тренды среднего бюджета и сборов по годам",
                xaxis_title="Год выпуска",
                yaxis_title="Сумма ($)",
                yaxis_tickformat='$%,.0f',
                template='plotly_dark',
                showlegend=True,
                margin=dict(l=50, r=50, t=50, b=50)
            )

        elif plot_type == "Распределение рейтингов (Гистограмма)":
            fig = px.histogram(
                filtered_data,
                x='imdb_score',
                nbins=20,
                title="Распределение рейтингов IMDB",
                labels={'imdb_score': 'Рейтинг IMDB', 'count': 'Количество фильмов'},
                template='plotly_dark',
                color_discrete_sequence=['teal']
            )
            fig.update_layout(
                showlegend=False,
                margin=dict(l=50, r=50, t=50, b=50)
            )

        st.plotly_chart(fig, use_container_width=True)
        
    except Exception as e:
        st.error(f"Не удалось построить график: {str(e)}")
        st.stop()

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