import sqlite3
# from datetime import datetime

def init_db(db_name):
    """
    Initializes the SQLite database for the library system.

    This function creates three tables if they do not already exist:
    - `books`: Stores information about books in the library.
    - `borrowers`: Stores information about borrowers.
    - `borrowed_books`: Tracks which books are borrowed, by whom, and when.

    The database file is named in db_name.
    """
    # Connect to the SQLite database (creates the file if it doesn't exist)
    conn = sqlite3.connect(db_name)
    c = conn.cursor()
    
    # Create the `books` table to store book details
    c.execute('''
        CREATE TABLE IF NOT EXISTS books (
            id INTEGER PRIMARY KEY,  -- Unique identifier for each book
            title TEXT NOT NULL,     -- Title of the book (required)
            author TEXT NOT NULL,    -- Author of the book (required)
            is_borrowed INTEGER DEFAULT 0  -- Borrowed status (0 = not borrowed, 1 = borrowed)
        )
    ''')
    
    # Create the `borrowers` table to store borrower details
    c.execute('''
        CREATE TABLE IF NOT EXISTS borrowers (
            id INTEGER PRIMARY KEY,  -- Unique identifier for each borrower
            name TEXT NOT NULL,      -- Name of the borrower (required)
            email TEXT UNIQUE NOT NULL  -- Email of the borrower (must be unique and required)
        )
    ''')
    
    # Create the `borrowed_books` table to track borrowed books
    c.execute('''
        CREATE TABLE IF NOT EXISTS borrowed_books (
            id INTEGER PRIMARY KEY,  -- Unique identifier for each borrowing record
            book_id INTEGER,         -- ID of the borrowed book (foreign key to `books`)
            borrower_id INTEGER,     -- ID of the borrower (foreign key to `borrowers`)
            borrow_date TEXT,        -- Date when the book was borrowed
            FOREIGN KEY (book_id) REFERENCES books (id),  -- Enforce relationship with `books`
            FOREIGN KEY (borrower_id) REFERENCES borrowers (id)  -- Enforce relationship with `borrowers`
        )
    ''')
    
    # Commit the changes and close the connection
    conn.commit()
    conn.close()



