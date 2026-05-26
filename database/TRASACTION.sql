

USE GRW;
GO

DROP PROCEDURE IF EXISTS sp_SellProduct;
GO

CREATE PROCEDURE sp_SellProduct
    @ItemID BIGINT,
    @QuantityToSell FLOAT,
    @SellingPrice FLOAT,
    @UserID INT = NULL -- Thêm UserID
AS
BEGIN
    SET NOCOUNT ON;

    DECLARE @CurrentStock FLOAT;
    DECLARE @CurrentSold FLOAT;
    DECLARE @OriginalPrice FLOAT;

    SELECT TOP 1 
        @CurrentStock = StockQuantity, 
        @CurrentSold = SoldQuantity,
        @OriginalPrice = OriginalPrice
    FROM Fact_Inventory_History 
    WHERE ItemID = @ItemID 
    ORDER BY Timestamp DESC;

    -- SECURITY VALIDATION
    IF (@QuantityToSell <= 0)
    BEGIN
        ;THROW 50004, N'Lỗi: Số lượng xuất bán phải > 0.', 1;
    END

    IF (@SellingPrice < 0)
    BEGIN
        ;THROW 50005, N'Lỗi: Giá bán không được là số âm.', 1;
    END

    BEGIN TRY
        BEGIN TRANSACTION;

        IF (@CurrentStock IS NULL OR @CurrentStock < @QuantityToSell)
        BEGIN
            ;THROW 50002, N'Kho không đủ hàng để xuất bán. Tồn kho hiện tại thấp hơn số lượng yêu cầu!', 1;
        END

        INSERT INTO Fact_Inventory_History (
            ItemID, UserID, Timestamp, Price, OriginalPrice, Discount, 
            StockQuantity, SoldQuantity, CommentCount, LikedCount
        )
        VALUES (
            @ItemID, 
            @UserID,
            GETDATE(), 
            @SellingPrice, 
            ISNULL(@OriginalPrice, @SellingPrice), 
            CASE WHEN @OriginalPrice > 0 THEN 1 - (@SellingPrice / @OriginalPrice) ELSE 0 END, 
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
