import pandas as pd
import numpy as np
from src.app import app
from src.config import *
from bson.json_util import dumps
from pandas.io.json import json_normalize
from sklearn.neighbors import NearestNeighbors
from sklearn.metrics.pairwise import linear_kernel
from sklearn.feature_extraction.text import CountVectorizer
from src.helpers.errorHandler import APIError, errorHandler
from sklearn.metrics.pairwise import cosine_similarity as distance
import re
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import pairwise_distances
#from sklearn.externals import joblib
import joblib


joblib_file="joblib_SVD_Model.pkl"
model_svd=joblib.load(joblib_file)

ratings=list(db.ratingid.find({},{"_id":0,"userId":1,"movieId":1,"rating":1}))
ratings_df=pd.DataFrame(json_normalize(ratings))
movies=list(db.movieid.find({},{"_id":0,"movieId":1,"title":1,"genres":1}))
movies_df=pd.DataFrame(json_normalize(movies))

def get_similar_movies(movie_title):#Find top 20 movies to recommend based on similarity content
    tfidf_movies_genres = TfidfVectorizer(token_pattern = '[a-zA-Z0-9\-]+')
    movies_df['genres'] = movies_df['genres'].replace(to_replace="(no genres listed)", value="")
    tfidf_movies_genres_matrix = tfidf_movies_genres.fit_transform(movies_df['genres'])
    cosine_sim_movies = linear_kernel(tfidf_movies_genres_matrix, tfidf_movies_genres_matrix)
    idx_movie = movies_df.loc[movies_df['title'].isin([movie_title])]# Get the index of the movie that matches the title
    idx_movie = idx_movie.index
    sim_scores_movies = list(enumerate(cosine_sim_movies[idx_movie][0]))# Get the pairwsie similarity scores of all movies with that movie
    sim_scores_movies = sorted(sim_scores_movies, key=lambda x: x[1], reverse=True)# Sort the movies based on the similarity scores
    sim_scores_movies = sim_scores_movies[1:21]# Get the scores of the 20 most similar movies
    movie_indices = [i[0] for i in sim_scores_movies] # Get the movie indices
    top_movies=movies_df['title'].iloc[movie_indices]
    return top_movies


@app.route("/ratings/prediction/<userId>", methods=["GET"])
def hybrid_content_svd_model(userId): #hydrid the functionality of content based and svd based model to recommend user top 10 movies. 
    recommended_movie_list = []
    movie_list = []
    df_rating_filtered = ratings_df[ratings_df["userId"]== int(userId)]
    for key, row in df_rating_filtered.iterrows():
        movie_list.append((movies_df["title"][row["movieId"]==movies_df["movieId"]]).values) 
    for index, movie in enumerate(movie_list):
        for key, movie_recommended in get_similar_movies(movie[0]).iteritems():
            recommended_movie_list.append(movie_recommended)
    for movie_title in recommended_movie_list:
        if movie_title in movie_list:
            recommended_movie_list.remove(movie_title)
    recommended_movies_by_content=set(recommended_movie_list)
    recommended_movies_by_content_model = movies_df[movies_df.apply(lambda movie: movie["title"] in recommended_movies_by_content, axis=1)]
    for key, columns in recommended_movies_by_content_model.iterrows():
        predict = model_svd.predict(userId, columns["movieId"])
        recommended_movies_by_content_model.loc[key, "svd_rating"] = predict.est
        recommended_movies_by_content_model=recommended_movies_by_content_model[["movieId","title","svd_rating"]]
        result=recommended_movies_by_content_model.sort_values("svd_rating", ascending=False).iloc[0:21]
    return dumps({"ratings_prediction":result.T})
