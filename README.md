# Movies Recommender System - Project

**Steps:**

* Data Analysis
* Recommender System:
    * **Content based filtering** <Sklearn>-> recommend movies based on the similarity content of the movies
    * **Collaborative filtering**:
         * **Memory based collaborative filtering:**<Sklearn>
                * *User-Item Filtering* 
                * *Item-Item Filtering*  
         * **Model based collaborative filtering:** <Surprise Library> 
                * *Single Value Decomposition(SVD)* <Matrix Factorization>
                * *SVD++*
         * **Evaluating Collaborative Filtering using SVD** 
    * **Hybrid Model** <Content Based Filtering + SVD:> - Rating Prediction

**Datasets:**
The data set used for this project is the 1M ratings data set from MovieLens <https://grouplens.org/datasets/movielens/>
    

# How to use the API?

Link ->

## API EndPoints: `Apitest.ipynb`

doc ´get.py´:
 - *"/"* --> **API Welcome Message**
 - *"/movies"* --> **Get all movies**
 -* "/movies/<movie>"* --> **Get details for an specific movie**
 - *"/users"* --> **Get all users**
 - *"/ratings/<userid>"* --> **Get all ratings given for an specific user**
 - *"/ratings/movies/<movieid>"* --> **Get all ratings for an specific movie**
 - *"/year/<year>"* --> **Get all movies for an specific year**
 - *"/genres"* --> **Get all genres**

 doc ´recommend.py´:
- *"/movies/top"* --> **Recommend top ranked movies**
- *"/genres/<genre>"* --> **Recommend top ranked movies for an specific genre**
- *"/movies/recommend/content/<movie_title>"* --> **Recommend top 20 movies based on similarity content**
- *"/movies/recommend/users/<movie>"* --> **Recommend top 20 movies watched for users that saw the same movie**

doc ´collaborativefiltering.py´:
- *"/movies/recommend/similarity/<user_id>"* --> **Recommend top 20 movies which user hasn't watched as per Item Similarity**
- *"/movies/recommend/usersimilarity/<user_id>"* --> **Recommend top 20 movies which user hasn't watched as per User Similarity**

doc ´predictions.py´:
- *"/ratings/prediction/<userId>"* --> **Recommend top 20 movies and predict the rating that the user would give to a movie that he has not yet rated**


**Built With:**
Sklearn - Machine learning library
seaborn, matplotlib.pyplot, - Visualization libraries
numpy, scipy - Number Python Library
pandas - Data Handling Library
Singular Value Decomposition(SVD) model and SVD++  - Used for making regression models
Surprise Libray - Used for making recommendation system models