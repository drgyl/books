"""
main.py
=======

This module implements the HTTP server for the Library Management System. It handles
HTTP GET and POST requests to manage books, borrowers, and borrowed books. The server
interacts with an SQLite database to perform CRUD operations and enforce data integrity.

Features:
---------
- Handles the following HTTP routes:
  1. `/books`:
     - GET: Lists all books in the library.
     - POST: Adds a new book to the library.
  2. `/borrowers`:
     - GET: Retrieves details of a specific borrower.
     - POST: Creates a new borrower.
  3. `/borrowed-books`:
     - GET: Retrieves books borrowed by a specific borrower.
     - POST: Records a book borrowing event.

- Validates request bodies and query parameters.
- Returns appropriate HTTP status codes and error messages for invalid requests.
- Enforces foreign key constraints and data integrity using SQLite.

Functions:
----------
- `run_server(port=8888)`: Starts the HTTP server on the specified port.
- `LibraryHandler`: Handles HTTP requests and routes them to the appropriate methods.

Dependencies:
-------------
- http.server: For creating the HTTP server.
- sqlite3: For database operations.
- json: For parsing and generating JSON responses.
- urllib.parse: For parsing query parameters.

Usage:
------
Run this module directly to start the server:
>>> python main.py

Example:
--------
1. Start the server:
   >>> python main.py
   Starting server on port 8888...

2. Use an HTTP client (e.g., `curl` or Postman) to interact with the server:

   - List all books:
     >>> curl -X GET http://localhost:8888/books

   - Add a new book:
     >>> curl -X POST http://localhost:8888/books -H "Content-Type: application/json" -d '{"title": "Python Basics", "author": "John Doe"}'

   - List all borrowers:
     >>> curl -X GET http://localhost:8888/borrowers

   - Add a new borrower:
     >>> curl -X POST http://localhost:8888/borrowers -H "Content-Type: application/json" -d '{"name": "Jane Smith", "email": "jane.smith@example.com"}'

   - Get details of a specific borrower:
     >>> curl -X GET http://localhost:8888/borrowers/1

   - List books borrowed by a specific borrower:
     >>> curl -X GET http://localhost:8888/borrowed-books/1

   - Record a book borrowing event:
     >>> curl -X POST http://localhost:8888/borrowed-books -H "Content-Type: application/json" -d '{"borrower_id": 1, "book_id": 2}'
"""

from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import sqlite3
from urllib.parse import parse_qs, urlparse

DATABASE_NAME = 'library.db'
DEFAULT_PORT = 8888

BOOKS_PATH = "/books"
BORROWERS_PATH = "/borrowers"
BORROWED_PATH = "/borrowed-books"

INVALID_JSON_ERROR = "Invalid JSON format"
PATH_NOT_FOUND_ERROR = "Path not found"
MAX_CONTENT_LENGTH = 1024 * 1024  # 1 MB

class LibraryHandler(BaseHTTPRequestHandler):
    """
    HTTP request handler for the library system.

    This class handles GET and POST requests to manage books, borrowers, and borrowed books.
    It interacts with the SQLite database to perform CRUD operations.
    """

    def send_json_response(self, status_code, data):
        self.send_response(status_code)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())

    def do_GET(self):
        """
        Handles HTTP GET requests.

        Routes:
        - `/books`: Lists all books in the library.
        - `/borrower/<id>`: Retrieves details of a specific borrower.
        - `/borrowed-books/<id>`: Retrieves books borrowed by a specific borrower.
        """
        parsed_path = urlparse(self.path)
        path = parsed_path.path
        
        if path == BOOKS_PATH:
            self.handle_list_books()
        elif path.startswith(BORROWERS_PATH):
            borrower_id = path.split('/')[-1]
            if not borrower_id.isdigit():
                self.send_error(400, "Invalid borrower ID format")
            else:          
                self.handle_get_borrower(borrower_id)
        elif path.startswith(BORROWED_PATH):
            borrower_id = path.split('/')[-1]
            if not borrower_id.isdigit():
                self.send_error(400, "Invalid borrower ID format")
            else:          
                self.handle_borrowed_books(borrower_id)
        else:
            self.send_error(400, PATH_NOT_FOUND_ERROR)

    def do_POST(self):
        """
        Handles HTTP POST requests.

        Routes:
        - `/books`: Adds a new book to the library.
        - `/borrowers`: Creates a new borrower.
        - `/borrow`: Records a book borrowing event.
        """
        try:
            # print(f'POST request processing {self.headers}...')
            content_length = int(self.headers.get('Content-Length', 0))  # Get the length of the request body
            # print(f'content length = {content_length}...')
            if content_length <= 2:
                raise ValueError(INVALID_JSON_ERROR)
            elif content_length > MAX_CONTENT_LENGTH:
                self.send_error(413, "Request body too large")
                return
            post_data = self.rfile.read(content_length)  # Read the request body
            # print(f'post data = {post_data}, len={len(post_data)}...')
            # print(f'post data decode {post_data.decode('utf-8')}...')
            if not post_data:  # Check if the body is empty
                raise ValueError(INVALID_JSON_ERROR)

            body = json.loads(post_data.decode('utf-8'))  # Parse the JSON body
            # print(f'body = {body}')
            if not isinstance(body, dict):  # Ensure the parsed body is a dictionary
                raise ValueError(INVALID_JSON_ERROR)
        except (ValueError, json.JSONDecodeError):
            self.send_error(400, INVALID_JSON_ERROR )
            return
    
        if self.path == BOOKS_PATH:
            # if all(key in body for key in ['title', 'author']):
            if body.get('title') and body.get('author'):
                self.handle_add_book(body)
            elif not body.get('title') and body.get('author'):
                self.send_error(400, "Invalid request body, missing Title")
            elif not body.get('author') and body.get('title'):
                self.send_error(400, "Invalid request body, missing Author")                
            else:
                self.send_error(400, "Invalid request body, no valid data provided")                
            
        elif self.path == BORROWERS_PATH:
            if body.get('name') and body.get('email'):
                self.handle_create_borrower(body)
            elif not body.get('name') and body.get('email'):
                self.send_error(400, "Invalid request body, missing Name")
            elif not body.get('email') and body.get('name'):
                self.send_error(400, "Invalid request body, missing Email")                
            else:
                self.send_error(400, "Invalid request body, no valid data provided")                

        elif self.path == BORROWED_PATH:
            if body.get('borrower_id') and body.get('book_id'):
                self.handle_borrow_book(body)
            elif not body.get('borrower_id') and body.get('book_id'):
                self.send_error(400, "Invalid request body, missing Borrower ID")                
            elif not body.get('book_id') and body.get('borrower_id'):
                self.send_error(400, "Invalid request body, missing Book ID")                
            else:
                self.send_error(400, "Invalid request body, no valid data provided")
        else:
            self.send_error(400, PATH_NOT_FOUND_ERROR)

    def handle_list_books(self):
        """
        Retrieves and sends a list of all books in the library.

        The response is a JSON array of books, where each book is represented as:
        {
            "id": <int>,
            "title": <str>,
            "author": <str>,
            "is_borrowed": <bool>
        }
        """

        with sqlite3.connect(DATABASE_NAME) as conn:
            conn.execute("PRAGMA foreign_keys = ON;")  # Enable foreign key constraints        
            c = conn.cursor()
            c.execute('SELECT * FROM books')  # Query all books
            books = [{'id': row[0], 'title': row[1], 'author': row[2], 'is_borrowed': bool(row[3])} 
                for row in c.fetchall()]  # Convert rows to dictionaries
            self.send_json_response(200, books)

    def handle_get_borrower(self, borrower_id):
        """
        Retrieves and sends details of a specific borrower.

        Args:
        - borrower_id (str): The ID of the borrower to retrieve.

        The response is a JSON object representing the borrower:
        {
            "id": <int>,
            "name": <str>,
            "email": <str>
        }
        """

        with sqlite3.connect(DATABASE_NAME) as conn:
            conn.execute("PRAGMA foreign_keys = ON;")  # Enable foreign key constraints        
            c = conn.cursor()
            c.execute('SELECT * FROM borrowers WHERE id = ?', (borrower_id,))  # Query the borrower by ID
            row = c.fetchone()

            if row:  # If a borrower is found
                borrower = {'id': row[0], 'name': row[1], 'email': row[2]}  # Convert row to dictionary
                self.send_json_response(200, borrower)
            else:  # If no borrower is found
                self.send_error(404, "Borrower not found")

    def handle_borrowed_books(self, borrower_id):
        """
        Retrieves and sends a list of books borrowed by a specific borrower.

        Args:
        - borrower_id (str): The ID of the borrower.

        The response is a JSON array of borrowed books, where each book is represented as:
        {
            "id": <int>,
            "title": <str>,
            "author": <str>
        }
        """

        with sqlite3.connect(DATABASE_NAME) as conn:
            conn.execute("PRAGMA foreign_keys = ON;")  # Enable foreign key constraints        
            c = conn.cursor()
            c.execute('''
                SELECT books.id, books.title, books.author
                FROM books
                INNER JOIN borrowed_books ON books.id = borrowed_books.book_id
                WHERE borrowed_books.borrower_id = ?
                ''', (borrower_id,))  # Query borrowed books by borrower ID
            books = [{'id': row[0], 'title': row[1], 'author': row[2]} for row in c.fetchall()]  # Convert rows to dictionaries
    
            if books:  # If borrowed books are found
                self.send_json_response(200, books)
            else:  # If no borrowed books are found
                self.send_error(404, "No borrowed books found for this borrower")

    def handle_add_book(self, body):
        """
        Adds a new book to the library.

        Args:
        - body (dict): The JSON body containing book details.

        The body should have the following structure:
        {
            "title": <str>,
            "author": <str>
        }

        The response is a JSON object representing the added book:
        {
            "id": <int>,
            "title": <str>,
            "author": <str>,
            "is_borrowed": <bool>
        }
        """
        title = body.get('title')
        author = body.get('author')
        print(f'Adding book body: {body}...')

        if not title or not author:  # Validate input
            self.send_error(400, "Title and author are required")
            return

        with sqlite3.connect(DATABASE_NAME) as conn:
            conn.execute("PRAGMA foreign_keys = ON;")  # Enable foreign key constraints
            c = conn.cursor()
            c.execute('INSERT INTO books (title, author, is_borrowed) VALUES (?, ?, ?)', 
                  (title, author, False))  # Insert the new book
            book_id = c.lastrowid  # Get the ID of the inserted book
            if not book_id.isdigit():
                self.send_error(400, "Invalid book ID format") 
                return           

            # Prepare the response
            book = {'id': book_id, 'title': title, 'author': author, 'is_borrowed': False}
            self.send_json_response(201, book)

    def handle_create_borrower(self, body):
        """
        Creates a new borrower.

        Args:
        - body (dict): The JSON body containing borrower details.

        The body should have the following structure:
        {
            "name": <str>,
            "email": <str>
        }

        The response is a JSON object representing the created borrower:
        {
            "id": <int>,
            "name": <str>,
            "email": <str>
        }
        """
        name = body.get('name')
        email = body.get('email')

        if not name or not email:  # Validate input
            self.send_error(400, "Name and email are required")
            return

        with sqlite3.connect(DATABASE_NAME) as conn:
            conn.execute("PRAGMA foreign_keys = ON;")  # Enable foreign key constraints        
            c = conn.cursor()
            c.execute('INSERT INTO borrowers (name, email) VALUES (?, ?)', (name, email))  # Insert the new borrower
            borrower_id = c.lastrowid  # Get the ID of the inserted borrower

            # Prepare the response
            borrower = {'id': borrower_id, 'name': name, 'email': email}
            self.send_json_response(201, borrower)

    def handle_borrow_book(self, body):
        """
        Records a book borrowing event.

        Args:
        - body (dict): The JSON body containing borrowing details.

        The body should have the following structure:
        {
            "borrower_id": <int>,
            "book_id": <int>
        }

        The response is a JSON object representing the borrowing event:
        {
            "borrower_id": <int>,
            "book_id": <int>
        }
        """
        borrower_id = body.get('borrower_id')
        book_id = body.get('book_id')

        if not borrower_id or not book_id:  # Validate input
            self.send_error(400, "Borrower ID and Book ID are required")
            return
        
        if not borrower_id.isdigit():
            self.send_error(400, "Invalid borrower ID format")
            return
        if not book_id.isdigit():
            self.send_error(400, "Invalid book ID format") 
            return      
            
        with sqlite3.connect(DATABASE_NAME) as conn:
            conn.execute("PRAGMA foreign_keys = ON;")  # Enable foreign key constraints        
            c = conn.cursor()

            # Check if the book is already borrowed
            c.execute('SELECT is_borrowed FROM books WHERE id = ?', (book_id,))
            book = c.fetchone()
            if not book:
                self.send_error(404, "Book not found")
                conn.close()
                return
            if book[0]:  # If the book is already borrowed
                self.send_error(400, "Book is already borrowed")
                conn.close()
                return

            # Record the borrowing event
            c.execute('INSERT INTO borrowed_books (borrower_id, book_id) VALUES (?, ?)', (borrower_id, book_id))
            c.execute('UPDATE books SET is_borrowed = ? WHERE id = ?', (True, book_id))  # Mark the book as borrowed

            # Prepare the response
            borrowing_event = {'borrower_id': borrower_id, 'book_id': book_id}
            self.send_json_response(201, borrowing_event)

def run_server(port=DEFAULT_PORT):
    """
    Starts the HTTP server for the library system.

    Args:
    - port (int): The port number to run the server on. Defaults to 8888.
    """
    server_address = ('', port)  # Bind to all available interfaces
    httpd = HTTPServer(server_address, LibraryHandler)  # Create the HTTP server
    print(f'Starting server on port {port}...')
    httpd.serve_forever()  # Start serving requests

if __name__ == '__main__':
    """
    Entry point of the application.

    Initializes the database and starts the HTTP server.
    """
    from database import init_db  # Import the database initialization function
    init_db(DATABASE_NAME)  # Initialize the database
    run_server()  # Start the server
