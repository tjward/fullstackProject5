# This is the API file for interacting with my Restaurant Menu database. 
# Below you will find all of the functions for performing CRUD operations.
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import psycopg2
 
from database_setup import Restaurant, Base, MenuItem
 
engine = create_engine('postgresql+psycopg2:///catalog')
# Bind the engine to the metadata of the Base class so that the
# declaratives can be accessed through a DBSession instance
Base.metadata.bind = engine
 
DBSession = sessionmaker(bind=engine)
# A DBSession() instance establishes all conversations with the database
# and represents a "staging zone" for all the objects loaded into the
# database session object. Any change made against the objects in the
# session won't be persisted into the database until you call
# session.commit(). If you're not happy about the changes, you can
# revert all of them back to the last commit by calling
# session.rollback()
# session = DBSession()

# Won't work because the exception wouldn't make it past the upper function
#def sanitizeQuery(inputFunction):
# this function holds the try catch block to protect entries to my DB messing things up
#    session = DBSession()
    # print = 'Session opened'
#    try:
#        result = inputFunction()
#        session.commit()
#        return result
#    except:
#        session.rollback()
#        raise
#    finally:
#    session.close()
    #print 'Session closed'


def getRestaurantsfromDB():
# pulls all entries from the Restaurant database
    session = DBSession()
    restaurantList = session.query(Restaurant).all()
    session.close()
    return restaurantList
    #returns a list of restaurants

    
def createRestaurantinDB(inputName):
# inserts an entry into the Restaurant database
# returns a new restaurant
    print 'Test API'
    session = DBSession()
    print 'Session opened'
    try:
        newRestaurant = Restaurant(name = str(inputName))
        print 'early test'
        #instance = newRestaurant.name
        session.add(newRestaurant)
        session.commit()
        instance = newRestaurant.name
        print 'Test'
        print newRestaurant.name
        
        return newRestaurant
    except:
        session.rollback()
        return False
    finally:
        session.close()
    #print 'Session closed'
    

def getRestaurantById(inputId):
# pulls an entry by ID from the Restaurant database
# returns a restaurant
    session = DBSession()
    resultRestaurant = []
    try:
        resultRestaurant = session.query(Restaurant).filter_by(id=inputId).one()
        print 'Result found by ID'
        print resultRestaurant.id
        print resultRestaurant.name
    except:
        session.rollback()
    finally:
        session.close()
        return resultRestaurant

def getRestaurantByName(inputName):
# pulls entries by Name from the Restaurant database
# returns a list of Restaurants
    session = DBSession()
    resultRestaurant = []
    filter = "%" + str(inputName) + "%"
    try:
        resultRestaurant = session.query(Restaurant).filter(Restaurant.name.like(filter)).all()
    except:
        session.rollback()
    finally:
        session.close()
        return resultRestaurant

def setRestaurantNameById(inputId, inputName):
# finds Restaurant by Id and changes the Name
# returns a Restaurant
    #print 'Test 1'
    updatedRestaurant = getRestaurantById(inputId)
    if updatedRestaurant == []:
        return False
    updatedRestaurant.name = str(inputName)
    try:
        session = DBSession()
    # print = 'Session opened'
        session.add(updatedRestaurant)
        session.commit()
        instance = updatedRestaurant.name
        # print test
        return updatedRestaurant
    except:
        session.rollback()
        return False
    finally:
        session.close()
    #print 'Session closed'

  
def deleteRestaurantById(inputId):
# deletes an entry from the Restaurant Database By Id
    print 'Delete test 1' 
    print 'Delete test 2'
    session = DBSession()
    response =  False
    # print = 'Session opened'
    try:
        deletedRestaurant = getRestaurantById(inputId)
        session.delete(deletedRestaurant)
        session.commit()
        print 'Delete test 3'
        response = 'Restaurant Deleted'
    except:
        print 'Delete test 4'
        session.rollback()
    finally:
        session.close()
        return response
    #print 'Session closed'
    

# MENU ITEMS    

def getMenuItemsfromDB():
# pulls all entries from the Menu Item database
# returns a list of menu items
    session = DBSession()
    menuItemsList = session.query(MenuItem).all()
    session.close()
    return menuItemsList

def getMenuItemById(inputId):
# pulls an entry by ID from the Menu Item database
# returns a menu item
    session = DBSession()
    resultMenuItem = []
    try:
        resultMenuItem = session.query(MenuItem).filter_by(id=inputId).one()
    except:
        session.rollback()
    finally:
        session.close()
    return resultMenuItem

def getMenuItemsByName(inputName, inputRestaurant='-1'):
# pulls entries by Name from the Menu Item database
# returns a list of menu items
    session = DBSession()
    resultMenuItem = []
    try:
        if (inputRestaurant != '-1'):
            filterId = inputRestaurant.id
            resultMenuItem = session.query(MenuItem).filter_by(id=filterId).filter_by(name=inputName).one()
        else:
            resultMenuItem = session.query(MenuItem).filter_by(name=inputName).all()
    except:
        session.rollback()
    finally:
        session.close()
    return resultMenuItem
    
def createMenuIteminDB(inputName, inputDescription, inputCourse, inputPrice, inputRestaurant):
# inserts an entry into the Menu Item database
# returns a menuItem
    session = DBSession()
    # print = 'Session opened'
    try:
        newMenuItem = MenuItem(name = inputName, description = inputDescription, course = inputCourse, restaurant = inputRestaurant)
        session.add(newMenuItem)
        session.commit()
        return newMenuItem
    except:
        session.rollback()
        raise
    finally:
        session.close()
    #print 'Session closed'    

    
    
def setMenuItemNameById(inputId, inputName):
# finds Menu item by Id and changes the Name
# returns a menuItem
    updatedMenuItem = getMenuItemById(inputId)
    updatedMenuItem.name = inputName    
    session = DBSession()
    # print = 'Session opened'
    try:
        session.add(updatedMenuItem)
        session.commit()
        return updatedMenuItem
    except:
        session.rollback()
        raise
    finally:
        session.close()
    #print 'Session closed'

def setMenuItemDescriptionById(inputId, inputDescription):
# finds Menu item by Id and changes the description
# returns a menuItem
    updatedMenuItem = getMenuItemById(inputId)
    updatedMenuItem.description = inputDescription    
    session = DBSession()
    # print = 'Session opened'
    try:
        session.add(updatedMenuItem)
        session.commit()
        return updatedMenuItem
    except:
        session.rollback()
        raise
    finally:
        session.close()
    #print 'Session closed'
    
def setMenuItemPriceById(inputId, inputPrice):
# finds Menu item by Id and changes the price
# returns a menuItem
    updatedMenuItem = getMenuItemById(inputId)
    updatedMenuItem.price = inputPrice    
    session = DBSession()
    # print = 'Session opened'
    try:
        session.add(updatedMenuItem)
        session.commit()
        return updatedMenuItem
    except:
        session.rollback()
        raise
    finally:
        session.close()
    #print 'Session closed'

def setMenuItemCourseById(inputId, inputDescription):
# finds Menu item by Id and changes the course
# returns a menuItem
    updatedMenuItem = getMenuItemById(inputId)
    updatedMenuItem.course = inputCourse    
    session = DBSession()
    # print = 'Session opened'
    try:
        session.add(updatedMenuItem)
        session.commit()
        return updatedMenuItem
    except:
        session.rollback()
        raise
    finally:
        session.close()
    #print 'Session closed'
    
def deleteMenuItemById(inputId):
# deletes an entry from the Menu Item By Id
    deletedMenuItem = getMenuItemById(inputId)    
    session = DBSession()
    # print = 'Session opened'
    try:
        session.delete(deletedMenuItem)
        session.commit()
    except:
        session.rollback()
        raise
    finally:
        session.close()
    #print 'Session closed'


    
# myFirstRestaurant = Restaurant(name = "Pizza Palace")
# session.add(myFirstRestaurant)
# session.commit()
# session.query(Restaurant).all()
# cheesepizza = MenuItem(name = "Cheese Pizza", description = 
# "Made with all natural ingredients and fresh mozzarella", 
# course = "Entree", price = "$8.99", restaurant = myFirstRestaurant)
# session.add(cheesepizza)
# session.commit()
# session.query(MenuItem).all()
