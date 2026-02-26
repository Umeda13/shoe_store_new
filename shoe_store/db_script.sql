-- db_script.sql
-- Скрипт базы данных для ООО "Обувь"
-- 3 нормальная форма с ссылочной целостностью

-- Таблица пользователей
CREATE TABLE core_user (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    password VARCHAR(128) NOT NULL,
    last_login DATETIME NULL,
    is_superuser BOOLEAN NOT NULL,
    username VARCHAR(150) UNIQUE NOT NULL,
    first_name VARCHAR(150) NOT NULL,
    last_name VARCHAR(150) NOT NULL,
    email VARCHAR(254) NOT NULL,
    is_staff BOOLEAN NOT NULL,
    is_active BOOLEAN NOT NULL,
    date_joined DATETIME NOT NULL,
    role VARCHAR(20) NOT NULL,
    fio VARCHAR(200) NOT NULL
);

-- Таблица категорий (3НФ)
CREATE TABLE core_category (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(100) UNIQUE NOT NULL
);

-- Таблица производителей (3НФ)
CREATE TABLE core_manufacturer (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(100) UNIQUE NOT NULL
);

-- Таблица поставщиков (3НФ)
CREATE TABLE core_supplier (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(100) UNIQUE NOT NULL
);

-- Таблица пунктов выдачи
CREATE TABLE core_pickuppoint (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    address VARCHAR(255) UNIQUE NOT NULL
);

-- Таблица товаров
CREATE TABLE core_product (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    article VARCHAR(20) UNIQUE NOT NULL,
    name VARCHAR(200) NOT NULL,
    category_id INTEGER NOT NULL,
    description TEXT NOT NULL,
    manufacturer_id INTEGER NOT NULL,
    supplier_id INTEGER NOT NULL,
    price DECIMAL(10,2) NOT NULL,
    unit VARCHAR(20) NOT NULL,
    stock_quantity INTEGER NOT NULL,
    discount DECIMAL(5,2) NOT NULL,
    image VARCHAR(100) NULL,
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL,
    FOREIGN KEY (category_id) REFERENCES core_category(id),
    FOREIGN KEY (manufacturer_id) REFERENCES core_manufacturer(id),
    FOREIGN KEY (supplier_id) REFERENCES core_supplier(id)
);

-- Таблица заказов
CREATE TABLE core_order (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id INTEGER NOT NULL,
    quantity INTEGER NOT NULL,
    status VARCHAR(20) NOT NULL,
    delivery_address_id INTEGER NOT NULL,
    order_date DATE NOT NULL,
    delivery_date DATE NOT NULL,
    client_id INTEGER NULL,
    code VARCHAR(10) UNIQUE NOT NULL,
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL,
    FOREIGN KEY (product_id) REFERENCES core_product(id),
    FOREIGN KEY (delivery_address_id) REFERENCES core_pickuppoint(id),
    FOREIGN KEY (client_id) REFERENCES core_user(id)
);

-- Индексы для оптимизации поиска
CREATE INDEX idx_product_name ON core_product(name);
CREATE INDEX idx_product_article ON core_product(article);
CREATE INDEX idx_order_status ON core_order(status);
CREATE INDEX idx_order_date ON core_order(order_date);