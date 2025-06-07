# How to use

## Step 1: 
    Install Postgresql:
     - sudo apt update
     - sudo apt install postgresql postgresql-contrib
     - sudo -u postgres psql
     - \password postgres
     - \q to exit pqsl

## Step 2:
    Setup python modules, in the project directory run commands:
     - python3 -m venv .venv
     - source .venv/bin/activate
     - pip install -r requirements.txt

## Step 3:
    Setup credentials
    Create .env file and fill in the fields (check .env.example).
    If you have a default instance of postgres you can copy the contents of .env.example

## Step 4:
    Setup database
    run: python setup_database.py
    It will create the necessary tables and insert data.

## Step 5:
    Start the app
    run: streamlit run streamlit_app.py
