from flask import Flask, render_template, url_for, jsonify, request, redirect, flash
app = Flask(__name__)
import RestaurantAPI
from sqlalchemy import create_engine, asc
from sqlalchemy.orm import sessionmaker
from database_setup import Restaurant, Base, MenuItem, User

from flask import session as login_session
import random, string

# New
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import json
from flask import make_response
import requests

CLIENT_ID = json.loads(
    open('/var/www/Catalog/Catalog/client_secrets.json', 'r').read())['web']['client_id']
APPLICATION_NAME = "TJ's Restaurant Menu"

engine = create_engine('postgresql+psycopg2://catalog:catalog@/catalog')
Base.metadata.bind = engine
 
DBSession = sessionmaker(bind=engine)
session = DBSession()


# Below is my state token to prevent requests
# Store it in the session for later validation
@app.route('/login')
@app.route('/login/')
def showLogin():
    state = ''.join(random.choice(string.ascii_uppercase + string.digits) for x in xrange(32))
    print 'State is ', state
    login_session['state'] = state
    # return the current session state is % login_session['state']
    return render_template('login.html', STATE=state)


    
@app.route('/gconnect', methods=['POST'])
def gconnect():
    print '---------------------------------'
    print login_session['state']
    print request
    if request.args.get('state') != login_session['state']:
        print 'Path 1'
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
        
    # obtain data
    code = request.data
    credentials = None
    print 'Path 2'
    print code
    
    try:
        #upgrade the authrization code into a credentials object
        oauth_flow = flow_from_clientsecrets('/var/www/Catalog/Catalog/client_secrets.json', scope='')
        # print oauth_flow
        
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        print FlowExchangeError
        response = make_response(json.dumps('Failed to upgrade the authorization code.'), 401)
        response.headers['Content Type'] = 'application/json'
        
    #Check that the access token is valid.
    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s' % access_token)
    h = httplib2.Http()
    temp = h.request(url, 'GET')
    result = json.loads(h.request(url, 'GET')[1])
    
    # If there was an error in the access token info, don't do anything.
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-type'] = 'application/json'
        
    # Verify that the access token is used for the intended user.
    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        response = make_response(
            json.dumps("Token's user ID doesn't match given user ID."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    
    # Verify that the access token is valid for this app.
    if result['issued_to'] != CLIENT_ID:
        response = make_response(
            json.dumps("Token's client does not match app's."), 401)
        print "Token's client ID does not match app's"
        response.headers['Content-Type'] = 'application/json'
        return response
        
    stored_credentials = login_session.get('credentials')
    stored_gplus_id = login_session.get('gplus_id')

    if stored_credentials is not None and gplus_id == stored_gplus_id:
        response = make_response(json.dumps('Current user is already connected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response
        
    # Store the access token in the session for later use.
    login_session['provider'] = 'google'
    login_session['credentials'] = credentials.to_json()
    login_session['gplus_id'] = gplus_id
    response = make_response(json.dumps('Successfully connected user'), 200)
    
    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)
    
    data = answer.json()
    
    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']
    
    user_id = getUserId(login_session['email'])
    if not user_id:
        user_id = createUser(login_session)
        login_session['user_id'] = user_id
        print '333333333333333333333333333'
    else:
        login_session['user_id'] = user_id
    # see here if the user exists in DB, if not create one
    
    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']
    output += '!</h1>'
    output += '"<img src="'
    output += login_session['picture']
    output += ' " style = "width: 300px; height: 300px;border-radius: 150px;-webkit-border-radius: 150px; -moz-border-radius: 150px;:>"'
    flash("you are now logged in as %s" % login_session['username'])
    print "done!"
    return output

    
@app.route('/gdisconnect')
def gdisconnect():
        # Only disconnect a connected user.
    strCredentials = login_session.get('credentials')
    if strCredentials is None:
        response = make_response(
            json.dumps('Current user not connected.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    
    jsonCredentials = json.loads(strCredentials)
    tokenResponse = jsonCredentials['token_response']
    access_token = tokenResponse['access_token']
    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % access_token
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]

    if result['status'] != '200':
        response = make_response(
            json.dumps('Failed to revoke token for given user.', 400))
        response.headers['Content-Type'] = 'application/json'
        return response    
    
    # Reset the user's sesson.
        #del login_session['credentials']
       # del login_session['gplus_id']
      #  del login_session['username']
     #   del login_session['email']
    #    del login_session['picture']

       # response = make_response(json.dumps('Successfully disconnected.'), 200)
      #  response.headers['Content-Type'] = 'application/json'
     #   return response
    #else:
        # For whatever reason, the given token was invalid.
        
    
    
@app.route('/fbconnect', methods=['POST'])
def fbconnect():

    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    access_token = request.data
    #Exchange client token for long-lived server-side token with GET /oauth/
    # access_token?grant_type=fb_exchange_token&client_id={app-id}&
    # client_secret={app-secret}&fb_exchange_token={short-lived-token}
    app_id = json.loads(open('fb_client_secrets.json', 'r').read())['web']['app_id']
    app_secret = json.loads(open('fb_client_secrets.json', 'r').read())['web']['app_secret']
    url = 'https://graph.facebook.com/oauth/access_token?grant_type=fb_exchange_token&client_id=%s&client_secret=%s&fb_exchange_token=%s' % (app_id, app_secret, access_token)
    h = httplib2.Http()
    result = h.request(url, 'GET')[1]
    
    #Use token to get user info from API
    userinfo_url = "https://graph.facebook.com/v2.2/me"
    # strip expire tag from access token
    token = result.split("&")[0]
    
    url = 'https://graph.facebook.com/v2.2/me?%s&fields=name,id,email' % token
    h = httplib2.Http()
    result = h.request(url, 'GET')[1]
    data = json.loads(result)
    
    login_session['provider'] = 'facebook'
    login_session['username'] = data["name"]
    login_session['email'] = data["email"]
    login_session['facebook_id'] = data["id"]
    
    stored_token = token.split("=")[1]
    login_session['access_token'] = stored_token
    
    
    # Get User Picture
    url = 'https://graph.facebook.com/v2.2/me/picture?%s&redirect=0&height=200&width=200' % token
    h = httplib2.Http()
    result = h.request(url, 'GET')[1]
    data = json.loads(result)
    
    login_session['picture'] = data["data"]["url"]
    
    user_id = getUserId(login_session['email'])
    if not user_id:
        user_id = createUser(login_session)
        login_session['user_id'] = user_id
    else:
        login_session['user_id'] = user_id
    
    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']
    output += '!</h1>'
    output += '"<img src="'
    output += login_session['picture']
    output += ' " style = "width: 300px; height: 300px;border-radius: 150px;-webkit-border-radius: 150px; -moz-border-radius: 150px;:>"'
    flash("you are now logged in as %s" % login_session['username'])
    print "done!"
    return output
    
    
@app.route('/fbdisconnect', methods=['GET', 'POST'])
def fbdisconnect():
    facebook_id = login_session['facebook_id']
    access_token = login_session['access_token']
    url = 'https://graph.facebook.com/%s/permissions?access_token=%s' % (facebook_id, access_token)
    h = httplib2.Http()
    result = h.request(url, 'DELETE')[1]
    return "You have been logged out"    
    
@app.route('/disconnect')
def disconnect():
    if 'provider' in login_session:
        if login_session['provider'] == 'google':
            gdisconnect()
            del login_session['gplus_id']
            del login_session['credentials']
        if login_session['provider'] == 'facebook':
            fbdisconnect()
            del login_session['facebook_id']
        del login_session['username']
        del login_session['email']
        del login_session['picture']
        del login_session['user_id']
        del login_session['provider']
        flash("You have successfully ben logged out.")
        return redirect(url_for('showRestaurants'))
    else:
        flash("You were not successfully logged in to begin with!")
        return redirect(url_for('showRestaurants'))
    
    facebook_id = login_session['facebook_id']
    url = 'https://graph.facebook.com/%s/permissions' % facebook_id
    h = httplib2.Http()
    result = h.request(url, 'DELETE')[1]
    del login_session['username']
    del login_session['email']
    del login_session['picture']
    del login_session['user_id']
    del login_session['facebook_id']


    
    #    OAUTH END    #

#JSON APIs to view Restaurant Information
@app.route('/restaurants/<int:restaurant_id>/menu/JSON')
def restaurantMenuJSON(restaurant_id):
    restaurant = session.query(Restaurant).filter_by(id = restaurant_id).one()
    items = session.query(MenuItem).filter_by(restaurant_id = restaurant_id).all()
    return jsonify(MenuItems=[i.serialize for i in items])


@app.route('/restaurants/<int:restaurant_id>/menu/<int:menu_id>/JSON')
def menuItemJSON(restaurant_id, menu_id):
    Menu_Item = session.query(MenuItem).filter_by(id = menu_id).one()
    return jsonify(Menu_Item = Menu_Item.serialize)

@app.route('/restaurants/JSON')
def restaurantsJSON():
    restaurants = session.query(Restaurant).all()
    return jsonify(restaurants= [r.serialize for r in restaurants])


#Show all restaurants
@app.route('/')
@app.route('/restaurants/')
def showRestaurants():
  restaurants = session.query(Restaurant).order_by(asc(Restaurant.name))
  if ('user_id' not in login_session):
    return render_template('publicrestaurants.html', restaurants = restaurants)
  return render_template('restaurants.html', restaurants = restaurants)

#Create a new restaurant
@app.route('/restaurants/new/', methods=['GET','POST'])
def newRestaurant():
  if 'username' not in login_session:
    return redirect ('login')
  if request.method == 'POST':
      newRestaurant = Restaurant(name = request.form['name'], user_id=login_session['user_id'])
      session.add(newRestaurant)
      flash('New Restaurant %s Successfully Created' % newRestaurant.name)
      session.commit()
      return redirect(url_for('showRestaurants'))
  else:
      return render_template('newRestaurant.html')

#Edit a restaurant
@app.route('/restaurants/<int:restaurant_id>/edit/', methods = ['GET', 'POST'])
def editRestaurant(restaurant_id):
  if 'username' not in login_session:
    return redirect('login')  
  editedRestaurant = session.query(Restaurant).filter_by(id = restaurant_id).one()
  creator = getUserInfo(editRestaurant.user_id)
  if login_session['user_id'] != creator:
    return redirect('login')
  if request.method == 'POST':
      if request.form['name']:
        editedRestaurant.name = request.form['name']
        flash('Restaurant Successfully Edited %s' % editedRestaurant.name)
        return redirect(url_for('showRestaurants'))
  else:
    return render_template('editRestaurant.html', restaurant = editedRestaurant)


#Delete a restaurant
@app.route('/restaurants/<int:restaurant_id>/delete/', methods = ['GET','POST'])
def deleteRestaurant(restaurant_id):
  if 'username' not in login_session:
    return redirect ('login')  
  restaurantToDelete = session.query(Restaurant).filter_by(id = restaurant_id).one()
  creator = getUserInfo(restaurantToDelete.user_id)
  if login_session['user_id'] != creator:
    return redirect('login')
  if request.method == 'POST':
    session.delete(restaurantToDelete)
    flash('%s Successfully Deleted' % restaurantToDelete.name)
    session.commit()
    return redirect(url_for('showRestaurants', restaurant_id = restaurant_id))
  else:
    return render_template('deleteRestaurant.html',restaurant = restaurantToDelete)

#Show a restaurant menu
@app.route('/restaurants/<int:restaurant_id>/')
@app.route('/restaurants/<int:restaurant_id>/menu/')
def showMenu(restaurant_id):
    restaurant = session.query(Restaurant).filter_by(id = restaurant_id).first()
    creator = getUserInfo(restaurant.user_id)
    items = session.query(MenuItem).filter_by(restaurant_id = restaurant_id).all()
    if ('user_id' not in login_session or login_session['user_id'] != creator.id):
        return render_template('publicmenu.html', items = items, restaurant = restaurant, creator = creator)
    return render_template('menu.html', items = items, restaurant = restaurant, creator = creator)
     

# PULLED DIRECTLY FROM DIRECTOR NOTES END #    

def home():
    return redirect(url_for('HelloWorld', restaurant_id = 10))

@app.route('/')
def defaultRestaurantMenu():
    restaurant = session.query(Restaurant).first()
    items = session.query(MenuItem).filter_by(restaurant_id = restaurant.id)
    return render_template('menu.html', restaurant=restaurant, items = items)

    
# Task 1: Create route for newMenuItem function here

@app.route('/restaurants/<int:restaurant_id>/new/', methods=['GET', 'POST'] )
def newMenuItem(restaurant_id):
    IDNumber = restaurant_id
    restaurant = session.query(Restaurant).filter_by(id=restaurant_id).first()
    creator = getUserInfo(restaurant.user_id)
    if ('user_id' not in login_session or login_session['user_id'] != creator.id):
        return redirect ('login')
    
    if request.method == 'POST':
        try:
            newItem = MenuItem(name = request.form['name'],restaurant_id=restaurant_id, description = request.form['description'], course = request.form['course'], price = request.form['price'], user_id = restaurant.user_id)
            session.add(newItem)
            session.commit()
            result = newItem
            session.close()
            flash('New Menu %s Item Successfully Created' % (result.name))
            return redirect(url_for('restaurantMenu', restaurant_id=restaurant_id))
        except:
            session.rollback()
            session.close()
            return render_template('newMenuItem.html', restaurant_id = restaurant_id)
    else:
        return render_template('newmenuitem.html', restaurant_id = restaurant_id)

# Task 2: Create route for editMenuItem function below

@app.route('/restaurants/<int:restaurant_id>/<int:menu_id>/edit/', methods=['GET', 'POST'])
def editMenuItem(restaurant_id, menu_id):
    restaurantFromDb = session.query(Restaurant).filter_by(id=restaurant_id).first()
    creator = getUserInfo(restaurantFromDb.user_id)
    if ('username' not in login_session or login_session['user_id'] != creator.id):
        return redirect ('login')    
    menuItemFromDb = session.query(MenuItem).filter_by(restaurant_id=restaurant_id, id= menu_id).first()
    if request.method == 'POST':
        try:
            if (request.form['name']):
                menuItemFromDb.name = request.form['name']
            if (request.form['description']):
                menuItemFromDb.description = request.form['description']
            if (request.form['price']):
                menuItemFromDb.price = request.form['price']
            if (request.form['course']):
                menuItemFromDb.course = request.form['course']
            session.add(menuItemFromDb)
            session.commit()
            result = menuItemFromDb
            session.close()
            return redirect(url_for('editMenuItem', restaurant_id=restaurant_id, menu_id = menu_id))
            
        except:
            session.rollback()
            session.close()
            return redirect(url_for('editMenuItem', restaurant_id=restaurant_id, menu_id = menu_id))
    else:
        return render_template('editmenuitem.html', restaurant = restaurantFromDb, menuItem = menuItemFromDb)
    return "page to edit a menu item. Task 2 complete!"

# Task 3: Create a route for deleteMenuItem function here

@app.route('/restaurants/<int:restaurant_id>/<int:menu_id>/delete/', methods=['GET', 'POST'])
def deleteMenuItem(restaurant_id, menu_id):
    restaurantFromDb = session.query(Restaurant).filter_by(id=restaurant_id).first()
    creator = getUserInfo(restaurantFromDb.user_id)
    if ('username' not in login_session or login_session['user_id'] != creator.id):
        return redirect ('login')
    menuItemFromDb = session.query(MenuItem).filter_by(restaurant_id=restaurant_id, id= menu_id).first()
    if request.method == 'POST':
        try:
            session.delete(menuItemFromDb)
            session.commit()
            session.close()
            return redirect(url_for('deleteMenuItemConfirmation', restaurant_id=restaurant_id))
        except:
            session.rollback()
            session.close()
            return redirect(url_for('deleteMenuItem', restaurant_id=restaurant_id, menu_id = menu_id))
    else:
        return render_template('deletemenuitem.html', restaurant = restaurantFromDb, menuItem = menuItemFromDb)
    return "page to delete a menu item. Task 3 complete!"

@app.route('/restaurants/<int:restaurant_id>/deleteConfirmation/')
def deleteMenuItemConfirmation(restaurant_id):
    restaurantFromDb = session.query(Restaurant).filter_by(id=restaurant_id).first()
    return render_template('deleteMenuItemConfirmation.html', restaurant = restaurantFromDb)
    
def getUserInfo(user_id):
    try:
        user = session.query(User).filter_by(id=user_id).first()
        return user
    except: 
        return None
    
def getUserId(email):
    try:
        user = session.query(User).filter_by(email=email).first()
        return user.id
    except:
        return None
    
def createUser(login_session):
    newUser = User(name = login_session['username'], email = login_session['email'], picture = login_session['picture'])
    session.add(newUser)
    session.commit()
    user = session.query(User).filter_by(email=login_session['email']).one()
    return user.id
    
    
    
    
if __name__ == '__main__':
    app.secret_key = 'tLTLQoXH2xwd9jTymHywEnHA'
    app.debug = True
    app.run(host='0.0.0.0', port=5000)
   # app.run(host='127.0.0.1', port=80)
   # app.run()
    
