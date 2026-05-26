

USE GRW;
GO

IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'Inventory_CO2_Warnings')
BEGIN
    CREATE TABLE Inventory_CO2_Warnings (
        WarningID INT IDENTITY(1,1) PRIMARY KEY,
        HistoryID INT,
        ItemID BIGINT,
        ExcessQuantity FLOAT,        
        ExcessCO2_kg FLOAT,          
        WarningTime DATETIME DEFAULT GETDATE()
    );
END
GO

DROP TRIGGER IF EXISTS trg_CheckOverstockCO2;
GO

CREATE TRIGGER trg_CheckOverstockCO2
ON Fact_Inventory_History
AFTER INSERT
AS
BEGIN
    SET NOCOUNT ON;

    INSERT INTO Inventory_CO2_Warnings (HistoryID, ItemID, ExcessQuantity, ExcessCO2_kg)
    SELECT 
        i.HistoryID,
        i.ItemID,
        (i.StockQuantity - p.SafetyStockLevel) AS ExcessQuantity,
        ((i.StockQuantity - p.SafetyStockLevel) * p.EmissionFactor) AS ExcessCO2_kg
    FROM inserted i
    JOIN Dim_Products p ON i.ItemID = p.ItemID

    WHERE i.StockQuantity > p.SafetyStockLevel; 

    PRINT N'[TRIGGER SYSTEM] Đã kiểm tra tồn kho ngầm và ghi nhận cảnh báo CO2 (nếu có dư thừa).';
END;
GO
