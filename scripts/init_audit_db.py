
import os
import sys
import pandas as pd
from sqlalchemy import text

# Add engine to path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(BASE_DIR, 'engine'))

from greenmind_engine import GreenMindEngine

def init_db():
    print("Connecting to SQL Server...")
    engine_ai = GreenMindEngine()
    sql_engine = engine_ai.get_sql_engine()
    
    table_sql = """
    IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[Admin_Action_Logs]') AND type in (N'U'))
    BEGIN
        CREATE TABLE [Admin_Action_Logs] (
            [LogID] INT PRIMARY KEY IDENTITY(1,1),
            [UserID] INT,
            [Action] NVARCHAR(100),
            [TableName] NVARCHAR(100),
            [RecordID] NVARCHAR(100),
            [OldValue] NVARCHAR(MAX),
            [NewValue] NVARCHAR(MAX),
            [IPAddress] NVARCHAR(50),
            [Timestamp] DATETIME DEFAULT GETDATE()
        );
        PRINT 'Table [Admin_Action_Logs] created successfully.';
    END
    ELSE
    BEGIN
        PRINT 'Table [Admin_Action_Logs] already exists.';
    END
    """
    
    try:
        with sql_engine.begin() as conn:
            conn.execute(text(table_sql))
        print("✅ Database operation completed.")
    except Exception as e:
        print(f"❌ Error during DB init: {e}")

if __name__ == "__main__":
    init_db()
