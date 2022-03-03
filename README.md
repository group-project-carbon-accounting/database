# Database
## Structure
The database module is intended to be a thin wrapper around the postgresql database. Apart from accessing data, it implements 2 additional functions:
- input sanitisation to protect the database from being modified wrongly
    - not implemented due to time constraint
- convenience methods that simplify database queries

The database comprises 5 tables, namely:
- entity
    - (id, display_name, carbon_offset, carbon_cost)
- product 
    - (id, item_name, carbon_cost)
- company_product
    - (comp_id, prod_id, carbon_cost)
- purchase
    - (id, buyr_id, selr_id, price, carbon_cost)
- products_purchased
    - (prch_id, comp_id, prod_id)

These are derived from the entity-relationship schema. 

```entity``` represents end-users or companies, and ```product``` represents products and their carbon costs. 

If we have more information about the carbon cost of a product sold by a company, then there is a relationship between ```entity``` and ```product```, and we store this carbon cost in ```company_product```. 

A ```purchase``` is a relation between 2 ```entities```. An item in this relation can also involve multiple products that are purchased, each of which could have (company, product) information. We store this in ```products_purchased```.
### Handlers
There should be get, insert, update, and delete handlers for different tables. All of the endpoints are documented on https://documenter.getpostman.com/view/19468275/UVktptPf#46caaa71-8274-4595-9c41-27bc2327a7ff. 

As a quick overview from the server's perspective, endpoints should be called to get information, calculations can be done in the server, and then a final call to update the database.

- For example, to calculate a better carbon cost for a purchase, the server would query ```GET \purchase\get\prch_id``` to get the purchase details. 
- The server might also want to query ```GET \product\get\prod_id``` if the purchase includes information about the products bought. 
- In the last step, the server calculates a better carbon cost, and calls ```POST \purchase\update``` with the new carbon cost.

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
2. Setup database
    - Create db with ```postgres=# create database db```
    - Connect to database with ```postgres=# \c db```
    - Copy and paste the stuff from ```test/integration/fixtures/initialise_postgresdb.sql``` into terminal
    - You can try out test queries with ```setup/test_queries.sql```
3. Install ```requirements.txt```

<!-- need to ... libpq -->

## Run
```
$ python main.py
```

## Test
A suite of integration tests were written to test the correctness of the database wrapper endpoints. In general, each table in the database has get, insert, and update endpoints, so the tests follow the following pattern:
- get
    - valid row id returns the contents of that row
    - invalid row id returns a HTTP response with a 4xx error code
- insert
    - valid row input updates the database table correctly
- update
    - valid row id updates the contents of that row
    - invalid row id returns a HTTP response with a 4xx error code
### Instructions for Running
1. Create a ```testdb``` in postgres
    - It will be automatically populated with test data in the fixtures folder
2. Run ```python -m test```
