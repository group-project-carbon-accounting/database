Install postgresql
```
sudo sh -c 'echo "deb http://apt.postgresql.org/pub/repos/apt $(lsb_release -cs)-pgdg main" > /etc/apt/sources.list.d/pgdg.list'
wget --quiet -O - https://www.postgresql.org/media/keys/ACCC4CF8.asc | sudo apt-key add -
sudo apt-get update
sudo apt-get -y install postgresql
```
need to change user to postgres with ```sudo -iu postgres```
To transfer files from normal user to postgres user, can transfer to tmp and then to user
Run postgresql
Need to connect to database with ```\c dvdrental```
Install requirements.txt

<!-- need to ... libpq -->