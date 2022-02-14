DROP TABLE IF EXISTS entity CASCADE;
DROP TABLE IF EXISTS product CASCADE;
DROP TABLE IF EXISTS company_product CASCADE;
DROP TABLE IF EXISTS purchase CASCADE;
DROP TABLE IF EXISTS products_purchased CASCADE;

CREATE TABLE IF NOT EXISTS entity(
    id SERIAL PRIMARY KEY,
    display_name VARCHAR(255) NOT NULL,
    -- grams
    carbon_offset INT NOT NULL,
    carbon_cost INT NOT NULL -- g / dollar
);

CREATE TABLE IF NOT EXISTS product(
    id SERIAL PRIMARY KEY,
    item_name VARCHAR(255) NOT NULL,
    carbon_cost INT NOT NULL -- g / item
);

CREATE TABLE IF NOT EXISTS company_product(
    comp_id INT NOT NULL,
    prod_id INT NOT NULL,
    carbon_cost INT NOT NULL,
    CONSTRAINT fk_comp FOREIGN KEY(comp_id) REFERENCES entity(id),
    CONSTRAINT fk_prod FOREIGN KEY(prod_id) REFERENCES product(id)
);

CREATE TABLE IF NOT EXISTS purchase(
    id SERIAL PRIMARY KEY,
    buyr_id INT NOT NULL,
    selr_id INT NOT NULL,
    -- cents
    price INT NOT NULL,
    carbon_cost INT NOT NULL,
    CONSTRAINT fk_buyr FOREIGN KEY(buyr_id) REFERENCES entity(id),
    CONSTRAINT fk_selr FOREIGN KEY(selr_id) REFERENCES entity(id)
);

CREATE TABLE IF NOT EXISTS products_purchased(
    prch_id INT NOT NULL,
    comp_id INT,
    prod_id INT,
    CONSTRAINT fk_prch FOREIGN KEY(prch_id) REFERENCES purchase(id),
    CONSTRAINT fk_comp FOREIGN KEY(comp_id) REFERENCES entity(id),
    CONSTRAINT fk_prod FOREIGN KEY(prod_id) REFERENCES product(id)
);

INSERT INTO
    entity(display_name, carbon_offset, carbon_cost)
VALUES
    -- people
    ('Albert', 0, 0),
    ('Ben', 0, 0),
    ('Carrie', 0, 0),
    ('Dan', 0, 0),
    ('Elania', 0, 0),
    -- companies
    ('Sainsburrows', 0, 1),
    ('Waiteroze', 0, 2),
    ('Curryies', 0, 3),
    ('Bangreat', 0, 4),
    ('Uniglo', 0, 5),
    ('Samsong', 0, 10),
    ('Lenova', 0, 10);

INSERT INTO
    product(item_name, carbon_cost)
VALUES
    -- food
    ('beef', 3300),
    ('cheese', 1225),
    ('pork', 850),
    ('chicken', 630),
    ('milk', 350),
    -- digital electronics
    ('laptop', 152000),
    ('smartphone', 55000),
    ('speaker', 21300),
    -- clothing
    ('tshirt', 1300),
    ('dress', 500),
    ('suit', 5000);

INSERT INTO
    company_product(comp_id, prod_id, carbon_cost)
VALUES
    -- sainsburrows food
    (6, 1, 2300),
    (6, 3, 700),
    (6, 4, 500),
    -- lenova laptop
    (12, 6, 130000),
    -- samsong smartphone
    (11, 7, 60000),
    -- uniglo dress
    (10, 10, 400);

INSERT INTO
    purchase(buyr_id, selr_id, price, carbon_cost)
VALUES
    -- albert buys items from sainsburrows
    (1, 6, 1200, 0),
    -- ben buys laptop from curryies
    (2, 8, 200000, 0),
    -- carrie buys dress from uniglo
    (3, 10, 1000, 0);

INSERT INTO
    products_purchased(prch_id, comp_id, prod_id)
VALUES
    -- albert's sainsburrows purchase
    -- beef
    (1, 6, 1),
    -- cheese
    (1, 6, 2),
    -- ben's laptop purchase
    -- lenovo laptop
    (2, 12, 6);