-- Tạo database mới nếu chưa có
CREATE DATABASE IF NOT EXISTS vnstock_data DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

USE vnstock_data;

-- Tạo bảng lưu trữ dữ liệu nến cuối ngày (EOD)
CREATE TABLE IF NOT EXISTS daily_ohlcv (
    id INT AUTO_INCREMENT PRIMARY KEY,
    symbol VARCHAR(50) NOT NULL,
    date DATE NOT NULL,
    open FLOAT NOT NULL DEFAULT 0.0,
    high FLOAT NOT NULL DEFAULT 0.0,
    low FLOAT NOT NULL DEFAULT 0.0,
    close FLOAT NOT NULL DEFAULT 0.0,
    volume INT NOT NULL DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uq_daily_ohlcv_symbol_date (symbol, date),
    INDEX idx_symbol (symbol),
    INDEX idx_date (date)
);

-- Cache overview doanh nghiệp (dữ liệu cơ bản + định giá chuẩn hóa)
CREATE TABLE IF NOT EXISTS company_overview_cache (
    symbol VARCHAR(50) PRIMARY KEY,
    payload_json LONGTEXT NOT NULL,
    source VARCHAR(64) NOT NULL DEFAULT 'vnstock',
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_company_overview_cache_updated_at (updated_at)
);

-- Cache báo cáo tài chính theo loại report
CREATE TABLE IF NOT EXISTS financial_report_cache (
    id INT AUTO_INCREMENT PRIMARY KEY,
    symbol VARCHAR(50) NOT NULL,
    report_type VARCHAR(20) NOT NULL,
    row_count INT NOT NULL DEFAULT 0,
    payload_json LONGTEXT NOT NULL,
    source VARCHAR(64) NOT NULL DEFAULT 'vnstock',
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uq_financial_report_cache_symbol_type (symbol, report_type),
    INDEX idx_financial_report_cache_symbol (symbol),
    INDEX idx_financial_report_cache_updated_at (updated_at)
);

-- Cache dữ liệu technical theo tham số truy vấn
CREATE TABLE IF NOT EXISTS technical_cache (
    id INT AUTO_INCREMENT PRIMARY KEY,
    symbol VARCHAR(50) NOT NULL,
    start_date DATE NULL,
    end_date DATE NULL,
    limit_value INT NOT NULL DEFAULT 365,
    history_count INT NOT NULL DEFAULT 0,
    history_last_time VARCHAR(32) NULL,
    payload_json LONGTEXT NOT NULL,
    source VARCHAR(64) NOT NULL DEFAULT 'mysql',
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uq_technical_cache_signature (symbol, start_date, end_date, limit_value),
    INDEX idx_technical_cache_symbol (symbol),
    INDEX idx_technical_cache_updated_at (updated_at)
);

-- Cache tin tức theo mã
CREATE TABLE IF NOT EXISTS news_cache (
    symbol VARCHAR(50) PRIMARY KEY,
    item_count INT NOT NULL DEFAULT 0,
    payload_json LONGTEXT NOT NULL,
    source VARCHAR(64) NOT NULL DEFAULT 'vnstock',
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_news_cache_updated_at (updated_at)
);

-- Cache sự kiện doanh nghiệp theo mã
CREATE TABLE IF NOT EXISTS events_cache (
    symbol VARCHAR(50) PRIMARY KEY,
    item_count INT NOT NULL DEFAULT 0,
    payload_json LONGTEXT NOT NULL,
    source VARCHAR(64) NOT NULL DEFAULT 'vnstock',
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_events_cache_updated_at (updated_at)
);

-- Tài khoản người dùng cho chức năng đăng ký / đăng nhập
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    first_name VARCHAR(120) NOT NULL,
    last_name VARCHAR(120) NOT NULL,
    email VARCHAR(255) NOT NULL,
    avatar_data LONGTEXT NULL,
    password_hash VARCHAR(255) NOT NULL,
    password_salt VARCHAR(255) NOT NULL,
    is_active TINYINT(1) NOT NULL DEFAULT 1,
    last_login_at DATETIME NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uq_users_email (email),
    INDEX idx_users_created_at (created_at)
);
