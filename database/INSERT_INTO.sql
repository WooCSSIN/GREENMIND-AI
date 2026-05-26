

USE GRW;
GO

DROP PROCEDURE IF EXISTS sp_InsertDailyInventory;
GO

CREATE PROCEDURE sp_InsertDailyInventory
    @ItemID BIGINT,
    @Price FLOAT,
    @OriginalPrice FLOAT,
    @Discount FLOAT,
    @StockQuantity FLOAT,
    @SoldQuantity INT,
    @CommentCount INT,
    @LikedCount INT
AS
BEGIN

    SET NOCOUNT ON;
    BEGIN TRY
        BEGIN TRANSACTION t_InsertInventory;

        IF NOT EXISTS (SELECT 1 FROM Dim_Products WHERE ItemID = @ItemID)
        BEGIN

            PRINT N'CẢNH BÁO: SKU ' + CAST(@ItemID AS NVARCHAR) + N' là sản phẩm mới. Hệ thống sẽ tự tạo danh mục mặc định.';
            INSERT INTO Dim_Products (ItemID, ProductName, Category, ShelfRow, ShelfColumn)
            VALUES (@ItemID, N'Sản phẩm MỚI ' + CAST(@ItemID AS NVARCHAR), N'Sản phẩm mới nhập', 5, 12);
        END

        IF (@Discount < 0 OR @Discount > 1)
        BEGIN

            ;THROW 50001, N'LỖI NGHIỆP VỤ: Mức giảm giá (Discount) phải nằm trong khoảng từ 0.0 đến 1.0 (0% đến 100%).', 1;
        END

        INSERT INTO Fact_Inventory_History (
            ItemID, 
            Timestamp, 
            Price, 
            OriginalPrice, 
            Discount, 
            StockQuantity, 
            SoldQuantity, 
            CommentCount, 
            LikedCount
        )
        VALUES (
            @ItemID, 
            GETDATE(),    
            @Price, 
            @OriginalPrice, 
            @Discount, 
            @StockQuantity, 
            @SoldQuantity, 
            @CommentCount, 
            @LikedCount
        );

        COMMIT TRANSACTION t_InsertInventory;
        PRINT N'THÀNH CÔNG: Đã lưu bản ghi tồn kho cho SKU ' + CAST(@ItemID AS NVARCHAR) + N' vào cơ sở dữ liệu.';

    END TRY
    BEGIN CATCH

        IF @@TRANCOUNT > 0
            ROLLBACK TRANSACTION t_InsertInventory;

        DECLARE @ErrorMessage NVARCHAR(4000) = ERROR_MESSAGE();
        PRINT N'LỖI HỆ THỐNG: Transaction đã bị Rollback. Nguyên nhân: ' + @ErrorMessage;
    END CATCH
END;
GO

PRINT N'
EXEC sp_InsertDailyInventory 
    @ItemID = 3391609027, 
    @Price = 209000, 
    @OriginalPrice = 299000, 
    @Discount = 0.3, 
    @StockQuantity = 860, 
    @SoldQuantity = 2250, 
    @CommentCount = 770, 
    @LikedCount = 2242;
GO

PRINT N'
EXEC sp_InsertDailyInventory 
    @ItemID = 10753341705, 
    @Price = 150000, @OriginalPrice = 200000, 
    @Discount = 3.0,     
    @StockQuantity = 450, @SoldQuantity = 10, @CommentCount = 5, @LikedCount = 52;
GO

PRINT N'
EXEC sp_InsertDailyInventory 
    @ItemID = 9999999999, 
    @Price = 50000, @OriginalPrice = 50000, 
    @Discount = 0.0, 
    @StockQuantity = 100, @SoldQuantity = 0, @CommentCount = 0, @LikedCount = 0;
GO

SELECT TOP 3 * FROM Fact_Inventory_History ORDER BY Timestamp DESC;
SELECT * FROM Dim_Products WHERE ItemID = 9999999999;
