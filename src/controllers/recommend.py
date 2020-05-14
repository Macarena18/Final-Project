import pandas as pd
from src.app import app
from src.config import *
from bson.json_util import dumps
from pandas.io.json import json_normalize
from scipy.spatial.distance import pdist, squareform

@app.route("/movies", methods=["GET"])
#Top Ranked movies
def TopMovies():
    movies_details=list(db.details.find({},{"_id":0,"title":1,"genres":1,"year":1,"imdbId":1,"tmdbId":1,"idmb_rank":1}))
    movies_info=pd.DataFrame(json_normalize(movies_details))
    top_movies=movies_info.sort_values(['idmb_rank'],ascending=False)[:10]
    return dumps(top_movies)

@app.route("/movies/genres/<genre>", methods=["GET"])
#Find top movies by genre
def moviesGenre(genre):
    movies_details=list(db.details.find({},{"_id":0}))
    movies_info=pd.DataFrame(json_normalize(movies_details))
    top_movies= movies_info.loc[(movies_info[genre]==1)].sort_values(['idmb_rank'],ascending=False)[:10]
    return dumps(top_movies)


@app.route("/movies/<name>", methods=["GET"])
"""
Find top 10 movies watched for users that saw the same movie:
-Create a dataframe with the list of all users who watched an specific movie
-Find all other movies watched by the users who watched this movie
-Find Top rank movies
"""
def similarmovies(name):
    ratings=list(db.ratings.find({},{"_id":0}))
    movies_ratings=pd.DataFrame(json_normalize(ratings))
    movies=list(db.movies.find({},{"_id":0}))
    movies_df=pd.DataFrame(json_normalize(movies))
    movies_ratings=pd.merge(movies_ratings,movies_df,on="movieId")
    movies_ratings=movies_ratings.drop(columns=["imdbId","tmdbId"])
    users_movie=movies_ratings.loc[movies_ratings["title"]==name]["userId"] # all users who saw the movie
    users_movie_df=pd.DataFrame(users_movie)
    user_other_movies=pd.merge(users_movie_df,movies_ratings,on="userId")
    top_movies=pd.DataFrame(user_other_movies.groupby("title")["userId"].count()).sort_values('userId',ascending=False)
    top_movies["rate_views"]= round(top_movies["userId"]*100/top_movies["userId"][0],1)
    return dumps(top_movies[:10])
