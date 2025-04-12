import pytest
from unittest.mock import Mock, patch
from http.server import BaseHTTPRequestHandler
from io import BytesIO
# import socket
import json

import sys
from pathlib import Path

# Add the src directory to the Python module search path
sys.path.append(str(Path(__file__).resolve().parent.parent / "src"))
from main import LibraryHandler

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

def test_do_get_books(mock_handler):
    """Test GET /books routes to handle_list_books."""
    with patch.object(mock_handler, 'handle_list_books') as mock_method:
        mock_handler.path = '/books'
        mock_handler.do_GET()
        mock_method.assert_called_once()

def test_do_get_borrower(mock_handler):
    """Test GET /borrower/ routes to handle_get_borrower."""
    with patch.object(mock_handler, 'handle_get_borrower') as mock_method:
        mock_handler.path = '/borrower/123'
        mock_handler.do_GET()
        mock_method.assert_called_once_with('123')

def test_do_get_borrowed_books(mock_handler):
    """Test GET /borrowed-books/ routes to handle_borrowed_books."""
    with patch.object(mock_handler, 'handle_borrowed_books') as mock_method:
        mock_handler.path = '/borrowed-books/456'
        mock_handler.do_GET()
        mock_method.assert_called_once_with('456')

def test_do_get_invalid_path(mock_handler):
    """Test GET with invalid path returns 400."""
    with patch.object(mock_handler, 'send_error') as mock_error:
        mock_handler.path = '/invalid-path'
        mock_handler.do_GET()
        mock_error.assert_called_once_with(400, "Path not found")

@pytest.mark.parametrize(
    "path, body, expected_call, expected_error",
    [
        # Scenario 1: Valid book data
        ("/books", {"title": "Python Basics", "author": "Anna Dee"}, True, None),
        # Scenario 2: Invalid book data (missing 'author')
        ("/books", {"title": "Missing Author"}, False, "Invalid request body, missing Author"),
        # Scenario 3: Invalid book data (missing 'title')
        ("/books", {"author": "Missing Title"}, False, "Invalid request body, missing Title"),
        # Scenario 4: Empty book data
        ("/books", {}, False, "Invalid JSON format"),
        # Scenario 5: Invalid JSON data
        ("/books", '{"title": "Invalid JSON"', False, "Invalid JSON format"),
        # Scenario 6: Invalid path (not /books)
        ("/invalid-path", {"title": "Invalid Path", "author": "Wrong Path"}, False, "Path not found"),
    ],
)
def test_do_post_add_book(mock_handler, path, body, expected_call, expected_error):
    """Test POST /books route with valid and invalid JSON using parametrization."""
    mock_handler.command = "POST"  # Set command to POST for testing
    mock_handler.path = path
    mock_handler.headers = {"Content-Length": str(len(json.dumps(body)))}
    mock_handler.rfile = BytesIO(json.dumps(body).encode())
    mock_handler.rfile.seek(0)  # Reset the file pointer to the beginning

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
        ("/borrowers", {"name": "John Doe", "email": "john@doe.com"}, True, None),
        # Scenario 2: Invalid borrower data (missing 'name')
        ("/borrowers", {"name": "Missing Email"}, False, "Invalid request body, missing Email"),
        # Scenario 3: Invalid borrower data (missing 'email')
        ("/borrowers", {"email": "missing@Name.com"}, False, "Invalid request body, missing Name"),
        # Scenario 4: Empty book data
        ("/borrowers", {}, False, "Invalid JSON format"),
        # Scenario 5: Invalid JSON data
        ("/borrowers", '{"title": "Invalid JSON"', False, "Invalid JSON format"),
        # Scenario 56: Invalid path (not /borrowers)
        ("/invalid-path", {"name": "Invalid Path", "email": "invalid@path.com"}, False, "Path not found"),
    ],
)
def test_do_post_create_borrower(mock_handler, path, body, expected_call, expected_error):
    """Test POST /borrowers routes to handle_create_borrower."""
    mock_handler.command = "POST"  # Set command to POST for testing
    mock_handler.path = path
    mock_handler.headers = {"Content-Length": str(len(json.dumps(body)))}
    mock_handler.rfile = BytesIO(json.dumps(body).encode())
    mock_handler.rfile.seek(0)  # Reset the file pointer to the beginning

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
        ("/borrow", {"borrower_id": 123, "book_id": 13}, True, None),
        # Scenario 2: Invalid borrow data (missing 'borrower_id')
        ("/borrow", {"book_id": 13}, False, "Invalid request body, missing Borrower ID"),
        # Scenario 3: Invalid borrow data (missing 'book_id')
        ("/borrow", {"borrower_id": 666}, False, "Invalid request body, missing Book ID"),
        # Scenario 4: Empty borrow data
        ("/borrow", {}, False, "Invalid JSON format"),
        # Scenario 5: Invalid JSON data
        ("/borrow", '{"title": "Invalid JSON"', False, "Invalid JSON format"),
        # Scenario 6: Invalid path (not /borrow)
        ("/invalid-path", {"name": "Invalid Path", "email": "invalid@path.com"}, False, "Path not found"),
    ],
)
def test_do_post_borrow(mock_handler, path, body, expected_call, expected_error):
    """Test POST /borrow routes to handle_borrow_book."""
    mock_handler.command = "POST"  # Set command to POST for testing
    mock_handler.path = path
    mock_handler.headers = {"Content-Length": str(len(json.dumps(body)))}
    mock_handler.rfile = BytesIO(json.dumps(body).encode())
    mock_handler.rfile.seek(0)  # Reset the file pointer to the beginning

    with patch.object(mock_handler, "handle_borrow_book") as mock_method, patch.object(
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
