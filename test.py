import mysql.connector

# Local Database Configuration
DB_CONFIG = {
    'host': 'localhost',        # Local MySQL server
    'user': 'root',             # Default MySQL username
    'password': 'Surya@123', # Replace with your MySQL root password
    'database': 'users'         # Database name (you will create this)
}

try:
    # Step 1: Establishing a connection to MySQL database
    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor()

    # Step 2: Create a new database (if it doesn't exist)
    cursor.execute("CREATE DATABASE IF NOT EXISTS users")
    print("Database 'users' created or already exists.")

    # Step 3: Use the database
    cursor.execute("USE users")

    # Step 4: Create a table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS user_details (
        id INT AUTO_INCREMENT PRIMARY KEY,
        username VARCHAR(100),
        email VARCHAR(100),
        phone VARCHAR(20),
        role VARCHAR(50)
    )
    """)
    print("Table 'user_details' created or already exists.")

    # Step 5: Insert data into the table
    cursor.execute("""
    INSERT INTO user_details (username, email, phone, role)
    VALUES (%s, %s, %s, %s)
    """, ("john_doe", "john@example.com", "1234567890", "actor"))
    
    cursor.execute("""
    INSERT INTO user_details (username, email, phone, role)
    VALUES (%s, %s, %s, %s)
    """, ("jane_doe", "jane@example.com", "9876543210", "writer"))

    # Commit the changes to the database
    conn.commit()
    print("Data inserted successfully.")

    # Step 6: Fetch and display the content from the table
    cursor.execute("SELECT * FROM user_details")
    rows = cursor.fetchall()

    print("\nUser Details in the 'user_details' Table:")
    for row in rows:
        print(f"ID: {row[0]}, Username: {row[1]}, Email: {row[2]}, Phone: {row[3]}, Role: {row[4]}")

except mysql.connector.Error as err:
    print(f"Error: {err}")
finally:
    # Closing the cursor and connection
    if cursor:
        cursor.close()
    if conn:
        conn.close()
