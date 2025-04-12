from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import sqlite3
from urllib.parse import parse_qs, urlparse

DATABASE_NAME = 'library.db'

class LibraryHandler(BaseHTTPRequestHandler):
    """
    HTTP request handler for the library system.

    This class handles GET and POST requests to manage books, borrowers, and borrowed books.
    It interacts with the SQLite database to perform CRUD operations.
    """

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
        
        if path == '/books':
            self.handle_list_books()
        elif path.startswith('/borrower/'):
            borrower_id = path.split('/')[-1]
            self.handle_get_borrower(borrower_id)
        elif path.startswith('/borrowed-books/'):
            borrower_id = path.split('/')[-1]
            self.handle_borrowed_books(borrower_id)
        else:
            self.send_error(400, "Path not found")

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
                raise ValueError("Invalid JSON format")
            
            post_data = self.rfile.read(content_length)  # Read the request body
            # print(f'post data = {post_data}, len={len(post_data)}...')
            # print(f'post data decode {post_data.decode('utf-8')}...')
            if not post_data:  # Check if the body is empty
                raise ValueError("Invalid JSON format")

            body = json.loads(post_data.decode('utf-8'))  # Parse the JSON body
            # print(f'body = {body}')
            if not isinstance(body, dict):  # Ensure the parsed body is a dictionary
                raise ValueError("Invalid JSON format")
        except (ValueError, json.JSONDecodeError):
            self.send_error(400, "Invalid JSON format")
            return
    
        if self.path == '/books':
            # if all(key in body for key in ['title', 'author']):
            if body.get('title') and body.get('author'):
                self.handle_add_book(body)
            elif not body.get('title') and body.get('author'):
                self.send_error(400, "Invalid request body, missing Title")
            elif not body.get('author') and body.get('title'):
                self.send_error(400, "Invalid request body, missing Author")                
            else:
                self.send_error(400, "Invalid request body, no valid data provided")                
            
        elif self.path == '/borrowers':
            if body.get('name') and body.get('email'):
                self.handle_create_borrower(body)
            elif not body.get('name') and body.get('email'):
                self.send_error(400, "Invalid request body, missing Name")
            elif not body.get('email') and body.get('name'):
                self.send_error(400, "Invalid request body, missing Email")                
            else:
                self.send_error(400, "Invalid request body, no valid data provided")                

        elif self.path == '/borrow':
            if body.get('borrower_id') and body.get('book_id'):
                self.handle_borrow_book(body)
            elif not body.get('borrower_id') and body.get('book_id'):
                self.send_error(400, "Invalid request body, missing Borrower ID")                
            elif not body.get('book_id') and body.get('borrower_id'):
                self.send_error(400, "Invalid request body, missing Book ID")                
            else:
                self.send_error(400, "Invalid request body, no valid data provided")
        else:
            self.send_error(400, "Path not found")

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
        conn = sqlite3.connect(DATABASE_NAME)  # Connect to the database
        c = conn.cursor()
        c.execute('SELECT * FROM books')  # Query all books
        books = [{'id': row[0], 'title': row[1], 'author': row[2], 'is_borrowed': bool(row[3])} 
                for row in c.fetchall()]  # Convert rows to dictionaries
        conn.close()  # Close the database connection
        
        self.send_response(200) # Send the response
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(books).encode())  # Write the JSON response

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
        conn = sqlite3.connect(DATABASE_NAME)
        c = conn.cursor()
        c.execute('SELECT * FROM borrowers WHERE id = ?', (borrower_id,))  # Query the borrower by ID
        row = c.fetchone()
        conn.close()

        if row:  # If a borrower is found
            borrower = {'id': row[0], 'name': row[1], 'email': row[2]}  # Convert row to dictionary
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(borrower).encode())
        else:  # If no borrower is found
            self.send_error(400, "Borrower not found")

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
        conn = sqlite3.connect(DATABASE_NAME)
        c = conn.cursor()
        c.execute('''
            SELECT books.id, books.title, books.author
            FROM books
            INNER JOIN borrowed_books ON books.id = borrowed_books.book_id
            WHERE borrowed_books.borrower_id = ?
        ''', (borrower_id,))  # Query borrowed books by borrower ID
        books = [{'id': row[0], 'title': row[1], 'author': row[2]} for row in c.fetchall()]  # Convert rows to dictionaries
        conn.close()

        if books:  # If borrowed books are found
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(books).encode())
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

        conn = sqlite3.connect(DATABASE_NAME)  # Connect to the database
        c = conn.cursor()
        c.execute('INSERT INTO books (title, author, is_borrowed) VALUES (?, ?, ?)', 
                  (title, author, False))  # Insert the new book
        book_id = c.lastrowid  # Get the ID of the inserted book
        conn.commit()  # Commit the transaction
        conn.close()

        # Prepare the response
        book = {'id': book_id, 'title': title, 'author': author, 'is_borrowed': False}
        self.send_response(201)  # Send a 201 Created status
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(book).encode())

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

        conn = sqlite3.connect(DATABASE_NAME)
        c = conn.cursor()
        c.execute('INSERT INTO borrowers (name, email) VALUES (?, ?)', (name, email))  # Insert the new borrower
        borrower_id = c.lastrowid  # Get the ID of the inserted borrower
        conn.commit()
        conn.close()

        # Prepare the response
        borrower = {'id': borrower_id, 'name': name, 'email': email}
        self.send_response(201)  # Send a 201 Created status
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(borrower).encode())

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

        conn = sqlite3.connect(DATABASE_NAME)
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
        conn.commit()
        conn.close() 

        # Prepare the response
        borrowing_event = {'borrower_id': borrower_id, 'book_id': book_id}
        self.send_response(201)  # Send a 201 Created status
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(borrowing_event).encode())

def run_server(port=8888):
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
