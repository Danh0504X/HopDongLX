import pyodbc

try:
    # Kết nối trực tiếp đến SQL Server
    conn = pyodbc.connect(
        'DRIVER={ODBC Driver 17 for SQL Server};'
        'SERVER=LEGION5-9FN5TV5\\SQLEXPRESS;'
        'DATABASE=DriveContract;'
        'Trusted_Connection=yes;'
    )
    
    cursor = conn.cursor()
    
    # Kiểm tra phiên bản SQL Server
    cursor.execute('SELECT @@VERSION')
    version = cursor.fetchone()[0]
    print(f"Connected to: {version}\n")
    
    # Lấy danh sách các bảng
    cursor.execute("""
        SELECT TABLE_NAME 
        FROM INFORMATION_SCHEMA.TABLES 
        WHERE TABLE_TYPE = 'BASE TABLE'
    """)
    
    print("Existing tables:")
    tables = cursor.fetchall()
    for table in tables:
        table_name = table[0]
        print(f"\n- {table_name}")
        
        # Lấy thông tin các cột
        cursor.execute(f"""
            SELECT COLUMN_NAME, DATA_TYPE, CHARACTER_MAXIMUM_LENGTH
            FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_NAME = '{table_name}'
        """)
        
        print("  Columns:")
        for col in cursor.fetchall():
            col_name, data_type, max_length = col
            type_info = f"{data_type}"
            if max_length:
                type_info += f"({max_length})"
            print(f"    - {col_name}: {type_info}")
            
    cursor.close()
    conn.close()
    
except Exception as e:
    print(f"Error: {str(e)}") 