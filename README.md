# csci320-group20

Members:
- Huy Le (hl9082)
- Jason Ting
- Iris Li
- Raymond Lee

## Project structure
CSCI320-Group20/
├── src/
│   ├── app.py
│   ├── backend.py
│   ├── db_connector.py
│   ├── requirements.txt
│   └── templates/
│       └── ... (HTML files)
├── .env
├── .gitignore
└── README.md

## Features

-   User account creation and login against the remote database.
-   Create, view, rename, and delete music collections.
-   Search for songs by title, artist, album, or genre.
-   Sort search results.
-   Simulate playing songs and entire collections, with play counts recorded.

## Setup and Installation

### Prerequisites

-   Python 3.6+
-   `pip` (Python package installer)
-   Your RIT CS username and password.
-   An existing, populated `p320_20` database on `starbug.cs.rit.edu`.

### Instructions

1.  **Save Project Files**
    -   Create the directory structure as shown above and save all the provided files.

2.  **Create and Configure the `.env` File**
    -   In the src directory, create a file named `.env`.
    -   Open the file and add your credentials for the `p320_20` database:
        ```env
        CS_USERNAME="YOUR_CS_USERNAME"
        CS_PASSWORD="YOUR_CS_PASSWORD"
        DB_NAME="p320_20"
        ```

3.  **Install Dependencies**
    -   Navigate to the `music_app` directory in your terminal.
    -   Install or upgrade the required packages using the `requirements.txt` file:
        ```bash
        pip install --upgrade -r src/requirements.txt
        ```

4.  **Run the Application**
    -   Start the Flask web server. It will connect to your existing database.
        ```bash
        cd src
        python app.py
        ```

5.  **Access the Application**
    -   Open your web browser and navigate to:
        [http://127.0.0.1:5000](http://127.0.0.1:5000)
    -   You can now log in with the user data present in your remote database.