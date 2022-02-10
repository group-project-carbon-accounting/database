import sqlalchemy as db
database_url = "postgresql://postgres:postgres@localhost:5432/db"
engine = db.create_engine(database_url, echo=True, future=True)
metadata = db.MetaData()
entity = db.Table('entity', metadata, autoload=True, autoload_with=engine)
product = db.Table('product', metadata, autoload=True, autoload_with=engine)
company_product = db.Table('company_product', metadata,
                           autoload=True, autoload_with=engine)
# this is how you get the table out
e2 = metadata.tables['entity']

stmt = db.insert(e2).values(
    display_name="Aperson", carbon_offset=0, carbon_cost=0)
print(stmt)

with engine.begin() as conn:
    result = conn.execute(stmt)
    print(result.inserted_primary_key)

stmt2 = db.select(product.c.item_name, product.c.carbon_cost).where(product.c.carbon_cost >= 1000)
with engine.begin() as conn:
    for row in conn.execute(stmt2):
        print((row.item_name, row.carbon_cost))

stmt3 = db\
    .select(entity.c.display_name, product.c.item_name, company_product.c.carbon_cost)\
    .select_from(entity)\
    .join(company_product, entity.c.id == company_product.c.comp_id)\
    .join(product, company_product.c.prod_id == product.c.id)

with engine.begin() as conn:
    for row in conn.execute(stmt3):
        print(row)

# make subqueries like this, which act like temporary tables
stmt4a = db\
    .select(company_product.c.comp_id, db.func.count(company_product.c.comp_id).label("comp_counts"))\
    .group_by(company_product.c.comp_id)\
    .subquery()

# use subqueries like this
stmt4b = db\
    .select(company_product.c.carbon_cost, stmt4a.c.comp_counts)\
    .select_from(company_product)\
    .join(stmt4a, company_product.c.comp_id == stmt4a.c.comp_id)

with engine.begin() as conn:
    for row in conn.execute(stmt4b):
        print(row)



# connection = engine.connect()
# # Print the column names
# print(entity.columns.keys())
# # Print full table metadata
# print(repr(metadata.tables['entity']))
