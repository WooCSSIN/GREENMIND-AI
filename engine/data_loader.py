import pandas as pd
import pyodbc
from sqlalchemy import create_engine
import time

SERVER = r"DESKTOP-65L3CQO\KMS"
DATABASE = "GRW"


def get_sql_engine():
    """Tạo kết nối đến SQL Server bằng SQLAlchemy"""

    drivers = [driver for driver in pyodbc.drivers()]

    driver_name = "SQL Server"
    for d in [
        "ODBC Driver 17 for SQL Server",
        "ODBC Driver 13 for SQL Server",
        "SQL Server Native Client 11.0",
    ]:
        if d in drivers:
            driver_name = d
            break

    print(f"Đang sử dụng Driver: {driver_name}")

    conn_str = (
        f"mssql+pyodbc://@{SERVER}/{DATABASE}"
        f"?driver={driver_name.replace(' ', '+')}"
        f"&Trusted_Connection=yes"
    )

    return create_engine(conn_str)


def load_data_from_csv():
    csv_path = r"D:\GREENMIND\data\processed\Price_Stock_History.csv"
    print(f"Đang đọc dữ liệu từ: {csv_path}...")
    df = pd.read_csv(csv_path)

    df["Timestamp"] = pd.to_datetime(df["time_str"])

    return df


def seed_database():
    try:
        engine = get_sql_engine()
        df = load_data_from_csv()

        print(f"\nBắt đầu nạp dữ liệu vào SQL Server (Tổng cộng {len(df)} dòng)...")
        start_time = time.time()

        print("1. Đang nạp bảng Dim_Products...")

        products_df = pd.DataFrame(
            {
                "ItemID": df["itemid"].unique(),
                "ProductName": [
                    f"Sản phẩm SKU {item}" for item in df["itemid"].unique()
                ],  # Tên giả định
                "Category": "Chưa phân loại",
                "Unit": "Cái",
                "EmissionFactor": 0.85,  # Tiêu chuẩn tính CO2
                "SafetyStockLevel": 100,
            }
        )

        try:
            products_df.to_sql(
                "Dim_Products", con=engine, if_exists="append", index=False
            )
            print(f"   -> Đã nạp thành công {len(products_df)} SKU vào Dim_Products.")
        except Exception as e:
            print(
                f"   -> Bỏ qua nạp Dim_Products (Có thể dữ liệu đã tồn tại). Lỗi: {str(e).split(']')[0]}"
            )

        print(
            "\n2. Đang nạp bảng Fact_Inventory_History (Việc này có thể mất vài phút)..."
        )

        fact_df = df.rename(
            columns={
                "itemid": "ItemID",
                "price": "Price",
                "original_price": "OriginalPrice",
                "discount": "Discount",
                "stock": "StockQuantity",
                "sold": "SoldQuantity",
                "cmt_count": "CommentCount",
                "liked_count": "LikedCount",
            }
        )

        cols_to_keep = [
            "ItemID",
            "Timestamp",
            "Price",
            "OriginalPrice",
            "Discount",
            "StockQuantity",
            "SoldQuantity",
            "CommentCount",
            "LikedCount",
        ]
        fact_df = fact_df[cols_to_keep]

        fact_df.to_sql(
            "Fact_Inventory_History",
            con=engine,
            if_exists="append",
            index=False,
            chunksize=1000,
        )

        end_time = time.time()
        print(f"\n✅ HOÀN TẤT! Đã nạp thành công {len(fact_df)} lịch sử kho.")
        print(f"⏱️ Thời gian thực thi: {end_time - start_time:.2f} giây")

    except Exception as e:
        print(f"\n❌ LỖI KẾT NỐI: {str(e)}")
        print(
            "Gợi ý: Hãy đảm bảo bạn đã mở SQL Server và tên Server/Database là chính xác."
        )


if __name__ == "__main__":
    seed_database()
