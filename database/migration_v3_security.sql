
USE GRW;
GO

-- 1. Thêm CHECK constraint cho Dim_Products
IF NOT EXISTS (SELECT * FROM sys.check_constraints WHERE name = 'CK_Product_SafetyStock')
BEGIN
    ALTER TABLE Dim_Products ADD CONSTRAINT CK_Product_SafetyStock CHECK (SafetyStockLevel >= 0);
END
GO

IF NOT EXISTS (SELECT * FROM sys.check_constraints WHERE name = 'CK_Product_Emission')
BEGIN
    ALTER TABLE Dim_Products ADD CONSTRAINT CK_Product_Emission CHECK (EmissionFactor >= 0);
END
GO

-- 2. Thêm CHECK constraint cho Fact_Inventory_History
IF NOT EXISTS (SELECT * FROM sys.check_constraints WHERE name = 'CK_History_Stock')
BEGIN
    ALTER TABLE Fact_Inventory_History ADD CONSTRAINT CK_History_Stock CHECK (StockQuantity >= 0);
END
GO

IF NOT EXISTS (SELECT * FROM sys.check_constraints WHERE name = 'CK_History_Price')
BEGIN
    ALTER TABLE Fact_Inventory_History ADD CONSTRAINT CK_History_Price CHECK (Price >= 0);
END
GO

IF NOT EXISTS (SELECT * FROM sys.check_constraints WHERE name = 'CK_History_Sold')
BEGIN
    ALTER TABLE Fact_Inventory_History ADD CONSTRAINT CK_History_Sold CHECK (SoldQuantity >= 0);
END
GO

-- 3. Thêm CHECK constraint cho Fact_AI_Predictions
IF NOT EXISTS (SELECT * FROM sys.check_constraints WHERE name = 'CK_Prediction_Qty')
BEGIN
    ALTER TABLE Fact_AI_Predictions ADD CONSTRAINT CK_Prediction_Qty CHECK (ForecastedQuantity >= 0);
END
GO

-- 4. Tạo bảng Audit Trail: Admin_Action_Logs
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'Admin_Action_Logs')
BEGIN
    CREATE TABLE Admin_Action_Logs (
        ActionID INT IDENTITY(1, 1) PRIMARY KEY,
        UserID INT NULL,
        Action NVARCHAR(100) NOT NULL,
        TableName NVARCHAR(50),
        RecordID NVARCHAR(50),
        OldValue NVARCHAR(MAX),
        NewValue NVARCHAR(MAX),
        Timestamp DATETIME DEFAULT GETDATE(),
        IPAddress NVARCHAR(50)
    );
END
GO

PRINT 'Database security migration completed successfully.';
