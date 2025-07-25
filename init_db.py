import sqlite3
from werkzeug.security import generate_password_hash
import os

def init_database():
    """Initialize the database with sample data"""
    # Create database connection
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    
    # Create users table if it doesn't exist
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT NOT NULL UNIQUE,
        password_hash TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # Check if users already exist
    cursor.execute("SELECT COUNT(*) FROM users")
    user_count = cursor.fetchone()[0]
    
    if user_count == 0:
        # Create sample users with hashed passwords
        sample_users = [
            {
                'name': 'John Doe',
                'email': 'john@example.com',
                'password': 'password123'
            },
            {
                'name': 'Jane Smith',
                'email': 'jane@example.com',
                'password': 'secret456'
            },
            {
                'name': 'Bob Johnson',
                'email': 'bob@example.com',
                'password': 'qwerty789'
            }
        ]
        
        for user_data in sample_users:
            password_hash = generate_password_hash(user_data['password'])
            cursor.execute(
                "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
                (user_data['name'], user_data['email'], password_hash)
            )
        
        conn.commit()
        print("Database initialized with sample data")
        print(f"Created {len(sample_users)} users:")
        for user in sample_users:
            print(f"  - {user['name']} ({user['email']})")
    else:
        print(f"Database already contains {user_count} users, skipping initialization")
    
    conn.close()

if __name__ == '__main__':
    init_database() 