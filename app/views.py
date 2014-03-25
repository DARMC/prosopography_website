from app import app #comment out to run on PyAW
import sqlite3 as sqlite
from flask import render_template, abort, jsonify, make_response, request
from collections import OrderedDict
import json
import random

### Uncomment to run App on Python Anywhere ###
#from flask import Flask 
#app = Flask(__name__)
#DATABASE = '/home/bmaionedowning/mysite/travelers.sqlite'

DATABASE = 'travelers.sqlite' #comment out to run on PyAW

def query_travelers_database(query):
    conn = sqlite.connect(DATABASE)
    c = conn.cursor()
    travelers = c.execute(query).fetchall()
    conn.close()

    return travelers

# Splash page
@app.route('/')
@app.route('/index/')
def index():
    return render_template("splash.html",
        title="Welcome")

# Travelers index
@app.route('/travelers/')
def travelers():
    # query information about all travelers
    travelers = query_travelers_database("""SELECT Name, BirthDate, DeathDate, Blurb, Bibliography FROM people ORDER BY Name""")

    # if no travelers are returned, something is wrong with the database
    if len(travelers) == 0:
        abort(500)
    # otherwise convert into a serialized format
    else:
        output = [{'number': i, 'name': t[0], 'birthDate': t[1], 'deathDate': t[2], 'notes': t[3],
            'bibliography': t[4]} for i, t in enumerate(travelers)]

    return render_template("travelers.html",
        title = 'Mediterranean Travlers',
        travelers = output)

# Render templates for individual travelers
@app.route('/travelers/<name>')
def traveler(name):
    conn = sqlite.connect(DATABASE)
    c = conn.cursor()
    
    try:
        attributes = c.execute("""SELECT * FROM people WHERE Name = ?""", (name,)).fetchall()[0]
        movements = c.execute("""SELECT * FROM places WHERE PersonID = ? ORDER BY PlaceOrder""", (attributes[0],)).fetchall()
        offices = c.execute("""SELECT * FROM offices WHERE PersonID = ?""", (attributes[0],)).fetchall()
        points = [[m[8], m[9]] for m in movements if m[8] != '' and m[9] != '']

    except IndexError:
        abort(404)

    return render_template("person.html",
        title = attributes[1],
        points = points,
        attributes = attributes,
        references = attributes[-1].split(';'),
        offices = offices,
        movements = movements,
        numoffice = len(offices),
        numplace = len(movements))


# Render list of all places
@app.route('/places/')
def places():
    conn = sqlite.connect(DATABASE)
    c = conn.cursor()
    places = c.execute("""SELECT places.*, people.Name 
                          FROM places 
                          LEFT JOIN people 
                          ON places.PersonId = people.PersonID 
                          ORDER BY places.PlaceName """).fetchall()  
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
        plattrs = c.execute("""SELECT places.*, people.Name 
                               FROM places 
                               LEFT JOIN people 
                               ON places.PersonId = people.PersonID 
                               WHERE places.PlaceNameCln = ? 
                               ORDER BY places.PlaceNameCln""", (destripped_place,)).fetchall()
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

@app.route('/search/', methods = ['GET', 'POST'])
def search():
    if request.method == 'POST':
        query = request.form['searchBox']
        conn = sqlite.connect(DATABASE)
        c = conn.cursor()
        place_results = c.execute("""SELECT * FROM places
                                      WHERE PlaceNameCln LIKE ?
                                      GROUP BY places.PlaceNameCln
                                      ORDER BY places.PlaceNameCln""", ('%'+query+'%',)).fetchall()

        person_results = c.execute("""SELECT * FROM people
                                      WHERE Name LIKE ?
                                      ORDER BY Name""", ('%'+query+'%',)).fetchall()
        
        return render_template("search_results.html",
            place_candidates = place_results,
            person_candidates = person_results,
            title = query)

    else:
        return render_template("search.html",
            title = 'Search')

#api description/documentation page
@app.route('/api/v1/')
@app.route('/API/v1/')
def api_splash():
    return render_template("api_splash.html",
        title = 'DARMC Prosopography API')

@app.route('/api/v1/places/<place>', methods = ['GET'])
def place_api(place):
    conn = sqlite.connect(DATABASE)
    c = conn.cursor()
    plup = place.upper()
    search_result = c.execute("""SELECT *
                                 FROM places
                                 WHERE upper(PlaceName) = ?""", (plup,)).fetchall()
    
    final_results = []
    for r in search_result:
        final_results.append({
            'PlaceID': r[0],
            'PersonID': r[1],
            'OfficeID': r[2],
            'Attributes': {
                'PlaceName': r[3],
                'PlaceNameCln': r[4],
                'PlaceSecondary': r[5],
                'PlaceCertainty': r[6],
                'PlaceOrder': r[7],
                'PlaceLat': r[8],
                'PlaceLng': r[9],
                'Centroid': r[10]
                },
            'Activity Detail': {
                'ActivityCat': r[11],
                'ActivityQ': r[12],
                'ActivityDsc': r[13],
                'ArrMode': r[14],
                'ArrDecimal': r[15],
                'ArrYear': r[16],
                'DepDecimal': r[17],
                'DepYear': r[18]           
                },
            'PelagiosLink': r[19]
            })
    if len(final_results) == 0:
        return json.dumps({'error':'No results returned for query {}'.format(place)})
    else:
        return json.dumps(final_results)

########## ERROR HANDLERS ############
@app.errorhandler(404)
def page_not_found(e):
    puns = [
        "I'm not your webpage, baby!",
        "You must construct additional pages."
    ]
    return render_template('404.html',
        pun = random.choice(puns)), 404

@app.errorhandler(403)
def forbidden(e):
    return render_template('403.html'), 403

@app.errorhandler(500)
def forbidden(e):
    return render_template('500.html'), 500

