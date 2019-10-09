import os
from flask import Flask, render_template, request, redirect, url_for
import requests
import json
from pymongo import MongoClient
from bson.objectid import ObjectId

#Client
client = MongoClient()
#Database associated with Client
db = client.MovieDB
#Collections associated with Database
cart_list = db.cart_list
wish_list = db.wish_list
current_index = db.current_index
current_index.drop()
#wish_list.drop()
#cart_list.drop()

app = Flask(__name__)
TMDB_API_KEY = 'c19ff401506998a56c82406befe55455'

#Show initial search page with attributions and big search bar
@app.route('/', methods=['GET', 'POST'])
def index():
    """Show Search Bar and Attributions"""

    #Page has just refreshed
    query = request.form.get('search')
    

    query_string = {
        'api_key': TMDB_API_KEY,
        'language': 'en-US',
        'query': query,
        'include_adult': 'False'
    }

    #if there is a query 
    if query is not None:
        r = requests.get("https://api.themoviedb.org/3/search/multi?", query_string)
        movies = json.loads(r.content)["results"]

        current_index.drop()

        #parse JSON
        #Thanks to Mr. Ben Lafferty and Zurich Okoren for helping me understand lambda and filter better
        filtered_list = list(filter(lambda x: (x.get("title") or x.get("original_title" or x.get("original_name"))) and x.get("poster_path"), movies))

        #Add current index of movies to a collection
        current_index.insert_many(filtered_list)

    #Display all movies in current_index
    return render_template('index.html', movies = list(current_index.find()))

#Route a single movie with description and images
@app.route('/movie/<movie_id>', methods=['POST'])
def movie_details(movie_id):
    """Show a single movies details"""
    #Find movie in index database
    movie = current_index.find_one({'_id': ObjectId(movie_id)})
    return render_template('movie_details.html', movie=movie)

#Add movie to either wishlist or cart with a movie id
@app.route('/<location>/add/<movie_id>')
def add_to(location, movie_id):
    #Find movie from index
    movie = current_index.find_one({'_id': ObjectId(movie_id)})

    #add item to cart
    if location == 'cart':
        cart_list.insert_one(movie)
    #add item to wishlist
    elif location == 'wishlist':
        wish_list.insert_one(movie)

    #redirect to cart or wishlist after adding a movie with collection list
    return redirect(url_for(f'{location}_index'))

#Show shopping cart                                     
@app.route('/cart')
def cart_index():
    """Show Cart with all cart contents""" 
    return render_template('cart.html', cart=list(cart_list.find()))

@app.route('/cart/delete/<movie_id>')
def cart_delete(movie_id):
    """Delete specified item from cart"""
    cart_list.delete_one({'_id': ObjectId(movie_id)})

    return redirect(url_for('cart_index'))



#@app.route('/wishlist')
#def wishlist_index(movies):
#    """Show Wishlist with all contents""" 
 #   return render_template('wishlist.html', movies=movies)