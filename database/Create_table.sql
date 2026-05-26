-- ==========================================================
-- SCRIPT KHỞI TẠO CƠ SỞ DỮ LIỆU GREENMIND AI (CHUẨN V2.0)
-- Đảm bảo Idempotent (chạy nhiều lần không lỗi)
-- Đã bao gồm Soft Delete (IsActive) và Audit Trail (UserID)
-- ==========================================================

-- 1. TẠO CƠ SỞ DỮ LIỆU CHÍNH (Nếu chưa có)
IF NOT EXISTS (SELECT * FROM sys.databases WHERE name = 'GRW')
BEGIN
    CREATE DATABASE GRW;
END
GO

USE GRW;
GO

-- 2. TẠO CÁC BẢNG (DIMENSIONS)
-- ==========================================================

-- Bảng Người Dùng
-- DEPRECATED: Bảng này KHÔNG được dùng cho authentication trong ứng dụng Web.
-- Chỉ dùng Django User model (auth_user) cho login.
-- Bảng này hiện giữ lại để duy trì tham chiếu khóa ngoại trong Fact_Inventory_History.
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'Dim_Users')
BEGIN
    CREATE TABLE Dim_Users (
        UserID INT IDENTITY(1,1) PRIMARY KEY,
        Username NVARCHAR(50) UNIQUE NOT NULL,
        PasswordHash NVARCHAR(255) NOT NULL,
        FullName NVARCHAR(100),
        Email NVARCHAR(100),
        PhoneNumber NVARCHAR(20),
        DateOfBirth DATE,
        Role NVARCHAR(20) DEFAULT 'Admin',
        CreatedAt DATETIME DEFAULT GETDATE()
    );
END
GO

-- Bảng Master Data Sản Phẩm
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'Dim_Products')
BEGIN
    CREATE TABLE Dim_Products (
        ItemID BIGINT PRIMARY KEY,
        ProductName NVARCHAR(255),
        Category NVARCHAR(100),
        Unit NVARCHAR(50) DEFAULT 'Cái',
        EmissionFactor FLOAT DEFAULT 0.85,
        SafetyStockLevel INT DEFAULT 0,
        ShelfRow INT DEFAULT 1,     
        ShelfColumn INT DEFAULT 1,  
        IsActive BIT DEFAULT 1,     -- Phục vụ Soft Delete (Fix #3)
        CreatedAt DATETIME DEFAULT GETDATE()
    );
END
GO

-- 3. TẠO CÁC BẢNG (FACT & LOGS)
-- ==========================================================

-- Bảng Lịch sử Tồn kho (Dữ liệu chuỗi thời gian cho AI & Audit)
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'Fact_Inventory_History')
BEGIN
    CREATE TABLE Fact_Inventory_History (
        HistoryID INT IDENTITY(1,1) PRIMARY KEY,
        ItemID BIGINT NOT NULL,
        UserID INT NULL,                         -- Phục vụ Audit Trail (Fix #4)
        Timestamp DATETIME NOT NULL,             
        Price FLOAT,                             
        OriginalPrice FLOAT,                     
        Discount FLOAT,                          
        StockQuantity FLOAT NOT NULL,            
        SoldQuantity INT,                        
        CommentCount INT,                        
        LikedCount INT,                          

        CONSTRAINT FK_Inventory_Product FOREIGN KEY (ItemID) 
            REFERENCES Dim_Products(ItemID),
        CONSTRAINT FK_Inventory_User FOREIGN KEY (UserID) 
            REFERENCES Dim_Users(UserID)
    );
END
GO

-- Bảng Lưu trữ Trích xuất Dự báo AI theo đợt
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'Fact_AI_Predictions')
BEGIN
    CREATE TABLE Fact_AI_Predictions (
        PredictionID INT IDENTITY(1, 1) PRIMARY KEY,
        ItemID BIGINT NOT NULL,
        PredictionDate DATE NOT NULL,
        ForecastedQuantity FLOAT NOT NULL,
        ModelUsed NVARCHAR(50),
        ConfidenceLevel FLOAT,
        CalculatedAt DATETIME DEFAULT GETDATE(),

        CONSTRAINT FK_Predictions_Product FOREIGN KEY (ItemID) 
            REFERENCES Dim_Products(ItemID)
    );
END
GO

-- Bảng Lưu trữ Log Tác động Môi trường (CO2)
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'Green_Impact_Logs')
BEGIN
    CREATE TABLE Green_Impact_Logs (
        LogID INT IDENTITY(1, 1) PRIMARY KEY,
        ItemID BIGINT NOT NULL,
        AnualCO2Saving FLOAT,
        TreesEquivalent FLOAT,
        ChampionModel NVARCHAR(50),
        CalculatedAt DATETIME DEFAULT GETDATE(),

        CONSTRAINT FK_GreenLog_Product FOREIGN KEY (ItemID) 
            REFERENCES Dim_Products(ItemID)
    );
END
GO

-- Bảng Lưu trữ Cảnh báo Vi phạm CO2/Tồn kho
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'Inventory_CO2_Warnings')
BEGIN
    CREATE TABLE Inventory_CO2_Warnings (
        WarningID INT IDENTITY(1, 1) PRIMARY KEY,
        ItemID BIGINT,
        WarningType NVARCHAR(50) DEFAULT 'Overstock',
        ExcessQuantity FLOAT NOT NULL,
        CO2Equivalent FLOAT NOT NULL,
        WarningTime DATETIME DEFAULT GETDATE(),

        CONSTRAINT FK_Warnings_Product FOREIGN KEY (ItemID) 
            REFERENCES Dim_Products(ItemID)
    );
END
GO

-- Bảng lưu log tình trạng Health Check hệ thống
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'System_Health_Log')
BEGIN
    CREATE TABLE System_Health_Log (
        LogID INT IDENTITY(1, 1) PRIMARY KEY,
        CheckTime DATETIME DEFAULT GETDATE(),
        Status NVARCHAR(20) NOT NULL,
        Details NVARCHAR(MAX),
        TriggeredBy NVARCHAR(100) DEFAULT 'system'
    );
END
GO

-- 4. TẠO CÁC INDEX TỐI ƯU HÓA TRUY VẤN

-- ==========================================================
IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'IX_Inventory_Timestamp' AND object_id = OBJECT_ID('Fact_Inventory_History'))
BEGIN
    CREATE INDEX IX_Inventory_Timestamp ON Fact_Inventory_History (ItemID, Timestamp);
END
GO

IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'IX_Predictions_Date'  AND object_id = OBJECT_ID('Fact_AI_Predictions'))
BEGIN
    CREATE INDEX IX_Predictions_Date ON Fact_AI_Predictions (PredictionDate);
END
GO

-- HOÀN TẤT --