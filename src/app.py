# src/app.py
'''
Author: Huy Le (hl9082)
Co-authors: Jason Ting, Iris Li (il6685), Raymond Lee (rl2574)
Group: 20
Course: CSCI 320
Filename: app.py
Description: 
This is the main Flask web application file. It defines the web routes
(URLs), handles user requests, interacts with the backend to fetch data,
and renders the HTML templates to display to the user.
'''
# --- Imports ---
from flask import Flask, render_template, request, redirect, url_for, session, flash # Core Flask components.
import backend # Direct import of our backend logic file.
import os # Used for the secret key.
from dotenv import find_dotenv, load_dotenv # Used to load environment variables.
import bcrypt 

# --- App Initialization ---

# Find and load the .env file from the root directory
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
        username = request.form['username']
        password = request.form['password']

        print(f"Login attempt - Username: {username}, Password: {password}")

        user = backend.login_user(username, password)
        if user:
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
        password = request.form['password']
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

        user_id = backend.create_user(
            username=request.form['username'], 
            password = hashed_password,
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
        return redirect(url_for('login'))
    
    # You can add dashboard-specific logic here, like "recently played"
    return render_template('dashboard.html')

@app.route('/search')
def search():
    """
    Handles the main search page for songs.
    Takes search and sorting parameters from the URL (GET request).
    """
    if not is_logged_in():
        return redirect(url_for('login'))

    # Get search parameters from the URL
    search_term = request.args.get('term', '')
    search_type = request.args.get('type', '')
    sort_by = request.args.get('sort', 'song_name') # Default sort
    sort_order = request.args.get('order', 'ASC')   # Default order

    search_results = []
    
    # If a search was performed, fetch results from the backend
    search_results = backend.search_songs(
        search_term=search_term or '', 
        search_type=search_type or None,
        sort_by=sort_by,
        sort_order=sort_order
    )
    
    print(search_results)

    # Always get the user's collections for the "Add to Collection" dropdown
    user_collections = backend.get_user_collections(session['user_id'])

    return render_template(
        'search.html',
        results=search_results,
        collections=user_collections,
        # Pass back search/sort parameters to keep them in the form
        term=search_term,
        type=search_type,
        sort=sort_by,
        order=sort_order
    )

# --- Collection Management Routes ---

@app.route('/collections')
def collections():
    """
    Displays a list of the user's collections.
    """
    if not is_logged_in():
        return redirect(url_for('login'))
        
    user_collections = backend.get_user_collections(session['user_id'])
    return render_template('collections.html', collections=user_collections)

@app.route('/collection/create', methods=['POST'])
def create_collection():
    """
    Handles the creation of a new, empty collection (POST request).
    """
    if not is_logged_in():
        return redirect(url_for('login'))
        
    title = request.form.get('title')
    if title:
        if not backend.create_collection(session['user_id'], title):
            flash('A collection with that name already exists.', 'danger')
        else:
            flash('Collection created successfully.', 'success')
            
    return redirect(url_for('collections'))

@app.route('/collection/<string:collection_title>')
def collection_details(collection_title):
    """
    Displays the details and list of songs for a specific collection.
    Identifies the collection by its title.
    """
    if not is_logged_in():
        return redirect(url_for('login'))
        
    details = backend.get_collection_details(session['user_id'], collection_title)
    
    if not details:
        flash('Collection not found.', 'danger')
        return redirect(url_for('collections'))
        
    return render_template('collectiondetails.html', collection=details)

@app.route('/collection/rename', methods=['POST'])
def rename_collection():
    """
    Handles renaming a collection (POST request).
    """
    if not is_logged_in():
        return redirect(url_for('login'))
        
    old_title = request.form.get('old_title')
    new_title = request.form.get('new_title')
    
    if old_title and new_title:
        if backend.rename_collection(session['user_id'], old_title, new_title):
            flash('Collection renamed successfully.', 'success')
            return redirect(url_for('collection_details', collection_title=new_title))
        else:
            flash('Failed to rename collection. Does a collection with the new name already exist?', 'danger')
            return redirect(url_for('collection_details', collection_title=old_title))
            
    return redirect(url_for('collections'))

@app.route('/collection/delete', methods=['POST'])
def delete_collection():
    """
    Handles deleting an entire collection (POST request).
    """
    if not is_logged_in():
        return redirect(url_for('login'))
        
    title = request.form.get('title')
    if title:
        backend.delete_collection(session['user_id'], title)
        flash('Collection deleted.', 'info')
            
    return redirect(url_for('collections'))

# --- Song and "Play" Routes ---

@app.route('/collection/add_song', methods=['POST'])
def add_song_to_collection():
    """
    Handles adding a single song to a collection (POST request).
    """
    if not is_logged_in():
        return redirect(url_for('login'))

    collection_title = request.form.get('collection_title')
    song_id = request.form.get('song_id')
    album_id = request.form.get('album_id') # For adding an album

    if song_id and collection_title:
        # Add a single song
        if backend.add_song_to_collection(session['user_id'], collection_title, song_id):
            flash('Song added to collection.', 'success')
        else:
            flash('Song is already in that collection.', 'warning')
            
    elif album_id and collection_title:
        # Add all songs from an album
        added_count = backend.add_album_to_collection(session['user_id'], collection_title, album_id)
        if added_count > 0:
            flash(f'Added {added_count} songs from the album.', 'success')
        else:
            flash('No new songs were added from this album.', 'info')
            
    else:
        flash('Invalid request.', 'danger')

    # Redirect back to the page the user was on
    return redirect(request.referrer or url_for('dashboard'))

@app.route('/collection/remove_song', methods=['POST'])
def remove_song_from_collection():
    """
    Handles removing a single song from a collection (POST request).
    """
    if not is_logged_in():
        return redirect(url_for('login'))
            
    collection_title = request.form.get('collection_title')
    song_id = request.form.get('song_id')
    
    if collection_title and song_id:
        backend.remove_song_from_collection(session['user_id'], collection_title, song_id)
        flash('Song removed from collection.', 'info')
            
    return redirect(url_for('collection_details', collection_title=collection_title))

@app.route('/play/song/<int:song_id>', methods=['POST'])
def play_song_route(song_id):
    """
    Logs that a user "played" a single song.
    """
    if not is_logged_in():
        return redirect(url_for('login'))
        
    backend.play_song(song_id, session['user_id'])
    flash('Song play logged!', 'success')
    
    # Redirect back to the page the user was on
    return redirect(request.referrer or url_for('dashboard'))

@app.route('/play/collection/<string:collection_title>', methods=['POST'])
def play_collection_route(collection_title):
    """
    Logs that a user "played" all songs in a collection.
    """
    if not is_logged_in():
        return redirect(url_for('login'))
        
    played_count = backend.play_collection(session['user_id'], collection_title)
    
    if played_count > 0:
        flash(f'Logged play for {played_count} songs in the collection.', 'success')
    else:
        flash('Could not play collection. Do you own it?', 'danger')
        
    return redirect(url_for('collection_details', collection_title=collection_title))

@app.route('/rate/song', methods=['POST'])
def rate_song_route():
    """
    Handles a user's rating submission for a song.
    The rating (1-5) is sent from a form.
    """
    if not is_logged_in():
        return redirect(url_for('login'))
        
    song_id = request.form.get('song_id')
    rating = request.form.get('rating')
    
    if not song_id or not rating:
        flash("Invalid rating request.", 'danger')
        return redirect(request.referrer or url_for('dashboard'))

    if backend.rate_song(session['user_id'], song_id, rating):
        flash("Your rating has been saved.", 'success')
    else:
        flash("Invalid rating. Must be between 1 and 5.", 'danger')
        
    return redirect(request.referrer or url_for('dashboard'))


# --- User Following Routes ---

@app.route('/users/search', methods=['GET', 'POST'])
def search_users():
    """
    Page for searching users (by email) and managing follows.
    - GET: Shows the search form and list of users.
    - POST: Performs the search by email.
    """
    if not is_logged_in():
        return redirect(url_for('login'))

    users = []
    search_email = ""
    if request.method == 'POST':
        search_email = request.form.get('email', '')
        if search_email:
            users = backend.search_users_by_email(session['user_id'], search_email)
    else:
        # On GET, just show all users to follow
        users = backend.get_all_users_to_follow(session['user_id'])

    return render_template('users.html', users=users, search_email=search_email)

@app.route('/follow', methods=['POST'])
def follow_user_route():
    """
    Handles the action of following another user.
    """
    if not is_logged_in():
        return redirect(url_for('login'))
        
    followee_id = request.form.get('followee_id')
    if followee_id:
        backend.follow_user(session['user_id'], followee_id)
        flash("User followed.", 'success')
    
    return redirect(request.referrer or url_for('search_users'))

@app.route('/unfollow', methods=['POST'])
def unfollow_user_route():
    """
    Handles the action of unfollowing another user.
    """
    if not is_logged_in():
        return redirect(url_for('login'))
        
    followee_id = request.form.get('followee_id')
    if followee_id:
        backend.unfollow_user(session['user_id'], followee_id)
        flash("User unfollowed.", 'info')

    return redirect(request.referrer or url_for('search_users'))

# --- Main Entry Point ---

if __name__ == '__main__':
    """
    This block runs only if the script is executed directly (e.g., `python app.py`).
    It starts the Flask development server.
    """
    app.run(debug=True)