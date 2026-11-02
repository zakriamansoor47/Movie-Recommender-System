import pandas as pd
import streamlit as st
from sklearn.metrics.pairwise import cosine_similarity
import pickle
import requests

# Fetch movie poster
@st.cache_data(ttl=86400)
def fetch_poster(movie_id):
    try:
        url = f"https://api.themoviedb.org/3/movie/{movie_id}?api_key=8265bd1679663a7ea12ac168da84d2e8"
        response = requests.get(url)
        data = response.json()
        return data.get("poster_path", None)

    except Exception:
        return None
    
def recommend(movie, top_n=5):
    matches = movies[movies["title"].str.lower() == movie.strip().lower()]

    if matches.empty:
        print(f"Movie '{movie}' not found!")
        return

    movie_index = matches.index[0]
    distances = cosine_similarity(vectors[movie_index], vectors).flatten()
    movie_list = sorted(list(enumerate(distances)), reverse=True, key=lambda x: x[1])[1 : top_n + 1]
    recommended_movies = [movies.iloc[i[0]].title for i in movie_list]
    recommended_movies_posters = [fetch_poster(movies.iloc[i[0]].id) for i in movie_list]

    return recommended_movies, recommended_movies_posters
# def recommend(movie, top_n=5):
#     matches = movies[movies["title"].str.lower() == movie.strip().lower()]

#     if matches.empty:
#         print(f"Movie '{movie}' not found!")
#         return

#     movie_index = matches.index[0]
#     distances = cosine_similarity(vectors[movie_index], vectors)
#     movie_list = sorted(list(enumerate(distances[0])), reverse=True, key=lambda x: x[1])[1 : top_n + 1]
#     recommended_movies = [movies.iloc[i[0]].title for i in movie_list]
#     recommended_movies_posters = [fetch_poster(movies.iloc[i[0]].id) for i in movie_list]

#     return recommended_movies, recommended_movies_posters

st.set_page_config(page_title="Movie Recommender", page_icon="🎬", layout="wide")

# Load movies
@st.cache_resource
def load_movies():
    with open('movies.pkl', 'rb') as f:
        return pd.DataFrame(pickle.load(f))

movies = load_movies().reset_index(drop=True)

# Load vectors
@st.cache_resource
def load_vectors():
    with open('vectors.pkl', 'rb') as f:
        return pickle.load(f)

vectors = load_vectors()

# Search movies - return maximum 10 results
@st.cache_data
def search_movies(query):
    matches = movies[
        movies['title'].str.contains(
            query,
            case=False,
            na=False,
            regex=False
        )
    ]

    return matches['title'].drop_duplicates().head(20).tolist()
 
st.markdown(
    """

<style>
.stApp {
}

.block-container {
padding-top: 2rem;
padding-bottom: 3rem;
max-width: 1800px;
}

.main-title {
text-align: center;
font-size: 3.2rem;
font-weight: 800;
color: #ffffff;
margin-bottom: 0.2rem;
}

.subtitle {
text-align: center;
font-size: 1.2rem;
color: #b0b0b0;
margin-bottom: 2rem;
}

.movie-title {
font-size: 1rem;
font-weight: 700;
color: white;
min-height: 45px;
margin-top: 10px;
}

.movie-card {
background-color: #1c212b;
padding: 12px;
border-radius: 12px;
height: 100%;
border: 1px solid #303642;
}

div.stButton > button {
background-color: #e50914;
color: white;
border-radius: 8px;
border: none;
font-weight: bold;
height: 45px;
width: 100%;
}

div.stButton > button:hover {
background-color: #b20710;
color: white;
border: none;
}
</style>

""",
    unsafe_allow_html=True,
)

st.markdown( '<div class="main-title">🎬 Movie Recommender</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Discover movies you will love, one recommendation at a time.</div>', unsafe_allow_html=True,)
st.divider()
st.markdown("### 🔍 Find Your Next Movie")
col1, col2 = st.columns([3, 1])
with col1:
    search_query = st.text_input(
        "Search for a movie",
        placeholder="Start typing a movie name...",
        key="movie_search"
    )

    selected_movie = None

    if len(search_query.strip()) >= 2:

        search_results = search_movies(search_query.strip())

        if search_results:

            selected_movie = st.selectbox(
                "Search results",
                search_results,
                index=None,
                placeholder="Select a movie...",
                key="selected_movie"
            )

        else:
            st.info("No movies found.")

    elif search_query:
        st.caption("Type at least 2 characters...")
with col2:
    num_recommendations = st.number_input(
        "Number of recommendations", min_value=1, max_value=10, value=5
    )

st.write("")
if st.button("✨ Discover Similar Movies", use_container_width=True):
    if selected_movie:
        recommended_movies, recommended_movies_posters = recommend(selected_movie, int(num_recommendations))
        st.divider()
        st.markdown("## 🍿 Movies You Might Like")
        columns = st.columns(int(num_recommendations), gap="medium")

        for i, col in enumerate(columns):

            with col:

                movie_title = recommended_movies[i]
                poster = recommended_movies_posters[i]

                movie_data = movies[movies["title"] == movie_title].iloc[0]

                with st.container(border=True):

                    if poster:
                        st.image(f"https://image.tmdb.org/t/p/w300_and_h450_face{poster}", use_container_width=True)
                    else:
                        st.markdown("🎬 Poster unavailable")

                    st.markdown(f"<div style='text-align:center;' class='movie-title'>{movie_title}</div>",unsafe_allow_html=True,)
                    st.markdown(
                        f"""
                        <p style="text-align:center;">
                            <a href="https://www.imdb.com/title/{movie_data['imdb_id']}/" target="_blank">IMDb</a>
                            |
                            <a href="https://www.themoviedb.org/movie/{movie_data['id']}/" target="_blank">TMDB</a>
                        </p>
                        """,
                        unsafe_allow_html=True
                    )

    else:
        st.warning("Please select a movie first!")

    st.divider()
    st.markdown("<p style='text-align:center;color:#777;'>""🎬 Movie Recommender | Made with ❤️ by Zakria Mansoor""</p>", unsafe_allow_html=True,)
