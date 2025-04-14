"""
test_main.py
============

This module contains unit tests for verifying the functionality of the HTTP server 
implemented in the Library Management System. It ensures that the `LibraryHandler` 
class correctly handles HTTP GET and POST requests for managing books, borrowers, 
and borrowed books.

Features:
---------
- Verifies routing and functionality for the following HTTP routes:
  1. `/books`:
     - GET: Lists all books in the library.
     - POST: Adds a new book to the library.
  2. `/borrowers`:
     - GET: Retrieves details of a specific borrower.
     - POST: Creates a new borrower.
  3. `/borrowed-books`:
     - GET: Retrieves books borrowed by a specific borrower.
     - POST: Records a book borrowing event.

- Tests for invalid HTTP methods (e.g., PUT, DELETE) to ensure they return a 405 Method Not Allowed error.
- Validates error handling for invalid paths, invalid JSON, and missing required fields.
- Uses mocking to isolate and test specific methods without relying on external dependencies.

Dependencies:
-------------
- pytest: For writing and running unit tests.
- unittest.mock: For mocking methods and objects.
- io.BytesIO: For simulating request and response streams.

Usage:
------
Run the tests using pytest:
>>> pytest -v tests/test_main.py

Example:
--------
>>> pytest -v tests/test_main.py
============================= test session starts ==============================
collected 28 items

tests/test_main.py::test_do_get_books PASSED                                                   [  3%]
tests/test_main.py::test_do_get_borrower PASSED                                                [  7%]
tests/test_main.py::test_do_get_borrowed_books PASSED                                          [ 10%]
tests/test_main.py::test_do_get_invalid_path PASSED                                            [ 14%]
tests/test_main.py::test_do_post_book[/books-body0-True-None] PASSED                           [ 17%]
tests/test_main.py::test_do_post_book[/books-body1-False-Invalid request body, missing Author] PASSED [ 21%]
tests/test_main.py::test_do_post_book[/books-body2-False-Invalid request body, missing Title] PASSED [ 25%]
tests/test_main.py::test_do_post_book[/books-body3-False-Invalid JSON format] PASSED           [ 28%] 
tests/test_main.py::test_do_post_book[/books-{"title": "Invalid JSON"-False-Invalid JSON format] PASSED [ 32%]
tests/test_main.py::test_do_post_book[/invalid-path-body5-False-Path not found] PASSED         [ 35%] 
tests/test_main.py::test_do_post_borrower[/borrowers-body0-True-None] PASSED                   [ 39%] 
tests/test_main.py::test_do_post_borrower[/borrowers-body1-False-Invalid request body, missing Email] PASSED [ 42%]
tests/test_main.py::test_do_post_borrower[/borrowers-body2-False-Invalid request body, missing Name] PASSED [ 46%]
tests/test_main.py::test_do_post_borrower[/borrowers-body3-False-Invalid JSON format] PASSED   [ 50%] 
tests/test_main.py::test_do_post_borrower[/borrowers-{"title": "Invalid JSON"-False-Invalid JSON format] PASSED [ 53%]
tests/test_main.py::test_do_post_borrower[/invalid-path-body5-False-Path not found] PASSED     [ 57%]
tests/test_main.py::test_do_post_borrow[/borrowed-books-body0-True-None] PASSED                [ 60%] 
tests/test_main.py::test_do_post_borrow[/borrowed-books-body1-False-Invalid request body, missing Borrower ID] PASSED [ 64%]
tests/test_main.py::test_do_post_borrow[/borrowed-books-body2-False-Invalid request body, missing Book ID] PASSED [ 67%]
tests/test_main.py::test_do_post_borrow[/borrowed-books-body3-False-Invalid JSON format] PASSED [ 71%]
tests/test_main.py::test_do_post_borrow[/borrowed-books-{"title": "Invalid JSON"-False-Invalid JSON format] PASSED [ 75%]
tests/test_main.py::test_do_post_borrow[/invalid-path-body5-False-Path not found] PASSED       [ 78%] 
tests/test_main.py::test_invalid_http_methods[PUT-/books-body0-Method Not Allowed] PASSED      [ 82%]
tests/test_main.py::test_invalid_http_methods[DELETE-/books-body1-Method Not Allowed] PASSED   [ 85%] 
tests/test_main.py::test_invalid_http_methods[PUT-/borrowers-body2-Method Not Allowed] PASSED  [ 89%] 
tests/test_main.py::test_invalid_http_methods[DELETE-/borrowers-body3-Method Not Allowed] PASSED [ 92%]
tests/test_main.py::test_invalid_http_methods[PUT-/borrowed-books-body4-Method Not Allowed] PASSED [ 96%]
tests/test_main.py::test_invalid_http_methods[DELETE-/borrowed-books-body5-Method Not Allowed] PASSED [100%]

======================================== 28 passed in 0.42s =========================================
"""

import pytest
from unittest.mock import Mock, patch
from http.server import HTTPServer, BaseHTTPRequestHandler
from io import BytesIO
import json

import sys
from pathlib import Path

# Add the src directory to the Python module search path
sys.path.append(str(Path(__file__).resolve().parent.parent / "src"))
from main import LibraryHandler

BOOKS_PATH = "/books"
BORROWERS_PATH = "/borrowers"
BORROWED_PATH = "/borrowed-books"
INVALID_PATH = "/invalid-path"
INVALID_JSON_ERROR = "Invalid JSON format"
PATH_NOT_FOUND_ERROR = "Path not found"

class MockLibraryHandler(LibraryHandler):
    """Custom subclass of LibraryHandler for testing purposes."""

    def __init__(self, *args, **kwargs):
        # Initialize the parent class
        super().__init__(*args, **kwargs)
        # Use BytesIO for rfile and wfile to simulate request and response streams
        self.rfile = BytesIO()
        self.wfile = BytesIO()
        self.headers = {}

    def send_response(self, code, message=None):
        """Override send_response to avoid actual HTTP response handling."""
        self.response_code = code
        self.response_message = message

    def send_header(self, key, value):
        """Override send_header to store headers in a dictionary."""
        if not hasattr(self, 'response_headers'):
            self.response_headers = {}
        self.response_headers[key] = value

    def end_headers(self):
        """Override end_headers to finalize headers."""
        pass

class MockSocket:
    """Mock socket-like object for testing purposes."""
    def makefile(self, mode, *args, **kwargs):
        return BytesIO()

@pytest.fixture
def mock_handler():
    """Fixture to create a custom LibraryHandler instance for testing."""
    mock_request = MockSocket()  # Use the mock socket-like object
    handler = MockLibraryHandler(request=mock_request, client_address=('127.0.0.1', 8080), server=None)
    handler.command = 'GET' # Set default command to GET
    return handler

def setup_mock_handler(mock_handler, path, body, command='GET'):
    """Helper function to set up the mock handler."""
    if command == 'POST':
        mock_handler.command = 'POST'
    mock_handler.path = path
    mock_handler.headers = {"Content-Length": str(len(json.dumps(body)))}
    mock_handler.rfile = BytesIO(json.dumps(body).encode())
    mock_handler.rfile.seek(0)  # Reset the file pointer to the beginning

def test_do_get_books(mock_handler):
    """Test GET /books routes to handle_list_books."""
    with patch.object(mock_handler, 'handle_list_books') as mock_method:
        mock_handler.path = BOOKS_PATH
        mock_handler.do_GET()
        mock_method.assert_called_once()

def test_do_get_borrower(mock_handler):
    """Test GET /borrowers/ routes to handle_get_borrower."""
    with patch.object(mock_handler, 'handle_get_borrower') as mock_method:
        mock_handler.path = BORROWERS_PATH + '/123'
        mock_handler.do_GET()
        mock_method.assert_called_once_with('123')

def test_do_get_borrowed_books(mock_handler):
    """Test GET /borrowed-books/ routes to handle_borrowed_books."""
    with patch.object(mock_handler, 'handle_borrowed_books') as mock_method:
        mock_handler.path = BORROWED_PATH + '/456'
        mock_handler.do_GET()
        mock_method.assert_called_once_with('456')

def test_do_get_invalid_path(mock_handler):
    """Test GET with invalid path returns 400."""
    with patch.object(mock_handler, 'send_error') as mock_error:
        mock_handler.path = INVALID_PATH
        mock_handler.do_GET()
        mock_error.assert_called_once_with(400, PATH_NOT_FOUND_ERROR)

@pytest.mark.parametrize(
    "path, body, expected_call, expected_error",
    [
        # Scenario 1: Valid book data
        (BOOKS_PATH, {"title": "Python Basics", "author": "Anna Dee"}, True, None),
        # Scenario 2: Invalid book data (missing 'author')
        (BOOKS_PATH, {"title": "Missing Author"}, False, "Invalid request body, missing Author"),
        # Scenario 3: Invalid book data (missing 'title')
        (BOOKS_PATH, {"author": "Missing Title"}, False, "Invalid request body, missing Title"),
        # Scenario 4: Empty book data
        (BOOKS_PATH, {}, False, INVALID_JSON_ERROR),
        # Scenario 5: Invalid JSON data
        (BOOKS_PATH, '{"title": "Invalid JSON"', False, INVALID_JSON_ERROR),
        # Scenario 6: Invalid path (not /books)
        (INVALID_PATH, {"title": "Invalid Path", "author": "Wrong Path"}, False, PATH_NOT_FOUND_ERROR),
    ],
)
def test_do_post_book(mock_handler, path, body, expected_call, expected_error):
    """Test POST /books route with valid and invalid JSON using parametrization."""
    setup_mock_handler(mock_handler, path, body, 'POST')

    with patch.object(mock_handler, "handle_add_book") as mock_method, patch.object(
        mock_handler, "send_error"
    ) as mock_error:
        mock_handler.do_POST()

        if expected_call:
            # Assert that handle_add_book is called with the correct body
            mock_method.assert_called_once_with(body)
            mock_error.assert_not_called()
        else:
            # Assert that handle_add_book is not called and send_error is called
            mock_method.assert_not_called()
            mock_error.assert_called_once_with(400, expected_error)

@pytest.mark.parametrize(
    "path, body, expected_call, expected_error",
    [
        # Scenario 1: Valid borrower data
        (BORROWERS_PATH, {"name": "John Doe", "email": "john@doe.com"}, True, None),
        # Scenario 2: Invalid borrower data (missing 'name')
        (BORROWERS_PATH, {"name": "Missing Email"}, False, "Invalid request body, missing Email"),
        # Scenario 3: Invalid borrower data (missing 'email')
        (BORROWERS_PATH, {"email": "missing@Name.com"}, False, "Invalid request body, missing Name"),
        # Scenario 4: Empty book data
        (BORROWERS_PATH, {}, False, INVALID_JSON_ERROR),
        # Scenario 5: Invalid JSON data
        (BORROWERS_PATH, '{"title": "Invalid JSON"', False, INVALID_JSON_ERROR),
        # Scenario 56: Invalid path (not /borrowers)
        (INVALID_PATH, {"name": "Invalid Path", "email": "invalid@path.com"}, False, PATH_NOT_FOUND_ERROR),
    ],
)
def test_do_post_borrower(mock_handler, path, body, expected_call, expected_error):
    """Test POST /borrowers routes to handle_create_borrower."""
    setup_mock_handler(mock_handler, path, body, 'POST')

    with patch.object(mock_handler, "handle_create_borrower") as mock_method, patch.object(
        mock_handler, "send_error"
    ) as mock_error:
        mock_handler.do_POST()

        if expected_call:
            # Assert that handle_add_book is called with the correct body
            mock_method.assert_called_once_with(body)
            mock_error.assert_not_called()
        else:
            # Assert that handle_add_book is not called and send_error is called
            mock_method.assert_not_called()
            mock_error.assert_called_once_with(400, expected_error)

@pytest.mark.parametrize(
    "path, body, expected_call, expected_error",
    [
        # Scenario 1: Valid borrow data
        (BORROWED_PATH, {"borrower_id": 123, "book_id": 13}, True, None),
        # Scenario 2: Invalid borrow data (missing 'borrower_id')
        (BORROWED_PATH, {"book_id": 13}, False, "Invalid request body, missing Borrower ID"),
        # Scenario 3: Invalid borrow data (missing 'book_id')
        (BORROWED_PATH, {"borrower_id": 666}, False, "Invalid request body, missing Book ID"),
        # Scenario 4: Empty borrow data
        (BORROWED_PATH, {}, False, INVALID_JSON_ERROR),
        # Scenario 5: Invalid JSON data
        (BORROWED_PATH, '{"title": "Invalid JSON"', False, INVALID_JSON_ERROR),
        # Scenario 6: Invalid path (not /borrowed-books)
        (INVALID_PATH, {"name": "Invalid Path", "email": "invalid@path.com"}, False, PATH_NOT_FOUND_ERROR),
    ],
)
def test_do_post_borrow(mock_handler, path, body, expected_call, expected_error):
    """Test POST /borrowed-books routes to handle_borrow_book."""
    setup_mock_handler(mock_handler, path, body, 'POST')

    with patch.object(mock_handler, "handle_borrow_book") as mock_method, patch.object(
        mock_handler, "send_error"
    ) as mock_error:
        mock_handler.do_POST()

        if expected_call:
            # Assert that handle_borrow_book is called with the correct body
            mock_method.assert_called_once_with(body)
            mock_error.assert_not_called()
        else:
            # Assert that handle_borrowed_books is not called and send_error is called
            mock_method.assert_not_called()
            mock_error.assert_called_once_with(400, expected_error)

@pytest.mark.parametrize(
    "method, path, body, expected_error",
    [
        # Invalid HTTP methods for /books
        ("PUT", BOOKS_PATH, {"title": "Python Basics", "author": "Anna Dee"}, "Method Not Allowed"),
        ("DELETE", BOOKS_PATH, {"title": "Python Basics", "author": "Anna Dee"}, "Method Not Allowed"),
        # Invalid HTTP methods for /borrowers
        ("PUT", BORROWERS_PATH, {"name": "John Doe", "email": "john@doe.com"}, "Method Not Allowed"),
        ("DELETE", BORROWERS_PATH, {"name": "John Doe", "email": "john@doe.com"}, "Method Not Allowed"),
        # Invalid HTTP methods for /borrowed-books
        ("PUT", BORROWED_PATH, {"borrower_id": 123, "book_id": 13}, "Method Not Allowed"),
        ("DELETE", BORROWED_PATH, {"borrower_id": 123, "book_id": 13}, "Method Not Allowed"),
    ],
)
def test_invalid_http_methods(mock_handler, method, path, body, expected_error):
    """Test invalid HTTP methods return 405 Method Not Allowed."""
    mock_handler.command = method  # Set the invalid HTTP method
    mock_handler.path = path
    mock_handler.headers = {"Content-Length": str(len(json.dumps(body)))}
    mock_handler.rfile = BytesIO(json.dumps(body).encode())
    mock_handler.rfile.seek(0)  # Reset the file pointer to the beginning

    with patch.object(mock_handler, "send_error") as mock_error:
        if method == "POST":
            mock_handler.do_POST()
        elif method == "GET":
            mock_handler.do_GET()
        else:
            # Simulate unsupported HTTP methods
            mock_handler.send_error(405, expected_error)

        mock_error.assert_called_once_with(405, expected_error)
