# 🎬 Movie Recommender System

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://movie-recommender-system-by-zakria.streamlit.app/)
![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python&logoColor=white)
![Scikit-Learn](https://img.shields.io/badge/Scikit--Learn-Machine%20Learning-orange?logo=scikit-learn&logoColor=white)
![Pandas](https://img.shields.io/badge/Pandas-Data%20Analysis-150458?logo=pandas&logoColor=white)
![TMDB API](https://img.shields.io/badge/TMDB-API%20Integration-01b4e4?logo=themoviedatabase&logoColor=white)

Discover movies you'll love with a machine-learning-powered recommender that analyzes over **389,000+ movies** to deliver personalized recommendations and franchise matches in real-time.

👉 **[Launch Live Demo](https://movie-recommender-system-by-zakria.streamlit.app/)**

---

## 📌 Table of Contents
- [What is Movie Recommender System?](#-what-is-movie-recommender-system)
- [What Does It Do?](#-what-does-it-do)
- [How Does It Work?](#-how-does-it-work)
- [How Big is the Dataset?](#-how-big-is-the-dataset)
- [Key Features](#-key-features)
- [Tech Stack](#-tech-stack)
- [Installation & Local Setup](#-installation--local-setup)
- [Project Structure](#-project-structure)
- [Author](#-author)

---

## 📖 What is Movie Recommender System?

The **Movie Recommender System** is an end-to-end content-based movie recommendation platform built with Python, Natural Language Processing (NLP), Scikit-Learn, and Streamlit.

Unlike basic collaborative filtering systems that require huge user interaction histories (ratings, likes, views), this system utilizes **content-based filtering**. It analyzes the intrinsic attributes of each movie—such as storyline overview, genres, cast members, directors, writers, and thematic keywords—to understand the movie's DNA and recommend films with similar themes and stylistic elements.

---

## 🎯 What Does It Do?

1. **Intelligent Movie Search:** Search through hundreds of thousands of titles in real-time with instant auto-suggestions.
2. **Selected Movie Spotlight:** Select any movie to instantly preview its official TMDB poster, title, and quick links to IMDb and TMDB above the search bar.
3. **Dual Recommendation Engine:**
   - **🍿 Movies You Might Like (Content-Based):** Discovers films that share similar themes, moods, storylines, genres, and cast/crew combinations using TF-IDF vectorization and Cosine Similarity.
   - **🏷️ Similar Movies by Title (Franchise & Sequel Matcher):** Automatically finds direct sequels, prequels, spin-offs, and title-related releases (e.g., searching for *Toy Story* finds *Toy Story 2*, *Toy Story 3*, *Toy Story 4*).
4. **Netflix-Style Interactive Carousel:** Displays recommendations in an elegant, horizontally scrollable shelf showing exactly **5 movies at a time** on screen, complete with official movie posters and direct links.
5. **Configurable Output Count:** Customize how many recommendations to generate (from 5 to 20 films).

---

## 🧠 How Does It Work?

```
[Raw Metadata + Credits + Keywords]
                 │
                 ▼
[Data Cleaning & Feature Engineering] (Overview + Genres + Cast + Crew + Keywords)
                 │
                 ▼
[Text Normalization & Stemming] (PorterStemmer)
                 │
                 ▼
[TF-IDF Vectorization] (20,000 features, 1-2 n-grams) ──► vectors.pkl
                 │
                 ▼
[Cosine Similarity & Title Matching] ──► Real-time Recommendations
                 │
                 ▼
[TMDB Poster API & Streamlit Web App] ──► Interactive UI
```

### 1. Data Cleaning & Feature Engineering
- Multiple data sources were merged on movie IDs to create an extensive representation for each film.
- Extracted and combined:
  - **Overview:** Plot synopsis and narrative summary.
  - **Genres:** Action, Sci-Fi, Thriller, Animation, etc.
  - **Keywords:** High-relevance plot descriptors and tags.
  - **Cast:** Top credited actors.
  - **Crew:** Directors and writers.
- All elements were combined into a unified, consolidated **`tags`** string.

### 2. NLP Pipeline & Stemming
- Text was normalized to lowercase and stripped of punctuation.
- **Porter Stemmer (`nltk.stem.porter.PorterStemmer`)** was applied to reduce words to their linguistic root forms (e.g., `"love"`, `"loving"`, `"loved"` $\rightarrow$ `"love"`), preventing redundant token dimensions.

### 3. Vectorization with TF-IDF
- Used **`TfidfVectorizer`** from Scikit-Learn to convert movie tags into high-dimensional numerical vectors:
  - `max_features = 20,000` (focusing on the most informative terms across the corpus).
  - `stop_words = 'english'` (filtering out uninformative stopwords).
  - `ngram_range = (1, 2)` (capturing both single words and compound phrases like "science fiction" or "dark knight").

### 4. Mathematical Similarity Computation
- Similarity between movies is calculated in real time using **Cosine Similarity**:
  $$\text{Cosine Similarity}(\mathbf{A}, \mathbf{B}) = \frac{\mathbf{A} \cdot \mathbf{B}}{\|\mathbf{A}\| \|\mathbf{B}\|}$$
- This measures the cosine of the angle between two sparse TF-IDF vectors in the 20,000-dimensional space, yielding a score between 0 and 1.
- Top $N$ highest-scoring movies (excluding the query movie itself) are returned.

### 5. Title & Franchise Similarity Algorithm
- Evaluates title tokens, series prefixes (splitting across `:`, `-`, `–`), token Jaccard overlap, and Levenshtein sequence matching to identify related franchise editions, spin-offs, and titles.

### 6. Dynamic Poster Fetching & Caching
- Connects to **The Movie Database (TMDB) API** to fetch high-resolution posters on demand.
- Poster requests are cached using `@st.cache_data(ttl=86400)` to ensure fast load times and minimal external network overhead.

---

## 📊 How Big is the Dataset?

| Metric | Details |
|---|---|
| **Raw Movie Records** | Over **440,000+** films compiled from TMDB and IMDb datasets |
| **Final Indexed Movies** | **389,448** clean, unique movie entries in `movies.pkl` |
| **Unique Titles** | **333,655+** distinct titles available for search |
| **TF-IDF Sparse Matrix** | **(389,448 × 20,000)** vector space in `vectors.pkl` |
| **Features Extracted** | Title, IMDb ID, TMDB ID, Overview, Genres, Keywords, Cast, Crew |
| **Compressed Artifact Size** | ~300+ MB model & index bundle (`movies.pkl` + `vectors.pkl`) |

---

## 💻 Tech Stack

- **Frontend & Web Framework:** [Streamlit](https://streamlit.io/)
- **Core Language:** Python 3.10+
- **Machine Learning & NLP:** [Scikit-Learn](https://scikit-learn.org/), [NLTK](https://www.nltk.org/)
- **Data Manipulation:** [Pandas](https://pandas.pydata.org/), [NumPy](https://numpy.org/), [SciPy](https://scipy.org/)
- **External API:** [The Movie Database (TMDB) API](https://www.themoviedb.org/documentation/api)
- **UI Components:** Custom responsive CSS & HTML5 flex carousels

---

## 🚀 Installation & Local Setup

If you would like to run this project locally on your machine:

### 1. Clone the repository
```bash
git clone https://github.com/your-username/movie-recommender-system.git
cd movie-recommender-system
```

### 2. Create and activate a virtual environment
```bash
# Windows
python -m venv venv
.\venv\Scripts\activate

# macOS / Linux
python3 -m venv venv
source venv/bin/activate
```

### 3. Install required packages
```bash
pip install -r requirements.txt
```

### 4. Ensure model files are present
Make sure `movies.pkl` and `vectors.pkl` are located in the project root directory. (If cloning via Git LFS, ensure large files are pulled with `git lfs pull`).

### 5. Launch the Streamlit application
```bash
streamlit run app.py
```

Open your browser at `http://localhost:8501` to use the recommender system.

---

## 📂 Project Structure

```
Movie Recommender System/
│
├── app.py                            # Streamlit web application & UI logic
├── Movie Recommender System.ipynb    # Data exploration, cleaning, and model training notebook
├── movies.pkl                        # Processed DataFrame containing 389,448 movies
├── vectors.pkl                       # TF-IDF sparse matrix (389,448 x 20,000)
├── requirements.txt                  # Python dependencies
├── Readme.md                         # Project documentation
└── the-movies-dataset/               # Raw metadata, keywords, and credits datasets
```

---

## 🌐 Test the Live Application

You can test the deployed application without installing anything locally:

🔗 **[https://movie-recommender-system-by-zakria.streamlit.app/](https://movie-recommender-system-by-zakria.streamlit.app/)**

---

## 👤 Author

Developed with ❤️ by **Zakria Mansoor**
- Live Demo: [Movie Recommender System](https://movie-recommender-system-by-zakria.streamlit.app/)
