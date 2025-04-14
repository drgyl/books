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
  - `unittest`: For mocking methods and objects as well as buiding integration testing

- **OpenTelemetry**:

    ***Spans***:
    - HTTP spans: "HTTP GET" and "HTTP POST" to capture lifecycle of HTTP requests, including route handling and response generation

    - DB spans: capturing all database queries. tracking the execution and ensuring proper database interaction ("ListBooksQuery", "ListBorrowerQuery", "GetBorrowerQuery", "AddBookQuery", "CreateBorrowerQuery", "BorrowBookQuery")

    ***Metrics***:
    - "http.server.requests"

        Type: Counter

        Description: Counts the total number of HTTP requests handled by the server.

        Attributes:

            - http.method: The HTTP method (GET, POST).

            - http.route: The requested route.

            - http.status_code: The HTTP response status code.

            - http.status_category: The status code category (e.g., 2xx, 4xx).

        Purpose: Tracks the volume of HTTP requests and categorizes them by status code.

    - "http.request.duration.ms"

        Type: Histogram

        Description: Measures the duration of HTTP requests in milliseconds.

        Attributes:

            - http.method: The HTTP method (GET, POST).

            - http.route: The requested route (e.g., /books, /borrowers).

            - http.status_code: The HTTP response status code (e.g., 200, 404).

        Purpose: Provides insights into the performance of HTTP request handling.

    - "db.connections.active"
    
        Type: UpDownCounter

        Description: Tracks the number of active SQLite database connections.

        Attributes:

            - db.name: The name of the database (library.db).

        Purpose: Monitors the lifecycle of database connections to ensure proper resource management.

## Installation

1. Clone the repository:

   ```
   git clone https://github.com/drgyl/books.git
   cd books
   ```

2. Install dependencies:

    ```
    pip install -r requirements.txt
    ```

    Following packages were installed:
    ```
    pytest, opentelemetry-api opentelemetry-sdk, opentelemetry-semantic-conventions
    ```

## Testing

Run the unit tests using pytest:

    ```
    pytest -v tests/
    ```

Run the integration tests using python:

    ```
    python -m unittest tests/test_integration.py -v
    ```  

## Project Structure

```
library-management-system/
├── src/
│   ├── main.py             # HTTP server implementation
│   ├── database.py         # SQLite database initialization and management
├── tests/
│   ├── test_main.py        # Unit tests for the HTTP server
│   ├── test_database.py    # Unit tests for the database
│   ├── test_integration.py # Integration tests for the application
├── README.md               # Project documentation
└── requirements.txt        # Python dependencies (if any)
```

## Usage

### Start the Server

Run the following command to start the server:

    ```bash
    python src/main.py
    ```

The server will start on http://localhost:8888.

Use an HTTP client (e.g., `curl`, `PowerShell` or `Postman`) to interact with the server:

   - List all books:
     > ```curl -X GET http://localhost:8888/books```

     > ```Invoke-RestMethod -Uri http://localhost:8888/books -Method GET```

   - Add a new book:
     > ```curl -X POST http://localhost:8888/books -H "Content-Type: application/json" -d '{"title": "Python Basics", "author": "John Doe"}'```

     > ```Invoke-RestMethod -Uri http://localhost:8888/books -Method POST -Headers @{"Content-Type"="application/json"} -Body '{"title": "Python Basics", "author": "John Doe"}'```

   - List all borrowers:
     > ```curl -X GET http://localhost:8888/borrowers```

     > ```Invoke-RestMethod -Uri http://localhost:8888/borrowers -Method GET```

   - Add a new borrower:
     > ```curl -X POST http://localhost:8888/borrowers -H "Content-Type: application/json" -d '{"name": "Jane Smith", "email": "jane.smith@example.com"}'```

     > ```Invoke-RestMethod -Uri http://localhost:8888/borrowers -Method POST -Headers @{"Content-Type"="application/json"} -Body '{"name": "Jane Smith", "email": "jane.smith@example.com"}'```

   - Get details of a specific borrower:
     > ```curl -X GET http://localhost:8888/borrowers/<id>```

     > ```Invoke-RestMethod -Uri http://localhost:8888/borrowers/<id> -Method GET```

   - List borrowed books:
     > ```curl -X GET http://localhost:8888/borrowed-books```

     > ```Invoke-RestMethod -Uri http://localhost:8888/borrowed-books -Method GET```

   - List books borrowed by a specific borrower:
     > ```curl -X GET http://localhost:8888/borrowed-books/<id>```

     > ```Invoke-RestMethod -Uri http://localhost:8888/borrowed-books/<id> -Method GET```

   - Record a book borrowing event:
     > ```curl -X POST http://localhost:8888/borrowed-books -H "Content-Type: application/json" -d '{"borrower_id": 1, "book_id": 2}'```

     > ```Invoke-RestMethod -Uri http://localhost:8888/borrowed-books -Method POST -Headers @{"Content-Type"="application/json"} -Body '{"borrower_id": 1, "book_id": 2}'```

### API Endpoints

```
/books
```
    - GET: List all books

    ```
    curl -X GET http://localhost:8888/books
    ```

    - POST: Add a new book

    ```
    curl -X POST http://localhost:8888/books -H "Content-Type: application/json" -d '{"title": "Python Basics", "author": "John Doe"}'

```
/borrowers
```
    - GET: List all borrowers

    ```
    curl -X GET http://localhost:8888/borrowers
    ```

    - GET: List all books borrowed per userid

    ```
    curl -X GET http://localhost:8888/borrowers/<id>
    ```

    - POST: Add a new borrower

    ```
    curl -X POST http://localhost:8888/borrowers -H "Content-Type: application/json" -d '{"name": "Jane Smith", "email": "jane.smith@example.com"}'
    ```

```
/borrowed-books
```

    - GET: Retrieve all borrowed books

    ```
    curl -X GET http://localhost:8888/borrowed-books
    ```

    - GET: Retrieve books borrowed by a specific borrower

    ```
    curl -X GET http://localhost:8888/borrowed-books/1
    ```

    - POST: Record a book borrowing event

    ```
    curl -X POST http://localhost:8888/borrowed-books -H "Content-Type: application/json" -d '{"borrower_id": 1, "book_id": 2}'
    ```

## License
This project is licensed under the MIT License. See the LICENSE file for details.

## Acknowledgments
SQLite documentation: https://sqlite.org/docs.html

Python documentation: https://docs.python.org/3/
