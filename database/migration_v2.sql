

USE GRW;
GO

-- ── Fix #3: Soft Delete ──────────────────────────────────────
-- Thêm cột IsActive vào Dim_Products nếu chưa có
IF NOT EXISTS (
    SELECT 1 FROM sys.columns 
    WHERE object_id = OBJECT_ID('Dim_Products') AND name = 'IsActive'
)
BEGIN
    ALTER TABLE Dim_Products ADD IsActive BIT NOT NULL DEFAULT 1;
    PRINT N'[MIGRATION] Đã thêm cột IsActive vào Dim_Products.';
END
ELSE
    PRINT N'[MIGRATION] Cột IsActive đã tồn tại - bỏ qua.';
GO

-- Đảm bảo tất cả SKU cũ đều là Active
UPDATE Dim_Products SET IsActive = 1 WHERE IsActive IS NULL;
GO

-- ── Fix #4: UserID Audit ─────────────────────────────────────
-- Thêm cột UserID vào Fact_Inventory_History nếu chưa có
IF NOT EXISTS (
    SELECT 1 FROM sys.columns 
    WHERE object_id = OBJECT_ID('Fact_Inventory_History') AND name = 'UserID'
)
BEGIN
    ALTER TABLE Fact_Inventory_History ADD UserID INT NULL;
    PRINT N'[MIGRATION] Đã thêm cột UserID vào Fact_Inventory_History.';
END
ELSE
    PRINT N'[MIGRATION] Cột UserID đã tồn tại - bỏ qua.';
GO

-- ── Cập nhật Stored Procedure sp_SellProduct ─────────────────
-- Đảm bảo proc luôn ghi UserID từ session Django
DROP PROCEDURE IF EXISTS sp_SellProduct;
GO

CREATE PROCEDURE sp_SellProduct
    @ItemID BIGINT,
    @QuantityToSell FLOAT,
    @SellingPrice FLOAT,
    @UserID INT = NULL  -- NULL được phép nếu không có user context
AS
BEGIN
    SET NOCOUNT ON;

    DECLARE @CurrentStock FLOAT;
    DECLARE @CurrentSold  FLOAT;
    DECLARE @OriginalPrice FLOAT;

    -- Lấy snapshot tồn kho mới nhất
    SELECT TOP 1
        @CurrentStock  = StockQuantity,
        @CurrentSold   = SoldQuantity,
        @OriginalPrice = OriginalPrice
    FROM Fact_Inventory_History
    WHERE ItemID = @ItemID
    ORDER BY Timestamp DESC;

    BEGIN TRY
        BEGIN TRANSACTION;

        IF (@CurrentStock IS NULL OR @CurrentStock < @QuantityToSell)
        BEGIN
            ;THROW 50002,
                N'Kho không đủ hàng để xuất. Tồn kho hiện tại thấp hơn số lượng yêu cầu!',
                1;
        END

        INSERT INTO Fact_Inventory_History (
            ItemID, UserID, Timestamp, Price, OriginalPrice,
            Discount, StockQuantity, SoldQuantity, CommentCount, LikedCount
        )
        VALUES (
            @ItemID,
            @UserID,   -- ← Ghi UserID từ Django session (NULL nếu không có)
            GETDATE(),
            @SellingPrice,
            ISNULL(@OriginalPrice, @SellingPrice),
            CASE WHEN ISNULL(@OriginalPrice,0) > 0
                 THEN 1.0 - (@SellingPrice / @OriginalPrice)
                 ELSE 0.0 END,
            @CurrentStock - @QuantityToSell,
            ISNULL(@CurrentSold, 0) + @QuantityToSell,
            0, 0
        );

        COMMIT TRANSACTION;
    END TRY
    BEGIN CATCH
        IF @@TRANCOUNT > 0 ROLLBACK TRANSACTION;
        DECLARE @ErrMsg NVARCHAR(4000) = ERROR_MESSAGE();
        THROW 50003, @ErrMsg, 1;
    END CATCH
END;
GO

PRINT N'[MIGRATION] Migration v2.0 hoàn tất thành công!';
GO
