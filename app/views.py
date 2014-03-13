from app import app #comment out to run on PyAW
import sqlite3 as sqlite
from flask import render_template, abort
import unicodecsv as csv
from collections import OrderedDict

# Uncomment to run App on Python Anywhere
#from flask import Flask 
#import csv
#app = Flask(__name__)
#DATABASE = '/home/bmaionedowning/mysite/travelers.sqlite'

DATABASE = 'travelers.sqlite' #comment out to run on PyAW

# Splash page
@app.route('/')
@app.route('/index/')
def index():
	return render_template("splash.html",
		title="Welcome")

# Travelers index
@app.route('/travelers/')
def travelers():
	conn = sqlite.connect(DATABASE)
	c = conn.cursor()
	travelers = c.execute("""SELECT Name, BirthDate, DeathDate, Notes, Bibliography FROM people""").fetchall()
	conn.close()
	# if no travelers are returned, something is wrong with the database
	if len(travelers) == 0:
		abort(500)
	return render_template("travelers.html",
		title = 'Mediterranean Travlers',
		travelers = travelers)

# Render automatic templates for individual travelers
@app.route('/travelers/<name>')
def traveler(name):
	conn = sqlite.connect(DATABASE)
	c = conn.cursor()
	try:
		attributes = c.execute("""SELECT * FROM people WHERE Name = ?""", (name,)).fetchall()
		attributes = attributes[0]
		movements = c.execute("""SELECT * FROM places WHERE PersonID = ? ORDER BY PlaceOrder""", (attributes[0],)).fetchall()
		offices = c.execute("""SELECT * FROM offices WHERE PersonID = ?""", (attributes[0],)).fetchall()
		points_array = []
		for movement in movements:
			if movement[8] != '' and movement[9] != '':
				points_array.append([movement[8], movement[9]])


		return render_template("person.html",
			title = attributes[1],
			points = points_array,
			attributes = attributes,
			references = attributes[-1].split(';'),
			offices = offices,
			movements = movements,
			numoffice = len(offices),
			numplace = len(movements))
	except IndexError:
		abort(404)

# Render list of all places
@app.route('/places/')
def places():
	conn = sqlite.connect(DATABASE)
	c = conn.cursor()
	places = c.execute("""SELECT places.*, people.Name FROM places LEFT JOIN people ON places.PersonId = people.PersonID ORDER BY places.PlaceName """).fetchall()	
	pldict = OrderedDict()
	for place in places:
		if place[4] not in pldict:
			pldict[place[4]] = [place[-1]]
		elif place[4] in pldict:
			pldict[place[4]].append(place[-1])

	place_list = []

	for place, travelers in pldict.items():
		place_list.append([place, set(travelers)])
	
	return render_template("places.html",
		title = 'Places',
		places = place_list) 

@app.route('/places/<place>')
def place(place):
	conn = sqlite.connect(DATABASE)
	c = conn.cursor()
	destripped_place = place.replace('_', ' ')
	print destripped_place
	try:
		plattrs = c.execute("""SELECT places.*, people.Name FROM places LEFT JOIN people ON places.PersonId = people.PersonID WHERE places.PlaceNameCln = ? ORDER BY places.PlaceNameCln""", (destripped_place,)).fetchall()
		print plattrs
		conn.close()
		if len(plattrs) == 0:
			raise IndexError
		return render_template("place.html",
			numvisits = len(plattrs),
			numtravelers = len(set([pl[-1] for pl in plattrs])),
			title = destripped_place,
			plattrs = plattrs)

	except IndexError:
		conn.close()
		abort(404)

@app.route('/links/')
def links():
	return render_template("links.html",
		title = 'Links')

########## ERROR HANDLERS ############
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(403)
def forbidden(e):
	return render_template('403.html'), 403

@app.errorhandler(500)
def forbidden(e):
	return render_template('500.html'), 500

