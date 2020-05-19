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


#Collaborative Filtering:

##Recommending movie which user hasn't watched as per Movie Similarity/User Similarity

ratings=list(db.ratingid.find({},{"_id":0,"userId":1,"movieId":1,"rating":1}))
ratings_df=pd.DataFrame(json_normalize(ratings))
movies=list(db.movieid.find({},{"_id":0,"movieId":1,"title":1,"genres":1,"year":1,"imdbId":1,"tmdbId":1}))
movies_df=pd.DataFrame(json_normalize(movies))
movies_ratings=pd.merge(movies_df, ratings_df)
ratings_matrix_items = movies_ratings.pivot_table(index=['movieId'],columns=['userId'],values='rating').reset_index(drop=True)
ratings_matrix_items.fillna( 0, inplace = True )
movie_similarity = 1 - pairwise_distances(ratings_matrix_items.to_numpy(), metric="cosine" )
np.fill_diagonal( movie_similarity, 0 ) #Filling diagonals with 0s for future use when sorting is done
ratings_matrix_items = pd.DataFrame( movie_similarity )

#Movie Similarity

def item_similarity(movieName): #Find similar movies
    try:
        user_inp=movieName
        inp=movies_df[movies_df['title']==user_inp].index.tolist()
        inp=inp[0]

        movies_df['similarity'] = ratings_matrix_items.iloc[inp]
        movies_df.columns = ['movie_id', 'title', 'release_date','similarity']
    except:
        print("Sorry, the movie is not in the database!")

def recommendedMoviesAsperItemSimilarity(user_id):#Recommending movie which user hasn't watched as per Item Similarity
    user_movie= movies_ratings[(movies_ratings.userId==int(user_id)) & movies_ratings.rating.isin([5,4])][['title']]
    user_movie=user_movie.iloc[0,0]
    item_similarity(user_movie)
    sorted_movies_as_per_userChoice=movies_df.sort_values( ["similarity"], ascending = False )
    sorted_movies_as_per_userChoice=sorted_movies_as_per_userChoice[sorted_movies_as_per_userChoice['similarity'] >=0.45]['movie_id']
    recommended_movies=list()
    df_recommended_item=pd.DataFrame()
    user2Movies= ratings_df[ratings_df['userId']== int(user_id)]['movieId']
    for movieId in sorted_movies_as_per_userChoice:
            if movieId not in user2Movies:
                df_new= ratings_df[(ratings_df.movieId==movieId)]
                df_recommended_item=pd.concat([df_recommended_item,df_new])
            top_movies=df_recommended_item.sort_values(["rating"], ascending = False)[1:21] 
    return top_movies['movieId']

def movieIdToTitle(listMovieIDs):
    movie_titles= list()
    for id in listMovieIDs:
        movie_titles.append(movies_df[movies_df['movie_id']==id]['title'])
    return movie_titles

@app.route("/movies/recommend/similarity/<user_id>", methods=["GET"])
def getitemsimilarity(user_id):
    result=movieIdToTitle(recommendedMoviesAsperItemSimilarity(user_id))
    return dumps({"movies_similarity":result})

#User Similarity

ratings_matrix_users = movies_ratings.pivot_table(index=['userId'],columns=['movieId'],values='rating').reset_index(drop=True)
ratings_matrix_users.fillna( 0, inplace = True )
movie_similarity = 1 - pairwise_distances( ratings_matrix_users.to_numpy(), metric="cosine" )
np.fill_diagonal( movie_similarity, 0 ) 
ratings_matrix_users = pd.DataFrame( movie_similarity )
ratings_matrix_users.idxmax(axis=1)
ratings_matrix_users.idxmax(axis=1).sample( 10, random_state = 10 )
similar_user_series= ratings_matrix_users.idxmax(axis=1)
df_similar_user= similar_user_series.to_frame()

def getRecommendedMoviesAsperUserSimilarity(userId):#Recommending movies which user hasn't watched as per User Similarity
    user2Movies= ratings_df[ratings_df['userId']== int(userId)]['movieId']
    sim_user=df_similar_user.iloc[0,0]
    df_recommended=pd.DataFrame(columns=['movieId','title','genres','userId','rating','timestamp'])
    for movieId in ratings_df[ratings_df['userId']== sim_user]['movieId']:
        if movieId not in user2Movies:
            df_new= movies_ratings[(movies_ratings.userId==sim_user) & (movies_ratings.movieId==movieId)]
            df_recommended=pd.concat([df_recommended,df_new])
        top_movies=df_recommended.sort_values(['rating'], ascending = False)[1:21]  
    return top_movies['movieId']

@app.route("/movies/recommend/usersimilarity/<user_id>", methods=["GET"])
def getusersimilarity(user_id):
    result=movieIdToTitle(getRecommendedMoviesAsperUserSimilarity(user_id))
    return dumps({"users_similarity":result})

