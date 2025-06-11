# Title of a project
Creators, Date, Course

----
## Table of contents
- [Title of a project](#title-of-a-project)
  - [Table of contents](#table-of-contents)
  - [Concept of a project](#concept-of-a-project)
  - [Dataset](#dataset)
  - [Data structure](#data-structure)
  - [Architecture of a system](#architecture-of-a-system)
  - [Features of a system](#features-of-a-system)
    - [Filtering](#filtering)
    - [Diagrams:](#diagrams)
      - ["Measures Over Time"](#measures-over-time)
      - ["Measures by Country"](#measures-by-country)
      - ["Distribution of Policy Measures by Level"](#distribution-of-policy-measures-by-level)
      - ["Authority Breakdown and Map"](#authority-breakdown-and-map)
  - [How to use](#how-to-use)
    - [Step 1:](#step-1)
    - [Step 2:](#step-2)
    - [Step 3:](#step-3)
    - [Step 4:](#step-4)
    - [Step 5:](#step-5)
---
## Concept of a project
What is a reasoning, what are the features of a created system

## Dataset
Description of a dataset here (source, description of coluimns + what do they even mean)

## Data structure
(here should be added a graph, ie. from https://dbdiagram.io/)

## Architecture of a system
What technologies were used, what is flow of data


## Features of a system
///
### Filtering
screen + description + fact of ability to choose multiple options from criteria

### Diagrams:

#### "Measures Over Time"

#### "Measures by Country"

#### "Distribution of Policy Measures by Level"

#### "Authority Breakdown and Map"


## How to use

### Step 1: 
    Install Postgresql:
     - sudo apt update
     - sudo apt install postgresql postgresql-contrib
     - sudo -u postgres psql
     - \password postgres
     - \q to exit pqsl

### Step 2:
    Setup python modules, in the project directory run commands:
     - python3 -m venv .venv
     - source .venv/bin/activate
     - pip install -r requirements.txt

### Step 3:
    Setup credentials
    Create .env file and fill in the fields (check .env.example).
    If you have a default instance of postgres you can copy the contents of .env.example

### Step 4:
    Setup database
    run: python setup_database.py
    It will create the necessary tables and insert data.

### Step 5:
    Start the app
    run: streamlit run streamlit_app.py
