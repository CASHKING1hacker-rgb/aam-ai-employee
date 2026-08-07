import sqlite3

conn = sqlite3.connect("your_database_name.db")
c = conn.cursor()

c.execute("""
ALTER TABLE orders
ADD COLUMN payment_invoice TEXT
""")

conn.commit()
conn.close()

print("Column added")