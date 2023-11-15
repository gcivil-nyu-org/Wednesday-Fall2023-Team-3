import os
import psycopg2
from psycopg2 import sql

# Replace these with your actual database connection details
db_params = {
    "dbname": "cheerup",
    "user": os.environ["DB_KEY"],
    "password": os.environ["DB_KEYP"],
    "host": "database-1.ceenqhnjmvnk.us-west-2.rds.amazonaws.com",
    "port": "5432",
}

# Establish a connection to the database
conn = psycopg2.connect(**db_params)
print(conn)
# Create a cursor object to execute SQL queries
cursor = conn.cursor()

# Example: Searching for data in a table
table_name = "locations"


# Construct the SQL query
query = sql.SQL("SELECT * FROM {};").format(sql.Identifier(table_name))

# Execute the query with the search value
cursor.execute(query)

# Fetch the results
results = cursor.fetchall()

# Print the results
for row in results:
    print(row)

# Close the cursor and connection
cursor.close()
conn.close()
