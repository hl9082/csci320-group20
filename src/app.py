# src/app.py
'''
Author: Huy Le (hl9082)
Co-authors: Jason Ting, Iris Li, Raymond Lee
 Group: 20
 Course: CSCI 320
 Filename: app.py
Description: 
This is the main Flask web application file. It defines the web routes
(URLs), handles user requests, interacts with the backend to fetch data,
          and renders the HTML templates to display to the user.
'''
from flask import Flask, render_template, request, redirect, url_for, session, flash
import backend  # Imports our backend.py
import os
from dotenv import find_dotenv, load_dotenv

# Find and load the .env file
load_dotenv(find_dotenv())

app = Flask(__name__)
# Create a secret key for session management.
app.secret_key = os.urandom(24)

# --- Prerequisite Check ---

# Check for credentials before starting
if not all([os.getenv("CS_USERNAME"), os.getenv("CS_PASSWORD"), os.getenv("DB_NAME")]):
    print("FATAL ERROR: Missing database credentials in .env file.")
    print("Please create a .env file in the project root with CS_USERNAME, CS_PASSWORD, and DB_NAME.")
    exit()

# --- Helper Function ---

def is_logged_in():
    """
    Checks if a user is currently logged in by looking for 'user_id' in the session.
    
    Returns: 
        True if 'user_id' is in session, False otherwise.
    """
    return 'user_id' in session

# --- User Account Routes ---

@app.route('/', methods=['GET', 'POST'])
def login():
    """
    Handles the login page.
    - GET: Shows the login page.
    - POST: Attempts to log the user in.
    """
    if is_logged_in():
        return redirect(url_for('dashboard')) # Go to dashboard if already logged in

    if request.method == 'POST':
        # Pass login credentials to the backend
        user = backend.login_user(request.form['username'], request.form['password'])
        if user:
            # If login is successful, store user info in the session
            session['user_id'] = user['userid']
            session['username'] = user['username']
            flash('Login successful!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password.', 'danger')
            
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    """
    Handles the user registration page.
    - GET: Shows the registration form.
    - POST: Attempts to create a new user.
    """
    if is_logged_in():
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        user_id = backend.create_user(
            username=request.form['username'], 
            password=request.form['password'],
            first_name=request.form['first_name'], 
            last_name=request.form['last_name'],
            email=request.form['email']
        )
        if user_id:
            flash('Account created successfully! Please log in.', 'success')
            return redirect(url_for('login'))
        else:
            flash('Username or email already exists.', 'danger')
            
    return render_template('register.html')

@app.route('/logout')
def logout():
    """
    Logs the user out by clearing the session.
    """
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

# --- Core App Routes ---

@app.route('/dashboard')
def dashboard():
    """
    Serves the main dashboard page.
    Redirects to login if the user is not authenticated.
    """
    if not is_logged_in():
        flash('You must be logged in to view this page.', 'danger')
        return redirect(url_for('login'))
        
    return render_template('dashboard.html')

@app.route('/search', methods=['GET', 'POST'])
def search():
    """
    Handles song searching.
    On GET, shows the search page.
    On POST, performs the search and returns results.
    """
    if not is_logged_in():
        flash('You must be logged in to view this page.', 'danger')
        return redirect(url_for('login'))

    songs = None
    # Get parameters from the form (for POST) or URL (for GET, e.g. re-sorting)
    search_term = request.values.get('search_term', "")
    search_type = request.values.get('search_type', 'song')
    sort_by = request.values.get('sort_by', 'song_name')
    sort_order = request.values.get('sort_order', 'ASC')
    
    # Only perform a search if a term was provided
    if search_term:
        songs = backend.search_songs(search_term, search_type, sort_by, sort_order)
        if not songs:
            flash('No songs found matching your criteria.', 'info')

    # Get user's collections for the "Add to Collection" dropdown
    collections = backend.get_user_collections(session['user_id'])
    
    return render_template('search.html',
                           songs=songs,
                           collections=collections,
                           search_term=search_term,
                           search_type=search_type,
                           sort_by=sort_by,
                           sort_order=sort_order)

# --- Collection Routes ---

@app.route('/collections')
def collections():
    """
    Displays a list of the user's collections.
    """
    if not is_logged_in():
        flash('You must be logged in to view this page.', 'danger')
        return redirect(url_for('login'))
        
    user_collections = backend.get_user_collections(session['user_id'])
    return render_template('collections.html', collections=user_collections)

@app.route('/collection/<collection_title>')
def collection_details(collection_title):
    """
    Shows the details and song list for a specific collection.
    """
    if not is_logged_in():
        flash('You must be logged in to view this page.', 'danger')
        return redirect(url_for('login'))
        
    collection = backend.get_collection_details(session['user_id'], collection_title)
    
    if not collection:
        flash('Collection not found or you do not have permission to view it.', 'danger')
        return redirect(url_for('collections'))

    # Get the collections list for the "Add" dropdown in the details page
    collections_list = backend.get_user_collections(session['user_id'])
        
    # Using your specific file name 'collectiondetails.html'
    return render_template('collectiondetails.html', collection=collection, collections=collections_list)


@app.route('/collection/create', methods=['POST'])
def create_collection():
    """
    Handles the creation of a new, empty collection.
    (Form submitted from the /collections page)
    """
    if not is_logged_in():
        return redirect(url_for('login'))
        
    title = request.form.get('title')
    if not title:
        flash('Collection name cannot be empty.', 'danger')
        return redirect(url_for('collections'))
        
    if backend.create_collection(session['user_id'], title):
        flash(f'Collection "{title}" created successfully.', 'success')
    else:
        flash(f'A collection with the name "{title}" already exists.', 'danger')
        
    return redirect(url_for('collections'))

@app.route('/collection/rename', methods=['POST'])
def rename_collection():
    """
    Handles renaming a collection.
    (Form submitted from the /collection_details page)
    """
    if not is_logged_in():
        return redirect(url_for('login'))
        
    old_title = request.form.get('old_title')
    new_title = request.form.get('new_title')
    
    if not new_title:
        flash('New collection name cannot be empty.', 'danger')
        return redirect(url_for('collection_details', collection_title=old_title))
        
    if backend.rename_collection(session['user_id'], old_title, new_title):
        flash('Collection renamed successfully.', 'success')
        # Redirect to the new URL
        return redirect(url_for('collection_details', collection_title=new_title))
    else:
        flash('Failed to rename collection. A collection with that name may already exist.', 'danger')
        return redirect(url_for('collection_details', collection_title=old_title))

@app.route('/collection/delete', methods=['POST'])
def delete_collection():
    """
    Handles deleting an entire collection.
    (Form submitted from the /collection_details page)
    """
    if not is_logged_in():
        return redirect(url_for('login'))
        
    title = request.form.get('title')
    if backend.delete_collection(session['user_id'], title):
        flash(f'Collection "{title}" deleted successfully.', 'success')
    else:
        flash('Failed to delete collection.', 'danger')
        
    return redirect(url_for('collections'))

# --- Collection-Song Routes ---

@app.route('/collection/add_song', methods=['POST'])
def add_song_to_collection():
    """
    Handles adding a single song to a collection.
    (Form submitted from /search or /collection_details)
    """
    if not is_logged_in():
        return redirect(url_for('login'))
        
    collection_title = request.form.get('collection_title')
    song_id = request.form.get('song_id')
    
    if not collection_title:
        flash('You must select a collection.', 'danger')
        return redirect(request.referrer)

    if backend.add_song_to_collection(session['user_id'], collection_title, song_id):
        flash('Song added to collection.', 'success')
    else:
        flash('Failed to add song. It may already be in the collection.', 'warning')
        
    return redirect(request.referrer) # Go back to the page they were on

@app.route('/collection/add_album', methods=['POST'])
def add_album_to_collection():
    """
    Handles adding all songs from an album to a collection.
    (Form submitted from /search or /collection_details)
    """
    if not is_logged_in():
        return redirect(url_for('login'))
        
    collection_title = request.form.get('collection_title')
    album_id = request.form.get('album_id')
    
    if not collection_title:
        flash('You must select a collection.', 'danger')
        return redirect(request.referrer)
    
    added_count = backend.add_album_to_collection(session['user_id'], collection_title, album_id)
    
    if added_count > 0:
        flash(f'Successfully added {added_count} new songs to the collection.', 'success')
    else:
        flash('No new songs were added. They may all be in the collection already.', 'info')
        
    return redirect(request.referrer)

@app.route('/collection/remove_song', methods=['POST'])
def remove_song_from_collection():
    """
    Handles removing a single song from a collection.
    (Form submitted from the /collection_details page)
    """
    if not is_logged_in():
        return redirect(url_for('login'))
        
    collection_title = request.form.get('collection_title')
    song_id = request.form.get('song_id')
    
    if backend.remove_song_from_collection(session['user_id'], collection_title, song_id):
        flash('Song removed from collection.', 'success')
    else:
        flash('Failed to remove song.', 'danger')
        
    return redirect(url_for('collection_details', collection_title=collection_title))

# --- "Play" and "Follow" Routes ---

@app.route('/play/song', methods=['POST'])
def play_song():
    """Logs that a user played a single song."""
    if not is_logged_in():
        return redirect(url_for('login'))
        
    song_id = request.form.get('song_id')
    if backend.play_song(song_id, session['user_id']):
        flash('Song play logged!', 'success')
    else:
        flash('Failed to log song play.', 'danger')
        
    return redirect(request.referrer)

@app.route('/play/collection', methods=['POST'])
def play_collection():
    """Logs that a user played an entire collection."""
    if not is_logged_in():
        return redirect(url_for('login'))
        
    collection_title = request.form.get('collection_title')
    played_count = backend.play_collection(session['user_id'], collection_title)
    
    if played_count > 0:
        flash(f'Logged play for {played_count} songs in "{collection_title}".', 'success')
    else:
        flash('Failed to log collection play. The collection might be empty.', 'warning')
        
    return redirect(request.referrer)

@app.route('/rate_song', methods=['POST'])
def rate_song():
    """Handles adding or updating a user's rating for a song."""
    if not is_logged_in():
        return redirect(url_for('login'))
        
    song_id = request.form.get('song_id')
    rating = request.form.get('rating')
    
    if backend.rate_song(session['user_id'], song_id, rating):
        flash(f'Song rated {rating} stars.', 'success')
    else:
        flash('Failed to save rating. Please enter a number between 1 and 5.', 'danger')
        
    return redirect(request.referrer)

@app.route('/users', methods=['GET', 'POST'])
def users():
    """
    Shows a list of other users to follow/unfollow.
    Can be filtered by an email search.
    """
    if not is_logged_in():
        flash('You must be logged in to view this page.', 'danger')
        return redirect(url_for('login'))

    search_email = request.form.get('search_email', "")
    
    if search_email:
        user_list = backend.search_users_by_email(session['user_id'], search_email)
    else:
        user_list = backend.get_all_users_to_follow(session['user_id'])
        
    return render_template('users.html', user_list=user_list, search_email=search_email)

@app.route('/follow', methods=['POST'])
def follow():
    """Handles following another user."""
    if not is_logged_in():
        return redirect(url_for('login'))
        
    followee_id = request.form.get('followee_id')
    if backend.follow_user(session['user_id'], followee_id):
        flash('User followed!', 'success')
    else:
        flash('Failed to follow user.', 'danger')
        
    return redirect(url_for('users'))

@app.route('/unfollow', methods=['POST'])
def unfollow():
    """Handles unfollowing another user."""
    if not is_logged_in():
        return redirect(url_for('login'))
        
    followee_id = request.form.get('followee_id')
    if backend.unfollow_user(session['user_id'], followee_id):
        flash('User unfollowed.', 'success')
    else:
        # Note: 'Entry' was likely a typo in the original, fixed to 'danger'
        flash('Failed to unfollow user.', 'danger')
        
    return redirect(url_for('users'))

# --- Main execution ---

if __name__ == '__main__':
    """
    This block runs only if the script is executed directly (e.g., `python app.py`).
    It starts the Flask development server.
    """
    app.run(debug=True)