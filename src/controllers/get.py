import pandas as pd
from src.app import app
from src.config import *
from bson.json_util import dumps
from src.helpers.errorHandler import APIError, errorHandler
from pandas.io.json import json_normalize

@app.route("/", methods=["GET"]) #return welcome message
def welcome():
    return dumps("Welcome to the API - Movie Recommendation") 

@app.route("/movies", methods=["GET"]) # return all  movies in the dataset
def movies():
    movies=(db.movies.distinct("title"))
    return dumps({"movies_list":movies})

@app.route("/users", methods=["GET"]) # return all users in the dataset
def users():
    users=(db.ratings.distinct("userId"))
    return dumps({"users_list":users})

@app.route("/movies/<movie>", methods=["GET"]) # return details for an  specific movie
def selectmovie(movie):
    movies_lst=(db.details.distinct("title"))
    movies=db.details.find({"title":movie},{"_id":0,"title":1,"genres":1,"year":1,"imdbId":1,"tmdbId":1,"idmb_rank":1})
    movies_df=pd.DataFrame(movies)
    imdb=movies_df["imdbId"][0]
    tmdb=movies_df["tmdbId"][0]
    title=movies_df["title"][0]
    year=movies_df["year"][0]
    score=movies_df["idmb_rank"]
    if movie not in movies_lst:
        print("ERROR")
        raise APIError ("I´m sorry this movie is not available. Try again with another movie.")
    return dumps({"title":title,"year":year,"score":score,"Link IMDB":f"http://www.imdb.com/title/{imdb}","Link TMDB":f"https://www.themoviedb.org/movie/{tmdb}"})

@app.route("/ratings/<userid>", methods=["GET"]) # return all ratings for specific user
def userratings(userid):
    userid_lst=(db.ratings.distinct("userId"))
    user_ratings=db.ratings.find({"userId":userid},{"_id":0,"movieId":1,"rating":1})
    if userid not in userid_lst:
        print("ERROR")
        raise APIError ("I´m sorry this user doesn´t exist. Try again with another user.")
    return dumps({"ratings":user_ratings})

@app.route("/ratings/movies/<movieid>", methods=["GET"]) # return all ratings for specific movie
def movieratings(movieid):
    movies_lst=(db.ratings.distinct("movieId"))
    movie_ratings=db.ratings.find({"movieId":movieid},{"_id":0,"userId":1,"rating":1})
    if movieid not in movies_lst:
        print("ERROR")
        raise APIError ("I´m sorry this movie is not available. Try again with another movie.")
    return dumps({"ratings":movie_ratings})

@app.route("/year/<year>", methods=["GET"]) # return all movies for  an specific year
def moviesyear(year):
    year_lst=(db.movies.distinct("year"))
    movies_year=db.details.find({"year":year},{"_id":0,"movieId":1,"title":1,"genres":1,"idmb_rank":1})
    if year not in year_lst:
        print("ERROR")
        raise APIError ("I´m sorry this year is not available. Try again with another year.")
    return dumps({"movies":movies_year})

@app.route("/genres", methods=["GET"]) # return all genres 
def genreslist():
    movies=list(db.movies.find({},{"_id":0,"movieId":1,"title":1,"genres":1,"year":1,"imdbId":1,"tmdbId":1}))
    movies_df=pd.DataFrame(json_normalize(movies))
    genre_list = ""
    for index,row in movies_df.iterrows():
            genre_list += row.genres + "|"  
    genre_list_split = genre_list.split('|')
    genre_list_split= list(set(genre_list_split)) # eliminate duplicates
    genre_list_split.remove('')
    return dumps({"genres":genre_list_split})