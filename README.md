# Database
## Structure
Coming soon!
## Setup
1. Install postgresql
    - can check the website https://www.postgresql.org/ for instructions
    - example for ubuntu: ```
    sudo sh -c 'echo "deb http://apt.postgresql.org/pub/repos/apt $(lsb_release -cs)-pgdg main" > /etc/apt/sources.list.d/pgdg.list'
wget --quiet -O - https://www.postgresql.org/media/keys/ACCC4CF8.asc | sudo apt-key add -
sudo apt-get update
sudo apt-get -y install postgresql```
    - Change user to postgres with ```$ sudo -iu postgres```, then do ```$ psql``` for manual connect
    - (To transfer files from normal user to postgres user, can transfer to ```\tmp``` and then to user)
    - Create db with ```postgres=# create database db```
    - Connect to database with ```postgres=# \c db```
    - Copy and paste the stuff from ```initialise_postgresdb.sql``` into terminal
    - You can try out test queries with ```test_queries.sql```
2. Install ```requirements.txt```

<!-- need to ... libpq -->

## Run
```
$ source venv/bin/activate
$ python main.py
```