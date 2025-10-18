# src/app.py
'''
Author: Huy Le (hl9082)
Description: This is the main program.
'''
from flask import Flask, render_template, request, redirect, url_for, session, flash
import backend # Direct import since they are in the same package
import os
from dotenv import find_dotenv, load_dotenv

# Find and load the .env file from the root directory
load_dotenv(find_dotenv())

app = Flask(__name__)
app.secret_key = os.urandom(24)

# Check for credentials before starting
if not all([os.getenv("CS_USERNAME"), os.getenv("CS_PASSWORD"), os.getenv("DB_NAME")]):
    print("FATAL ERROR: Missing database credentials in .env file.")
    print("Please create a .env file in the project root with CS_USERNAME, CS_PASSWORD, and DB_NAME.")
    exit()

def is_logged_in():
    return 'user_id' in session

@app.route('/', methods=['GET', 'POST'])
def login():
    if is_logged_in():
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        user = backend.login_user(request.form['username'], request.form['password'])
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
    if is_logged_in():
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        user_id = backend.create_user(
            username=request.form['username'], password=request.form['password'],
            first_name=request.form['first_name'], last_name=request.form['last_name'],
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
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

@app.route('/dashboard')
def dashboard():
    if not is_logged_in():
        return redirect(url_for('login'))
    collections = backend.get_user_collections(session['user_id'])
    return render_template('dashboard.html', collections=collections)

@app.route('/collections')
def collections():
    if not is_logged_in():
        return redirect(url_for('login'))
    user_collections = backend.get_user_collections(session['user_id'])
    return render_template('collections.html', collections=user_collections)

@app.route('/search')
def search():
    if not is_logged_in():
        return redirect(url_for('login'))
    return render_template('search.html')

if __name__ == '__main__':
    app.run(debug=True)