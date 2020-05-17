import pandas as pd
from src.app import app
from src.config import *
from bson.json_util import dumps
from pandas.io.json import json_normalize
from scipy.spatial.distance import pdist, squareform
from sklearn.neighbors import NearestNeighbors
from sklearn.metrics.pairwise import linear_kernel
from sklearn.feature_extraction.text import CountVectorizer
from src.helpers.errorHandler import APIError, errorHandler
from sklearn.metrics.pairwise import cosine_similarity as distance
import re
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import pairwise_distances


@app.route("/movies/top", methods=["GET"])#Top Ranked movies
def TopMovies():
    movies_details=list(db.details.find({},{"_id":0,"title":1,"genres":1,"year":1,"imdbId":1,"tmdbId":1,"idmb_rank":1}))
    movies_info=pd.DataFrame(json_normalize(movies_details))
    top_movies=movies_info.sort_values(['idmb_rank'],ascending=False)[:20]
    return dumps(top_movies)

@app.route("/genres/<genre>", methods=["GET"])#Find top movies by genre
def moviesGenre(genre):
    movies_details=list(db.details.find({},{"_id":0}))
    movies_info=pd.DataFrame(json_normalize(movies_details))
    top_movies= movies_info.loc[(movies_info[genre]==1)].sort_values(['idmb_rank'],ascending=False)[:20]
    return dumps({"movieid":top_movies["movieId"],"title":top_movies["title"],"genres":top_movies["genres"],"year":top_movies["year"],"IDMB rating":top_movies["idmb_rank"]})


# Recommend movies:

ratings=list(db.ratings.find({},{"_id":0,"userId":1,"movieId":1,"rating":1}))
ratings_df=pd.DataFrame(json_normalize(ratings))
ratings_df["movieId"]=ratings_df["movieId"].astype("int")
movies=list(db.movies.find({},{"_id":0,"movieId":1,"title":1,"genres":1,"year":1,"imdbId":1,"tmdbId":1}))
movies_df=pd.DataFrame(json_normalize(movies))
movies_ratings = pd.merge(ratings_df,movies_df, on = 'movieId')
movies_ratings.drop(columns=["imdbId","tmdbId"],inplace=True)
movie_rating_average = pd.DataFrame(ratings_df.groupby('movieId')['rating'].agg(['count','mean']))

@app.route("/movies/recommend/content/<movie_title>", methods=["GET"])
def get_similar_movies(movie_title):#Find top 20 movies to recommend based on similarity content:
    tfidf_movies_genres = TfidfVectorizer(token_pattern = '[a-zA-Z0-9\-]+')
    movies_df['genres'] = movies_df['genres'].replace(to_replace="(no genres listed)", value="")
    tfidf_movies_genres_matrix = tfidf_movies_genres.fit_transform(movies_df['genres'])
    cosine_sim_movies = linear_kernel(tfidf_movies_genres_matrix, tfidf_movies_genres_matrix)
    idx_movie = movies_df.loc[movies_df['title'].isin([movie_title])]# Get the index of the movie that matches the title
    idx_movie = idx_movie.index
    sim_scores_movies = list(enumerate(cosine_sim_movies[idx_movie][0]))# Get the pairwsie similarity scores of all movies with that movie
    sim_scores_movies = sorted(sim_scores_movies, key=lambda x: x[1], reverse=True)# Sort the movies based on the similarity scores
    sim_scores_movies = sim_scores_movies[1:21]## Get the scores of the 10 most similar movies
    movie_indices = [i[0] for i in sim_scores_movies] ## Get the movie indices
    top_movies=movies_df['title'].iloc[movie_indices]
    return dumps(top_movies) # Return the top 20 most similar movies

@app.route("/movies/recommend/users/<movie>", methods=["GET"])
def similarmovies(movie): #Find top 20 movies watched for users that saw the same movie
    movies_lst=(db.movies.distinct("title"))
    if movie not in movies_lst:
        print("ERROR")
        raise APIError ("I´m sorry this movie is not available. Try again with another movie.")
    else:
        users_movie=movies_ratings.loc[movies_ratings["title"]==movie]["userId"] # all users who saw the movie
        users_movie_df=pd.DataFrame(users_movie,columns=['userId'])#Create a dataframe with the list of all users who watched an specific movie
        user_other_movies=pd.merge(users_movie_df,movies_ratings,on="userId")#Find all other movies watched by the users who watched this movie
        top_movies=pd.DataFrame(user_other_movies.groupby("title")["userId"].count()).sort_values('userId',ascending=False) #Find Top rank movies
        top_movies["rate_views"]= round(top_movies["userId"]*100/top_movies["userId"][0],1)
        top_movies=top_movies[1:21]
        print(f" These are similar movies watched by users who saw {movie}:")
        return dumps(top_movies) # return user ids who saw the movies and the rate views of each movie


@app.route("/movies/recommend/<userid>", methods=["GET"])
def get_user_similarmovie(userid):#Find top movies to be recommended to user based on movies user has watched
    recommended_movie_list = []
    movie_list = []
    df_rating_filtered = ratings_df[ratings_df["userId"]== userid]
    for key, row in df_rating_filtered.iterrows():
        movie_list.append((movies_df["title"][row["movieId"]==movies_df["movieId"]]).values) 
    for index, movie in enumerate(movie_list):
        for key, movie_recommended in get_similar_movies(movie[0]).iteritems():
            recommended_movie_list.append(movie_recommended)
    for movie_title in recommended_movie_list:# removing already watched movie from recommended list    
        if movie_title in movie_list:
            recommended_movie_list.remove(movie_title)
    return set(recommended_movie_list)

@app.route("/movies/recommend/ratings/<movieid>")
def similaratings(movieid): # similar movies by ranking
        movies_filtered=movie_rating_average.loc[movie_rating_average['count']>=10]
        filtered_ratings = pd.merge(movies_filtered, ratings_df, on="movieId")
        movies_table=filtered_ratings.pivot(index = 'movieId', columns = 'userId', values = 'rating').fillna(0)
        model_knn = NearestNeighbors(metric='cosine',algorithm='brute').fit(movies_table)
        index_movie_ratings=movies_table.loc[int(movieid),:].values.reshape(1,-1)##get the list of user ratings for a specific userId
        distances,indices = model_knn.kneighbors(index_movie_ratings,n_neighbors = 11)
        for i in range(0,len(distances.flatten())):
            get_movie = movies_df.loc[movies_df['movieId']==int(movieid)]['title']
            if i==0:
                print('Recommendations for {0}:\n'.format(get_movie))
            else :
                #get the indiciees for the closest movies
                indices_flat = indices.flatten()[i]
                #get the title of the movie
                get_movie = movies_df.loc[movies_df['movieId']==movies_table.iloc[indices_flat,:].name]['title']
                #print the movie
                return('{0}: {1}, with distance of {2}:'.format(i,get_movie,distances.flatten()[i]))    

#Recommending movie which user hasn't watched as per Item Similarity/User Similarity

"""
ratings_matrix_items = movies_ratings.pivot_table(index=['movieId'],columns=['userId'],values='rating').reset_index(drop=True)
ratings_matrix_items.fillna( 0, inplace = True )
movie_similarity = 1 - pairwise_distances( ratings_matrix_items.to_numpy(), metric="cosine" )
np.fill_diagonal( movie_similarity, 0 ) #Filling diagonals with 0s for future use when sorting is done
ratings_matrix_items = pd.DataFrame( movie_similarity )

def item_similarity(movieName): 
    try:
        user_inp=movieName
        inp=movies_df[movies_df['title']==user_inp].index.tolist()
        inp=inp[0]
        movies_df['similarity'] = ratings_matrix_items.iloc[inp]
        movies_df.columns = ['movie_id', 'title', 'release_date','similarity']
    except:
        print("Sorry, the movie is not in the database!")

def recommendedMoviesAsperItemSimilarity(user_id):#Recommending movie which user hasn't watched as per Item Similarity
    user_movie= movies_ratings[(movies_ratings.userId==user_id) & movies_ratings.rating.isin([5,4.5])][['title']]
    user_movie=user_movie.iloc[0,0]
    item_similarity(user_movie)
    sorted_movies_as_per_userChoice=movies_df.sort_values( ["similarity"], ascending = False )
    sorted_movies_as_per_userChoice=sorted_movies_as_per_userChoice[sorted_movies_as_per_userChoice['similarity'] >=0.45]['movie_id']
    recommended_movies=list()
    df_recommended_item=pd.DataFrame()
    user2Movies= ratings_df[ratings_df['userId']== user_id]['movieId']
    for movieId in sorted_movies_as_per_userChoice:
            if movieId not in user2Movies:
                df_new= ratings_df[(ratings_df.movieId==movieId)]
                df_recommended_item=pd.concat([df_recommended_item,df_new])
            top_movies=df_recommended_item.sort_values(["rating"], ascending = False )[1:21] 
    return top_movies['movieId']

def movieIdToTitle(listMovieIDs):
    movie_titles= list()
    for id in listMovieIDs:
        movie_titles.append(movies_df[movies_df['movie_id']==id]['title'])
    return movie_titles

#user_id=50
#movieIdToTitle(recommendedMoviesAsperItemSimilarity(user_id)))


def getRecommendedMoviesAsperUserSimilarity(userId):#Recommending movies which user hasn't watched as per User Similarity
    user2Movies= ratings_df[ratings_df['userId']== userId]['movieId']
    sim_user=df_similar_user.iloc[0,0]
    df_recommended=pd.DataFrame(columns=['movieId','title','genres','userId','rating','timestamp'])
    for movieId in ratings_df[ratings_df['userId']== sim_user]['movieId']:
        if movieId not in user2Movies:
            df_new= movies_ratings[(movies_ratings.userId==sim_user) & (movies_ratings.movieId==movieId)]
            df_recommended=pd.concat([df_recommended,df_new])
        best10=df_recommended.sort_values(['rating'], ascending = False )[1:21]  
    return best10['movieId']

#user_id=50
#movieIdToTitle(getRecommendedMoviesAsperUserSimilarity(user_id))
"""