#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import json
from sre_parse import State
from xml.dom.minidom import AttributeList
import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import *
from flask_migrate import Migrate

#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')

# TODO: connect to a local postgresql database

#----------------------------------------------------------------------------#
# Models.
#----------------------------------------------------------------------------#
from model import db, Venue, Artist, Show
db.init_app(app)
migrate = Migrate(app, db)
#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
  date = dateutil.parser.parse(value)
  if format == 'full':
      format="EEEE MMMM, d, y 'at' h:mma"
  elif format == 'medium':
      format="EE MM, dd, y h:mma"
  return babel.dates.format_datetime(date, format, locale='en')

app.jinja_env.filters['datetime'] = format_datetime

#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#

@app.route('/')
def index():
  return render_template('pages/home.html')


#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():
  # TODO: replace with real venues data.

  area=[]
  actual_venue=[]
  distinct_venue=Venue.query.distinct(Venue.city, Venue.state).all()
  for venue in distinct_venue:
    filtered_venue=Venue.query.filter(Venue.city==venue.city, Venue.state==venue.state).all()
    for venue in filtered_venue:
      actual_venue+=[{
        'id':venue.id,
        'name':venue.name
      }]
      area+=[{
        'city':venue.city,
        'state':venue.state,
        'venues':actual_venue
      }]
    actual_venue=[]

  return render_template('pages/venues.html', areas=area);

@app.route('/venues/search', methods=['POST'])
def search_venues():
  # TODO: implement search on venues with partial string search. Ensure it is case-insensitive.
  # seach for Hop should return "The Musical Hop".
  # search for "Music" should return "The Musical Hop" and "Park Square Live Music & Coffee"
  search = request.form['search_term']
  searched_venue=Venue.query.filter(Venue.name.ilike(f'%{search}%')).all()
 
  if searched_venue:
    search_data=[]
    for data in searched_venue:
      search_data += [{
         'id':data.id,
         'name':data.name
        }] 
      response={
        'count':len(searched_venue),
        'data': search_data
      }
  else:
    response={
      'Count':0,
    }
  
  return render_template('pages/search_venues.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
  # shows the venue page with the given venue_id
  # TODO: replace with real venue data from the venues table, using venue_id
  main_venue = Venue.query.get(venue_id)
  upcoming_shows = []
  past_shows = []

  venue={
    "id": main_venue.id,
    "name": main_venue.name,
    "genres": main_venue.genres,
    "city": main_venue.city,
    "state": main_venue.state,
    'address': main_venue.address,
    "phone": main_venue.phone,
    'website': main_venue.website,
    "seeking_talent": main_venue.seeking_talent,
    'facebook_link': main_venue.facebook_link,
    'seeking_description':main_venue.seeking_description,
    "image_link": main_venue.image_link,
    "past_shows": past_shows,
    "upcoming_shows": upcoming_shows,
    "upcoming_shows_count": len(upcoming_shows),
    "past_shows_count": len(past_shows),
  }

  upcoming_shows_query = db.session.query(Show, Artist).join(Artist).filter(Show.venue_id==venue_id).filter(Show.start_time>datetime.now()).all()   
  for show, artist in upcoming_shows_query: 
    upcoming_shows.append({
      'artist_id':artist.id,
      'artist_name':artist.name,
      'artist_image_link':artist.image_link,
      'start_time': str(show.start_time),
    })
    venue.update({
      "upcoming_shows_count": len(upcoming_shows),
    })

  past_shows_query = db.session.query(Show, Artist).join(Artist).filter(Show.venue_id==venue_id).filter(Show.start_time<datetime.now()).all()   
  for show, artist in past_shows_query:
    past_shows.append({
      'artist_id':artist.id,
      'artist_name':artist.name,
      'artist_image_link':artist.image_link,
      'start_time': str(show.start_time),
    })
    venue.update({
      "past_shows_count": len(past_shows),
    })
  

  return render_template('pages/show_venue.html', venue=venue)

#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
  form = VenueForm()
  return render_template('forms/new_venue.html', form=form)

@app.route('/venues/create', methods=['POST'])
# TODO: insert form data as a new Venue record in the db, instead
# TODO: modify data to be the data object returned from db insertion

def create_venue_submission():  
  form_data = VenueForm(request.form)
  if form_data.validate():
    newvenue = Venue (
      name=form_data.name.data, 
      city=form_data.city.data,
      state=form_data.state.data,
      address=form_data.address.data,
      phone=form_data.phone.data,
      genres=form_data.genres.data,
      website=form_data.website_link.data,
      facebook_link=form_data.facebook_link.data,
      image_link=form_data.image_link.data,
      seeking_talent=form_data.seeking_talent.data,
      seeking_description=form_data.seeking_description.data
    )
    try:
      db.session.add(newvenue)
      db.session.commit()
      # on successful db insert, flash success
      flash('Venue ' + request.form['name'] + ' was successfully listed!')
    except:
      db.session.rollback()
      flash('Venue ' + request.form['name'] + ' was not successfully listed!')
    finally:
      db.session.close()
  else:
    for field, message in form_data.errors.items():
        flash(field + ' - ' + str(message), 'danger')

  # TODO: on unsuccessful db insert, flash an error instead.
  # e.g., flash('An error occurred. Venue ' + data.name + ' could not be listed.')
  # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
  return render_template('pages/home.html')

@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):

  # TODO: Complete this endpoint for taking a venue_id, and using
  # SQLAlchemy ORM to delete a record. Handle cases where the session commit could fail.
  try:
    delete_venue = Venue.query.get(venue_id)
    db.session.delete(delete_venue)
    flash('Venue ' + request.form['name'] + ' was successfully Deleted!')
  except:
    db.session.rollback()
    flash('An error has occurred. Venue ' + request.form['name'] + ' could not be Deleted!')
  finally:
    db.session.close
  # BONUS CHALLENGE: Implement a button to delete a Venue on a Venue Page, have it so that
  # clicking that button delete it from the db then redirect the user to the homepage
  return render_template('pages/home.html')

#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
  # TODO: replace with real data returned from querying the database
  return render_template('pages/artists.html', artists=Artist.query.all())

@app.route('/artists/search', methods=['POST'])
def search_artists():
  # TODO: implement search on artists with partial string search. Ensure it is case-insensitive.
  # seach for "A" should return "Guns N Petals", "Matt Quevado", and "The Wild Sax Band".
  # search for "band" should return "The Wild Sax Band".
  search = request.form['search_term']
  searched_artist=Artist.query.filter(Artist.name.ilike(f'%{search}%')).all()
 
  if searched_artist:
    search_data=[]
    for data in searched_artist:
      search_data += [{
         'id':data.id,
         'name':data.name
        }] 
      response={
        'count':len(searched_artist),
        'data': search_data
      }
  else:
    response={
      'Count':0,
    }
  return render_template('pages/search_artists.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
  # shows the artist page with the given artist_id
  # TODO: replace with real artist data from the artist table, using artist_id
  main_artist = Artist.query.get(artist_id)
  upcoming_shows = []
  past_shows = []

  artist={
    "id": main_artist.id,
    "name": main_artist.name,
    "genres": main_artist.genres,
    "city": main_artist.city,
    "state": main_artist.state,
    "phone": main_artist.phone,
    'website': main_artist.website,
    'facebook_link': main_artist.facebook_link,
    "seeking_venue": main_artist.seeking_venue,
    'seeking_description':main_artist.seeking_description,
    "image_link": main_artist.image_link,
    "past_shows": past_shows,
    "upcoming_shows": upcoming_shows,
    "upcoming_shows_count": len(upcoming_shows),
    "past_shows_count": len(past_shows),
  }

  upcoming_shows_query = db.session.query(Show, Venue).join(Venue).filter(Show.artist_id==artist_id).filter(Show.start_time>datetime.now()).all()   
  for show, venue in upcoming_shows_query: 
    upcoming_shows.append({
      'venue_id':venue.id,
      'venue_name':venue.name,
      'venue_image_link':venue.image_link,
      'start_time': str(show.start_time),
    })
    artist.update({
      "upcoming_shows_count": len(upcoming_shows),
    })

  past_shows_query = db.session.query(Show, Venue).join(Venue).filter(Show.artist_id==artist_id).filter(Show.start_time<datetime.now()).all()   
  for show, venue in past_shows_query:
    past_shows.append({
      'venue_id':venue.id,
      'venue_name':venue.name,
      'venue_image_link':venue.image_link,
      'start_time': str(show.start_time),
    })
    artist.update({
      "past_shows_count": len(past_shows),
    })
    
  return render_template('pages/show_artist.html', artist=artist)

#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
  form = ArtistForm()
  artist = Artist.query.get(artist_id)
  # TODO: populate form with fields from artist with ID <artist_id>
  return render_template('forms/edit_artist.html', form=form, artist=artist)

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
  # TODO: take values from the form submitted, and update existing
  # artist record with ID <artist_id> using the new attributes
  form_data = ArtistForm(request.form)
  if form_data.validate():
    editartist =Artist.query.get(artist_id)
    editartist.name=form_data.name.data
    editartist.city=form_data.city.data
    editartist.state=form_data.state.data
    editartist.phone=form_data.phone.data
    editartist.genres=form_data.genres.data
    editartist.website=form_data.website_link.data
    editartist.facebook_link=form_data.facebook_link.data
    editartist.image_link=form_data.image_link.data
    editartist.seeking_venue=form_data.seeking_venue.data
    editartist.seeking_description=form_data.seeking_description.data
    try:
      db.session.commit()
      # on successful db insert, flash success
      flash('Artist ' + request.form['name'] + ' was successfully Updated!')
    except:
      db.session.rollback()
      flash('An error occurred. Artist ' + request.form['name'] + ' could not be updated!')
    finally:
      db.session.close()
  else:
    for field, message in form_data.errors.items():
        flash(field + ' - ' + str(message), 'danger')

  return redirect(url_for('show_artist', artist_id=artist_id))

@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
  form = VenueForm()
  # TODO: populate form with values from venue with ID <venue_id>
  venue = Venue.query.get(venue_id)
  return render_template('forms/edit_venue.html', form=form, venue=venue)

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
  # TODO: take values from the form submitted, and update existing
  # venue record with ID <venue_id> using the new attributes
  form_data = VenueForm(request.form)
  if form_data.validate():
    editvenue =Venue.query.get(venue_id)
    editvenue.name=form_data.name.data
    editvenue.city=form_data.city.data
    editvenue.state=form_data.state.data
    editvenue.address=form_data.address.data
    editvenue.phone=form_data.phone.data
    editvenue.genres=form_data.genres.data
    editvenue.website=form_data.website_link.data
    editvenue.facebook_link=form_data.facebook_link.data
    editvenue.image_link=form_data.image_link.data
    editvenue.seeking_talent=form_data.seeking_talent.data
    editvenue.seeking_description=form_data.seeking_description.data
    try:
      db.session.commit()
      # on successful db insert, flash success
      flash('Venue ' + request.form['name'] + ' was successfully Updated!')
    except:
      db.session.rollback()
      flash('An error occurred. Venue ' + request.form['name'] + ' could not be updated!')
    finally:
      db.session.close()
  else:
    for field, message in form_data.errors.items():
        flash(field + ' - ' + str(message), 'danger')

  return redirect(url_for('show_venue', venue_id=venue_id))

#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
  form = ArtistForm()
  return render_template('forms/new_artist.html', form=form)

@app.route('/artists/create', methods=['POST'])
def create_artist_submission(): 
  form_data = ArtistForm(request.form)
  if form_data.validate():
    newartist = Artist (
      name=form_data.name.data, 
      city=form_data.city.data,
      state=form_data.state.data,
      phone=form_data.phone.data,
      genres=form_data.genres.data,
      image_link=form_data.image_link.data,
      facebook_link=form_data.facebook_link.data,
      website=form_data.website_link.data,
      seeking_venue=form_data.seeking_venue.data,
      seeking_description=form_data.seeking_description.data
    )
    try:
      db.session.add(newartist)
      db.session.commit()
      # on successful db insert, flash success
      flash('Artist ' + request.form['name'] + ' was successfully listed!')
    except:
      db.session.rollback()
      flash('An error occurred. Artist ' + request.form['name'] + ' could not be listed!')
    finally:
      db.session.close()
  else:
    for field, message in form_data.errors.items():
      flash(field + ' - ' + str(message), 'danger')

  # called upon submitting the new artist listing form
  # TODO: insert form data as a new Artist record in the db, instead
  # TODO: modify data to be the data object returned from db insertion
  # TODO: on unsuccessful db insert, flash an error instead.
  # e.g., flash('An error occurred. Artist ' + data.name + ' could not be listed.')
  return render_template('pages/home.html')


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
  # displays list of shows at /shows
  # TODO: replace with real venues data.
  shows= Show.query.all()
  data=[]
  for datum in shows:
    venue= Venue.query.get(datum.venue_id)
    artist = Artist.query.get(datum.artist_id)
    data+=[{
      'venue_id': venue.id,
      'artist_id': artist.id,
      'artist_name':artist.name,
      'venue_name':venue.name,
      'artist_image_link':artist.image_link,
      'start_time': str(datum.start_time),
    }]    

  return render_template('pages/shows.html', shows=data)

@app.route('/shows/create')
def create_shows():
  # renders form. do not touch.
  form = ShowForm()
  return render_template('forms/new_show.html', form=form)

@app.route('/shows/create', methods=['POST'])
def create_show_submission():
  # called to create new shows in the db, upon submitting new show listing form
  form_data = ShowForm(request.form)
  if form_data.validate():
    newshow = Show(
      artist_id=form_data.artist_id.data, 
      venue_id=form_data.venue_id.data,
      start_time=form_data.start_time.data)
    try:
      db.session.add(newshow)
      db.session.commit()
      # on successful db insert, flash success
      flash('Show was successfully listed!')
    except:
      db.session.rollback()
      flash('An error occurred. Show could not be listed.')
    finally:
      db.session.close()
  else:
    for field, message in form_data.errors.items():
        flash(field + ' - ' + str(message), 'danger')

  # TODO: insert form data as a new Show record in the db, instead
  # TODO: on unsuccessful db insert, flash an error instead.
  # e.g., flash('An error occurred. Show could not be listed.')
  # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
  return render_template('pages/home.html')

@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

#----------------------------------------------------------------------------#
# Launch.
#----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
