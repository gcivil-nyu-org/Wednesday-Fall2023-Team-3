import sqlite3
import csv

conn = sqlite3.connect("db.sqlite3")
cursor = conn.cursor()

cursor.execute("SELECT * FROM location_location;")
data = cursor.fetchall()

# Specify 'utf-8' encoding when writing to the CSV file
with open("exported_data.csv", "w", newline="", encoding="utf-8") as csv_file:
    csv_writer = csv.writer(csv_file)
    csv_writer.writerows(data)

conn.close()
