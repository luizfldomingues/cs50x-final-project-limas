-- Clear existing data
DELETE FROM order_products;
DELETE FROM order_increments;
DELETE FROM order_payments;
DELETE FROM orders;
DELETE FROM products;
DELETE FROM product_types;

-- Reset autoincrement counters if using SQLite
DELETE FROM sqlite_sequence WHERE name IN ('orders', 'users');


-- Sample Product Types
INSERT INTO product_types (id, type_name) VALUES (1, 'Beverages');
INSERT INTO product_types (id, type_name) VALUES (2, 'Appetizers');
INSERT INTO product_types (id, type_name) VALUES (3, 'Main Courses');
INSERT INTO product_types (id, type_name) VALUES (4, 'Desserts');
INSERT INTO product_types (id, type_name) VALUES (5, 'Salads');
INSERT INTO product_types (id, type_name) VALUES (6, 'Soups');
INSERT INTO product_types (id, type_name) VALUES (7, 'Sandwiches');
INSERT INTO product_types (id, type_name) VALUES (8, 'Seafood');
INSERT INTO product_types (id, type_name) VALUES (9, 'Pasta');
INSERT INTO product_types (id, type_name) VALUES (10, 'Pizzas');
INSERT INTO product_types (id, type_name) VALUES (11, 'Steaks');
INSERT INTO product_types (id, type_name) VALUES (12, 'Side Dishes');

-- Sample Products

-- Beverages (Type 1)
INSERT INTO products (product_name, product_type_id, price) VALUES ('Coca-Cola', 1, 5);
INSERT INTO products (product_name, product_type_id, price) VALUES ('Pepsi', 1, 5);
INSERT INTO products (product_name, product_type_id, price) VALUES ('Sprite', 1, 5);
INSERT INTO products (product_name, product_type_id, price) VALUES ('Fanta', 1, 5);
INSERT INTO products (product_name, product_type_id, price) VALUES ('Iced Tea', 1, 6);
INSERT INTO products (product_name, product_type_id, price) VALUES ('Lemonade', 1, 6);
INSERT INTO products (product_name, product_type_id, price) VALUES ('Orange Juice', 1, 7);
INSERT INTO products (product_name, product_type_id, price) VALUES ('Apple Juice', 1, 7);
INSERT INTO products (product_name, product_type_id, price) VALUES ('Bottled Water', 1, 3);
INSERT INTO products (product_name, product_type_id, price) VALUES ('Sparkling Water', 1, 4);

-- Appetizers (Type 2)
INSERT INTO products (product_name, product_type_id, price) VALUES ('French Fries', 2, 10);
INSERT INTO products (product_name, product_type_id, price) VALUES ('Onion Rings', 2, 12);
INSERT INTO products (product_name, product_type_id, price) VALUES ('Nachos with Cheese', 2, 15);
INSERT INTO products (product_name, product_type_id, price) VALUES ('Chicken Wings', 2, 18);
INSERT INTO products (product_name, product_type_id, price) VALUES ('Mozzarella Sticks', 2, 14);
INSERT INTO products (product_name, product_type_id, price) VALUES ('Garlic Bread', 2, 8);
INSERT INTO products (product_name, product_type_id, price) VALUES ('Bruschetta', 2, 13);
INSERT INTO products (product_name, product_type_id, price) VALUES ('Spring Rolls', 2, 11);
INSERT INTO products (product_name, product_type_id, price) VALUES ('Quesadillas', 2, 16);
INSERT INTO products (product_name, product_type_id, price) VALUES ('Spinach Dip', 2, 14);

-- Main Courses (Type 3)
INSERT INTO products (product_name, product_type_id, price) VALUES ('Classic Hamburger', 3, 20);
INSERT INTO products (product_name, product_type_id, price) VALUES ('Cheeseburger', 3, 22);
INSERT INTO products (product_name, product_type_id, price) VALUES ('Bacon Burger', 3, 24);
INSERT INTO products (product_name, product_type_id, price) VALUES ('Grilled Chicken Sandwich', 3, 19);
INSERT INTO products (product_name, product_type_id, price) VALUES ('Fish and Chips', 3, 25);
INSERT INTO products (product_name, product_type_id, price) VALUES ('Roast Chicken', 3, 28);
INSERT INTO products (product_name, product_type_id, price) VALUES ('BBQ Ribs', 3, 30);

-- Desserts (Type 4)
INSERT INTO products (product_name, product_type_id, price) VALUES ('Chocolate Cake', 4, 10);
INSERT INTO products (product_name, product_type_id, price) VALUES ('Cheesecake', 4, 12);
INSERT INTO products (product_name, product_type_id, price) VALUES ('Ice Cream Sundae', 4, 8);
INSERT INTO products (product_name, product_type_id, price) VALUES ('Apple Pie', 4, 9);
INSERT INTO products (product_name, product_type_id, price) VALUES ('Brownie with Ice Cream', 4, 11);
INSERT INTO products (product_name, product_type_id, price) VALUES ('Pudding', 4, 6);
INSERT INTO products (product_name, product_type_id, price) VALUES ('Fruit Salad', 4, 7);

-- Salads (Type 5)
INSERT INTO products (product_name, product_type_id, price) VALUES ('Caesar Salad', 5, 15);
INSERT INTO products (product_name, product_type_id, price) VALUES ('Greek Salad', 5, 16);
INSERT INTO products (product_name, product_type_id, price) VALUES ('Garden Salad', 5, 12);
INSERT INTO products (product_name, product_type_id, price) VALUES ('Cobb Salad', 5, 18);
INSERT INTO products (product_name, product_type_id, price) VALUES ('Chicken Caesar Salad', 5, 19);

-- Soups (Type 6)
INSERT INTO products (product_name, product_type_id, price) VALUES ('Tomato Soup', 6, 9);
INSERT INTO products (product_name, product_type_id, price) VALUES ('Chicken Noodle Soup', 6, 10);
INSERT INTO products (product_name, product_type_id, price) VALUES ('French Onion Soup', 6, 12);
INSERT INTO products (product_name, product_type_id, price) VALUES ('Clam Chowder', 6, 14);
INSERT INTO products (product_name, product_type_id, price) VALUES ('Minestrone Soup', 6, 11);

-- Sandwiches (Type 7)
INSERT INTO products (product_name, product_type_id, price) VALUES ('Club Sandwich', 7, 18);
INSERT INTO products (product_name, product_type_id, price) VALUES ('BLT Sandwich', 7, 15);
INSERT INTO products (product_name, product_type_id, price) VALUES ('Tuna Melt', 7, 16);
INSERT INTO products (product_name, product_type_id, price) VALUES ('Roast Beef Sandwich', 7, 19);
INSERT INTO products (product_name, product_type_id, price) VALUES ('Veggie Sandwich', 7, 14);

-- Seafood (Type 8)
INSERT INTO products (product_name, product_type_id, price) VALUES ('Grilled Salmon', 8, 32);
INSERT INTO products (product_name, product_type_id, price) VALUES ('Shrimp Scampi', 8, 28);
INSERT INTO products (product_name, product_type_id, price) VALUES ('Lobster Tail', 8, 45);
INSERT INTO products (product_name, product_type_id, price) VALUES ('Crab Cakes', 8, 26);
INSERT INTO products (product_name, product_type_id, price) VALUES ('Fried Calamari', 8, 22);

-- Pasta (Type 9)
INSERT INTO products (product_name, product_type_id, price) VALUES ('Spaghetti Bolognese', 9, 22);
INSERT INTO products (product_name, product_type_id, price) VALUES ('Fettuccine Alfredo', 9, 20);
INSERT INTO products (product_name, product_type_id, price) VALUES ('Lasagna', 9, 24);
INSERT INTO products (product_name, product_type_id, price) VALUES ('Penne alla Vodka', 9, 23);
INSERT INTO products (product_name, product_type_id, price) VALUES ('Macaroni and Cheese', 9, 18);

-- Pizzas (Type 10)
INSERT INTO products (product_name, product_type_id, price) VALUES ('Margherita Pizza', 10, 25);
INSERT INTO products (product_name, product_type_id, price) VALUES ('Pepperoni Pizza', 10, 28);
INSERT INTO products (product_name, product_type_id, price) VALUES ('Hawaiian Pizza', 10, 29);
INSERT INTO products (product_name, product_type_id, price) VALUES ('BBQ Chicken Pizza', 10, 30);
INSERT INTO products (product_name, product_type_id, price) VALUES ('Veggie Pizza', 10, 26);

-- Steaks (Type 11)
INSERT INTO products (product_name, product_type_id, price) VALUES ('Filet Mignon', 11, 55);
INSERT INTO products (product_name, product_type_id, price) VALUES ('Ribeye Steak', 11, 48);
INSERT INTO products (product_name, product_type_id, price) VALUES ('New York Strip', 11, 45);
INSERT INTO products (product_name, product_type_id, price) VALUES ('Sirloin Steak', 11, 38);
INSERT INTO products (product_name, product_type_id, price) VALUES ('T-Bone Steak', 11, 52);

-- Side Dishes (Type 12)
INSERT INTO products (product_name, product_type_id, price) VALUES ('Mashed Potatoes', 12, 8);
INSERT INTO products (product_name, product_type_id, price) VALUES ('Steamed Vegetables', 12, 7);
INSERT INTO products (product_name, product_type_id, price) VALUES ('Baked Potato', 12, 9);
INSERT INTO products (product_name, product_type_id, price) VALUES ('Coleslaw', 12, 6);
INSERT INTO products (product_name, product_type_id, price) VALUES ('Rice Pilaf', 12, 7);
INSERT INTO products (product_name, product_type_id, price) VALUES ('Mac and Cheese Side', 12, 9);
INSERT INTO products (product_name, product_type_id, price) VALUES ('Side Salad', 12, 8);
INSERT INTO products (product_name, product_type_id, price) VALUES ('Corn on the Cob', 12, 7);
INSERT INTO products (product_name, product_type_id, price) VALUES ('Garlic Mashed Potatoes', 12, 9);
INSERT INTO products (product_name, product_type_id, price) VALUES ('Sweet Potato Fries', 12, 11);
INSERT INTO products (product_name, product_type_id, price) VALUES ('Sauteed Spinach', 12, 8);
INSERT INTO products (product_name, product_type_id, price) VALUES ('Grilled Asparagus', 12, 10);
INSERT INTO products (product_name, product_type_id, price) VALUES ('Creamed Corn', 12, 8);
INSERT INTO products (product_name, product_type_id, price) VALUES ('Potato Salad', 12, 7);
INSERT INTO products (product_name, product_type_id, price) VALUES ('Pasta Salad', 12, 8);