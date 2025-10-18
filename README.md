# csci320-group20

Members:
- Huy Le (hl9082)
- Jason Ting
- Iris Li
- Raymond Lee

## Setup and Installation

### Prerequisites

-   Python 3.6+
-   `pip` (Python package installer)
-   Your RIT CS username, password, and database name.

### Instructions

1.  **Save Project Files**
    -   Create the directory structure as shown above and save all the provided files.

2.  **Enter Your Credentials**
    -   Open the `.env` file.
    -   Fill in the `CS_USERNAME`, `CS_PASSWORD`, and `DB_NAME` variables with your RIT CS credentials.

3.  **Install Dependencies**
    -   Navigate to the `src` directory in your terminal.
    -   Install the required packages using the `requirements.txt` file:
        ```bash
        pip install -r requirements.txt
        ```

4.  **Initialize the Database**
    -   Run the setup script. This command will connect to `starbug.cs.rit.edu`, drop any existing tables, create the new schema, and populate it with sample data in your remote PostgreSQL database.
        
        python database_setup.py
        

5.  **Run the Application**
    -   Start the Flask web server:python src/app.py
        

6.  **Access the Application**
    -   Open your web browser and navigate to:
        [http://127.0.0.1:5000](http://127.0.0.1:5000)