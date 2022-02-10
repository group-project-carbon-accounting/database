-- displays the companies that have special product information
select
    entity.display_name,
    product.item_name
from
    entity
    join company_product on entity.id = company_product.comp_id
    join product on product.id = company_product.prod_id;

-- displays purchases (without linking to purchase information)
select
    e1.display_name,
    e2.display_name,
    p.price
from
    entity as e1
    join purchase as p on e1.id = p.buyr_id
    join entity as e2 on e2.id = p.selr_id;

-- displays purchases (with linking to purchase information)
select
    buyer.display_name as buyer,
    seller.display_name as shop,
    purchase.price as price,
    manufacturer.display_name as producer,
    product.item_name as product
from
    entity as buyer
    join purchase on buyer.id = purchase.buyr_id
    join entity as seller on seller.id = purchase.selr_id
    left join products_purchased as pp on purchase.id = pp.prch_id
    left join entity as manufacturer on pp.comp_id = manufacturer.id
    left join product on product.id = pp.prod_id;