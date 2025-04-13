# Library Management System

The **Library Management System** is a Python-based application that provides an HTTP server for managing books, borrowers, and borrowed books. It uses an SQLite database for persistent storage and supports CRUD operations via HTTP GET and POST requests.

## Features

- **Books Management**:
  - List all books in the library.
  - Add new books to the library.

- **Borrowers Management**:
  - Retrieve details of borrowers.
  - Add new borrowers to the system.

- **Borrowed Books Management**:
  - Retrieve books borrowed by a specific borrower.
  - Record book borrowing events.

- **Data Integrity**:
  - Enforces foreign key constraints in the SQLite database.
  - Validates request bodies and query parameters.
  - Returns appropriate HTTP status codes and error messages for invalid requests.

## Technologies Used

- **Python**:
  - `http.server`: For creating the HTTP server.
  - `sqlite3`: For database operations.
  - `json`: For parsing and generating JSON responses.
  - `urllib.parse`: For parsing query parameters.

- **SQLite**:
  - Lightweight database for persistent storage.
  - Schema includes `books`, `borrowers`, and `borrowed_books` tables.

- **Testing**:
  - `pytest`: For unit testing.
  - `unittest.mock`: For mocking methods and objects.

## Installation

1. Clone the repository:

   ```bash
   git clone https://github.com/drgyl/books.git
   cd books
   ```

2. Install dependencies (if any):

    ```bash
    pip install -r requirements.txt
    ```

## Usage

### Start the Server

Run the following command to start the server:
    ```bash
    python src/main.py
    ```

The server will start on http://localhost:8888.

2. Use an HTTP client (e.g., `curl`, PowerShell or Postman) to interact with the server:

   - List all books:
     >>> curl -X GET http://localhost:8888/books
     >>> Invoke-RestMethod -Uri http://localhost:8888/books -Method GET

   - Add a new book:
     >>> curl -X POST http://localhost:8888/books -H "Content-Type: application/json" -d '{"title": "Python Basics", "author": "John Doe"}'
     >>> Invoke-RestMethod -Uri http://localhost:8888/books -Method POST -Headers @{"Content-Type"="application/json"} -Body '{"title": "Python Basics", "author": "John Doe"}'

   - List all borrowers:
     >>> curl -X GET http://localhost:8888/borrowers
     >>> Invoke-RestMethod -Uri http://localhost:8888/borrowers -Method GET

   - Add a new borrower:
     >>> curl -X POST http://localhost:8888/borrowers -H "Content-Type: application/json" -d '{"name": "Jane Smith", "email": "jane.smith@example.com"}'
     >>> Invoke-RestMethod -Uri http://localhost:8888/borrowers -Method POST -Headers @{"Content-Type"="application/json"} -Body '{"name": "Jane Smith", "email": "jane.smith@example.com"}'

   - Get details of a specific borrower:
     >>> curl -X GET http://localhost:8888/borrowers/1
     >>> Invoke-RestMethod -Uri http://localhost:8888/borrowers/1 -Method GET

   - List books borrowed by a specific borrower:
     >>> curl -X GET http://localhost:8888/borrowed-books/1
     >>> Invoke-RestMethod -Uri http://localhost:8888/borrowed-books/1 -Method GET

   - Record a book borrowing event:
     >>> curl -X POST http://localhost:8888/borrowed-books -H "Content-Type: application/json" -d '{"borrower_id": 1, "book_id": 2}'
     >>> Invoke-RestMethod -Uri http://localhost:8888/borrowed-books -Method POST -Headers @{"Content-Type"="application/json"} -Body '{"borrower_id": 1, "book_id": 2}'

### API Endpoints

```bash
/books
```
    - GET: List all books

    ```bash
    curl -X GET http://localhost:8888/books
    ```

    - POST: Add a new book

    ```bash
    curl -X POST http://localhost:8888/books -H "Content-Type: application/json" -d '{"title": "Python Basics", "author": "John Doe"}'
    ```bash

/borrowers
```
    - GET: List all borrowers

    ```bash
    curl -X GET http://localhost:8888/borrowers
    ```
    - POST: Add a new borrower

    ```bash
    curl -X POST http://localhost:8888/borrowers -H "Content-Type: application/json" -d '{"name": "Jane Smith", "email": "jane.smith@example.com"}'
    ```

```bash
/borrowed-books
```
    - GET: Retrieve books borrowed by a specific borrower

    ```bash
    curl -X GET http://localhost:8888/borrowed-books/1
    ```

    - POST: Record a book borrowing event

    ```bash
    curl -X POST http://localhost:8888/borrowed-books -H "Content-Type: application/json" -d '{"borrower_id": 1, "book_id": 2}'
    ```

## Testing

Run the unit tests using pytest:

    ```bash
    pytest -v tests/
    ```

## Project Structure

```bash
library-management-system/
├── src/
│   ├── main.py          # HTTP server implementation
│   ├── database.py      # SQLite database initialization and management
├── tests/
│   ├── test_main.py     # Unit tests for the HTTP server
│   ├── test_database.py # Unit tests for the database
├── [README.md]          # Project documentation
└── requirements.txt     # Python dependencies (if any)
```

## License
This project is licensed under the MIT License. See the LICENSE file for details.

## Acknowledgments
SQLite documentation: https://sqlite.org/docs.html
Python documentation: https://docs.python.org/3/
