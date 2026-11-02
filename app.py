import pandas as pd
import streamlit as st
from sklearn.metrics.pairwise import cosine_similarity
import pickle
import requests
import html
import re
import difflib

# Fetch movie poster
@st.cache_data(ttl=86400)
def fetch_poster(movie_id):
    try:
        url = f"https://api.themoviedb.org/3/movie/{movie_id}?api_key=8265bd1679663a7ea12ac168da84d2e8"
        response = requests.get(url, timeout=5)
        data = response.json()
        return data.get("poster_path", None)
    except Exception:
        return None

def recommend(movie, top_n=5):
    matches = movies[movies["title"].str.lower() == movie.strip().lower()]

    if matches.empty:
        return [], []

    movie_index = matches.index[0]
    distances = cosine_similarity(vectors[movie_index], vectors).flatten()
    movie_list = sorted(list(enumerate(distances)), reverse=True, key=lambda x: x[1])[1 : top_n + 1]
    recommended_movies = [movies.iloc[i[0]].title for i in movie_list]
    recommended_movies_posters = [fetch_poster(movies.iloc[i[0]].id) for i in movie_list]

    return recommended_movies, recommended_movies_posters

@st.cache_data
def recommend_by_title(target_title, top_n=5):
    target_clean = target_title.strip()
    target_lower = target_clean.lower()
    
    # Extract franchise prefix before delimiters (e.g., :, -, –)
    prefix = re.split(r'[:\-–—]', target_clean)[0].strip()
    prefix_lower = prefix.lower()
    
    stopwords = {'the', 'a', 'an', 'and', 'or', 'of', 'in', 'on', 'at', 'to', 'for', 'with', 'from', 'by', 'vs', 'part', 'vol', 'volume'}
    words = [w for w in re.findall(r'[a-zA-Z0-9]+', target_lower) if w not in stopwords and len(w) > 1]
    
    # Fast filtering of candidate pool using regex
    patterns = []
    if len(prefix_lower) >= 3:
        patterns.append(re.escape(prefix_lower))
    elif len(target_lower) >= 3:
        patterns.append(re.escape(target_lower))
        
    for w in sorted(words, key=len, reverse=True)[:3]:
        if len(w) >= 4:
            patterns.append(re.escape(w))
            
    if patterns:
        combined_regex = '|'.join(patterns)
        candidate_df = movies[movies['title'].str.contains(combined_regex, case=False, na=False, regex=True)]
    else:
        candidate_df = movies
        
    candidate_titles = candidate_df['title'].drop_duplicates().tolist()
    
    target_words_set = set(words)
    scored = []
    
    for cand in candidate_titles:
        cand_clean = cand.strip()
        cand_lower = cand_clean.lower()
        if cand_lower == target_lower:
            continue
            
        cand_words = [w for w in re.findall(r'[a-zA-Z0-9]+', cand_lower) if w not in stopwords and len(w) > 1]
        cand_words_set = set(cand_words)
        
        seq_ratio = difflib.SequenceMatcher(None, target_lower, cand_lower).ratio()
        
        if target_words_set and cand_words_set:
            overlap = len(target_words_set & cand_words_set)
            token_ratio = (2.0 * overlap) / (len(target_words_set) + len(cand_words_set))
        else:
            token_ratio = 0.0
            
        prefix_bonus = 0.0
        if len(prefix_lower) >= 3:
            if cand_lower.startswith(prefix_lower):
                prefix_bonus = 0.4
            elif prefix_lower in cand_lower:
                prefix_bonus = 0.2
                
        len_penalty = 0.0
        if len(cand_lower) < len(target_lower) * 0.4 and len(cand_words) == 1:
            len_penalty = -0.3
            
        total_score = (seq_ratio * 0.4) + (token_ratio * 0.4) + prefix_bonus + len_penalty
        if total_score > 0.35:
            scored.append((cand, total_score))
            
    scored.sort(key=lambda x: x[1], reverse=True)
    similar_titles = [c[0] for c in scored[:top_n]]
    
    # Fallback to difflib close matches if fewer candidates were scored
    if len(similar_titles) < top_n:
        all_unique = movies['title'].dropna().drop_duplicates().tolist()
        close = difflib.get_close_matches(target_clean, all_unique, n=top_n * 2, cutoff=0.3)
        for c in close:
            if c.lower() != target_lower and c not in similar_titles:
                similar_titles.append(c)
                if len(similar_titles) == top_n:
                    break
                    
    similar_posters = []
    for t in similar_titles:
        matching = movies[movies['title'] == t]
        if not matching.empty:
            similar_posters.append(fetch_poster(matching.iloc[0].id))
        else:
            similar_posters.append(None)
            
    return similar_titles, similar_posters

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

# Search movies - return maximum 20 results
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

/* Selected Movie Preview Card above Search Box */
.selected-movie-preview {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    background-color: #1c212b;
    border: 1px solid #303642;
    border-radius: 12px;
    padding: 16px 20px;
    margin: 10px auto 25px auto;
    max-width: 280px;
    box-shadow: 0 6px 20px rgba(0, 0, 0, 0.45);
    text-align: center;
    transition: border-color 0.2s ease, box-shadow 0.2s ease;
}

.selected-movie-preview:hover {
    border-color: #e50914;
    box-shadow: 0 8px 24px rgba(229, 9, 20, 0.25);
}

.selected-movie-badge {
    color: #e50914;
    font-size: 0.8rem;
    font-weight: 800;
    text-transform: uppercase;
    letter-spacing: 1.5px;
    margin-bottom: 10px;
}

.selected-movie-poster {
    width: 100%;
    aspect-ratio: 2 / 3;
    object-fit: cover;
    border-radius: 8px;
    box-shadow: 0 6px 16px rgba(0, 0, 0, 0.6);
    margin-bottom: 12px;
}

.selected-movie-poster-placeholder {
    width: 100%;
    aspect-ratio: 2 / 3;
    border-radius: 8px;
    background: linear-gradient(145deg, #1f2532 0%, #151922 100%);
    border: 1px dashed #303642;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    color: #8c96a8;
    font-size: 0.85rem;
    margin-bottom: 12px;
    box-sizing: border-box;
    padding: 10px;
}

.selected-movie-title {
    color: #ffffff;
    font-size: 1.15rem;
    font-weight: 700;
    margin: 0 0 8px 0;
    line-height: 1.3;
}

/* Horizontal Scrollable Carousel */
.movie-carousel-container {
    display: flex;
    flex-direction: row;
    overflow-x: auto;
    overflow-y: hidden;
    gap: 16px;
    padding: 10px 0 20px 0;
    scroll-behavior: smooth;
    -webkit-overflow-scrolling: touch;
    width: 100%;
    box-sizing: border-box;
}

/* Custom Scrollbar for Carousel */
.movie-carousel-container::-webkit-scrollbar {
    height: 10px;
}
.movie-carousel-container::-webkit-scrollbar-track {
    background: #141820;
    border-radius: 6px;
}
.movie-carousel-container::-webkit-scrollbar-thumb {
    background: #e50914;
    border-radius: 6px;
    border: 2px solid #141820;
}
.movie-carousel-container::-webkit-scrollbar-thumb:hover {
    background: #ff1e2b;
}

/* Exactly 5 items visible per screen (with 4 gaps of 16px = 64px total gap) */
.movie-carousel-card {
    flex: 0 0 calc((100% - 64px) / 5);
    min-width: calc((100% - 64px) / 5);
    max-width: calc((100% - 64px) / 5);
    box-sizing: border-box;
    background-color: #1c212b;
    border: 1px solid #303642;
    border-radius: 12px;
    padding: 12px;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    transition: transform 0.2s ease, border-color 0.2s ease, box-shadow 0.2s ease;
}

.movie-carousel-card:hover {
    transform: translateY(-4px);
    border-color: #e50914;
    box-shadow: 0 8px 20px rgba(229, 9, 20, 0.2);
}

.carousel-poster {
    width: 100%;
    aspect-ratio: 2 / 3;
    object-fit: cover;
    border-radius: 8px;
    background-color: #11141a;
    display: block;
}

.carousel-poster-placeholder {
    width: 100%;
    aspect-ratio: 2 / 3;
    border-radius: 8px;
    background: linear-gradient(145deg, #1f2532 0%, #151922 100%);
    border: 1px dashed #303642;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    color: #8c96a8;
    font-size: 0.85rem;
    font-weight: 500;
    text-align: center;
    padding: 12px;
    box-sizing: border-box;
}

.movie-carousel-card .movie-title {
    font-size: 0.95rem;
    font-weight: 700;
    color: #ffffff;
    text-align: center;
    margin: 10px 0 6px 0;
    line-height: 1.35;
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
    overflow: hidden;
    text-overflow: ellipsis;
    min-height: 2.7em;
}

.movie-links {
    text-align: center;
    font-size: 0.85rem;
    margin-top: auto;
    padding-top: 8px;
    border-top: 1px solid #282f3c;
}

.movie-links a {
    color: #f5c518;
    text-decoration: none;
    font-weight: 600;
}

.movie-links a.tmdb-link {
    color: #01b4e4;
}

.movie-links a:hover {
    text-decoration: underline;
}

.link-divider {
    color: #555e70;
    margin: 0 6px;
}

/* Responsive adjustment for small screens */
@media (max-width: 900px) {
    .movie-carousel-card {
        flex: 0 0 180px !important;
        min-width: 180px !important;
        max-width: 180px !important;
    }
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

def render_movie_carousel(movie_titles, movie_posters):
    if not movie_titles:
        st.info("No movies found.")
        return

    cards_html = []
    for title, poster in zip(movie_titles, movie_posters):
        matching = movies[movies["title"] == title]
        movie_data = matching.iloc[0] if not matching.empty else {}
        
        safe_title = html.escape(str(title))
        
        if poster:
            poster_html = f'<img src="https://image.tmdb.org/t/p/w300_and_h450_face{poster}" alt="{safe_title}" class="carousel-poster" loading="lazy" />'
        else:
            poster_html = '<div class="carousel-poster-placeholder"><div style="font-size:2rem;margin-bottom:4px;">🎬</div><div>Poster Unavailable</div></div>'

        imdb_id = movie_data.get("imdb_id") if isinstance(movie_data, pd.Series) else None
        tmdb_id = movie_data.get("id") if isinstance(movie_data, pd.Series) else None

        imdb_link = f'<a href="https://www.imdb.com/title/{html.escape(str(imdb_id))}/" target="_blank">IMDb</a>' if (pd.notna(imdb_id) and str(imdb_id).strip().lower() != 'nan') else ''
        tmdb_link = f'<a href="https://www.themoviedb.org/movie/{html.escape(str(tmdb_id))}/" target="_blank" class="tmdb-link">TMDB</a>' if pd.notna(tmdb_id) else ''

        divider = '<span class="link-divider">|</span>' if (imdb_link and tmdb_link) else ''
        links_html = f'<div class="movie-links">{imdb_link}{divider}{tmdb_link}</div>' if (imdb_link or tmdb_link) else ''

        card_html = f'<div class="movie-carousel-card">{poster_html}<div class="movie-title" title="{safe_title}">{safe_title}</div>{links_html}</div>'
        cards_html.append(card_html)

    carousel_html = f'<div class="movie-carousel-container">{"".join(cards_html)}</div>'
    st.html(carousel_html)

st.markdown('<div class="main-title">🎬 Movie Recommender</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Discover movies you will love, one recommendation at a time.</div>', unsafe_allow_html=True)
st.divider()

# Container for selected movie poster and title above the search box
selected_movie_container = st.container()

st.markdown("### Find Your Next Movie")
col1, col2, col3 = st.columns([2.5, 2.5, 1.2])

with col1:
    search_query = st.text_input(
        "Search for a movie",
        placeholder="Start typing a movie name...",
        key="movie_search"
    )
    if 0 < len(search_query.strip()) < 2:
        st.caption("Type at least 2 characters...")

with col2:
    search_results = []
    if len(search_query.strip()) >= 2:
        search_results = search_movies(search_query.strip())

    selected_movie = st.selectbox(
        "Search results",
        options=search_results,
        index=None,
        placeholder="Select a movie..." if search_results else ("No movies found" if len(search_query.strip()) >= 2 else "Type movie name first..."),
        disabled=len(search_results) == 0,
        key="selected_movie"
    )

with col3:
    num_recommendations = st.number_input(
        "Number of recommendations", min_value=5, max_value=20, value=5, step=1
    )

# Render selected movie poster and title above the search box
if selected_movie:
    with selected_movie_container:
        sel_matches = movies[movies["title"] == selected_movie]
        if not sel_matches.empty:
            sel_data = sel_matches.iloc[0]
            sel_poster = fetch_poster(sel_data["id"])
            sel_imdb = sel_data.get("imdb_id")
            sel_tmdb = sel_data.get("id")

            safe_sel_title = html.escape(str(selected_movie))

            if sel_poster:
                poster_html = f'<img src="https://image.tmdb.org/t/p/w300_and_h450_face{sel_poster}" alt="{safe_sel_title}" class="selected-movie-poster" />'
            else:
                poster_html = '<div class="selected-movie-poster-placeholder"><div style="font-size:2rem;margin-bottom:4px;">🎬</div><div>Poster Unavailable</div></div>'

            imdb_html = f'<a href="https://www.imdb.com/title/{html.escape(str(sel_imdb))}/" target="_blank">IMDb</a>' if (pd.notna(sel_imdb) and str(sel_imdb).strip().lower() != 'nan') else ''
            tmdb_html = f'<a href="https://www.themoviedb.org/movie/{html.escape(str(sel_tmdb))}/" target="_blank" class="tmdb-link">TMDB</a>' if pd.notna(sel_tmdb) else ''

            divider = ' <span class="link-divider">|</span> ' if (imdb_html and tmdb_html) else ''
            links_html = f'<div class="movie-links">{imdb_html}{divider}{tmdb_html}</div>' if (imdb_html or tmdb_html) else ''

            preview_html = (
                f'<div class="selected-movie-preview">'
                f'<div class="selected-movie-badge">Selected Movie</div>'
                f'{poster_html}'
                f'<div class="selected-movie-title">{safe_sel_title}</div>'
                f'{links_html}'
                f'</div>'
            )
            st.html(preview_html)

st.write("")
discover_clicked = st.button("✨ Discover Similar Movies", width='stretch')

if discover_clicked:
    if selected_movie:
        st.session_state["submitted_movie"] = selected_movie
        st.session_state["submitted_num"] = int(num_recommendations)
    else:
        st.warning("Please select a movie first!")
        if "submitted_movie" in st.session_state:
            del st.session_state["submitted_movie"]

active_movie = st.session_state.get("submitted_movie")
active_num = st.session_state.get("submitted_num", int(num_recommendations))

if active_movie:
    if selected_movie and selected_movie != active_movie:
        st.info(f"💡Note: Currently showing results for **{active_movie}**. Click **Discover Similar Movies** to update for **{selected_movie}**.")

    # 1. Content-based recommendations
    with st.spinner("Finding recommended movies..."):
        rec_movies, rec_posters = recommend(active_movie, active_num)

    st.divider()
    st.markdown("## Movies You Might Like")
    st.caption(f"Top {len(rec_movies)} recommendations based on storyline, genre, and cast similarity (scroll horizontally to see more)")
    render_movie_carousel(rec_movies, rec_posters)

    # 2. Similar movies by title
    with st.spinner("Finding similar movies by title..."):
        title_movies, title_posters = recommend_by_title(active_movie, active_num)

    st.divider()
    st.markdown("## Similar Movies by Title")
    st.caption(f"Top {len(title_movies)} movies with similar titles, sequels, or franchise editions (scroll horizontally to see more)")
    render_movie_carousel(title_movies, title_posters)

st.divider()
st.markdown("<p style='text-align:center;color:#777;'>🎬 Movie Recommender | Made with ❤️ by Zakria Mansoor</p>", unsafe_allow_html=True)
