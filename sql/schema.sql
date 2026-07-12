-- ArcaneBazaar Database Schema
-- The Grand Archive of Magical Commerce

CREATE DATABASE IF NOT EXISTS arcane_bazaar
    DEFAULT CHARACTER SET utf8mb4
    DEFAULT COLLATE utf8mb4_unicode_ci;

USE arcane_bazaar;

-- Mystical Phenomena Forecasts (realm magic conditions)
CREATE TABLE IF NOT EXISTS mystical_phenomena (
    id INT AUTO_INCREMENT PRIMARY KEY,
    realm VARCHAR(64) NOT NULL COMMENT 'Realm name',
    fx_date DATE NOT NULL COMMENT 'Forecast date',
    mana_level DECIMAL(4,1) NOT NULL COMMENT 'Mana concentration (0-10)',
    phenomenon_type VARCHAR(64) NOT NULL COMMENT 'Type of phenomenon',
    danger_rating TINYINT NOT NULL DEFAULT 1 COMMENT 'Danger scale 1-5',
    magic_surge_chance DECIMAL(4,1) NOT NULL DEFAULT 0 COMMENT 'Magic surge probability (%)',
    temp_high INT NOT NULL COMMENT 'Ethereal temperature high',
    temp_low INT NOT NULL COMMENT 'Ethereal temperature low',
    description TEXT COMMENT 'Phenomenon description',
    update_time DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uk_realm_date (realm, fx_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Magical Item Inventory (the grand bazaar catalog)
CREATE TABLE IF NOT EXISTS magical_items (
    id INT AUTO_INCREMENT PRIMARY KEY,
    item_name VARCHAR(128) NOT NULL COMMENT 'Item name',
    category VARCHAR(32) NOT NULL COMMENT 'potion / scroll / artifact / reagent / weapon / familiar',
    rarity VARCHAR(16) NOT NULL COMMENT 'Common / Uncommon / Rare / Epic / Legendary',
    origin_realm VARCHAR(64) NOT NULL COMMENT 'Realm of origin',
    seller VARCHAR(64) NOT NULL COMMENT 'Shop or merchant name',
    stock INT NOT NULL DEFAULT 0 COMMENT 'Available quantity',
    price_mana DECIMAL(10,0) NOT NULL COMMENT 'Price in mana crystals',
    description TEXT COMMENT 'Item flavor text',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uk_item_seller (item_name, seller)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
