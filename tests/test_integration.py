"""
test_integration.py
====================

This module contains integration tests for the Library Management System. It verifies 
the end-to-end functionality of the HTTP server, database operations, and API endpoints 
by simulating real-world workflows and scenarios.

Purpose:
--------
- Ensure that the HTTP server correctly handles requests for managing books, borrowers, 
  and borrowed books.
- Validate the interaction between the server and the SQLite database.
- Test the system's behavior under various conditions, including valid and invalid inputs.

Main Functions:
---------------
- `test_full_workflow`: Tests the complete workflow of adding a book, creating a borrower, 
  and borrowing a book, while verifying the database state.
- `test_invalid_book_borrow`: Tests the behavior when attempting to borrow a non-existent book.
- `test_foreign_key_constraints`: Verifies that foreign key constraints are enforced in the database.
- `test_concurrent_borrowing`: Simulates concurrent borrowing attempts to ensure proper handling 
  of book availability.


Usage:
------
Run the tests using `unittest`:
>>> python -m unittest tests/test_integration.py

Example:
--------
1. Start the test server and run all integration tests:
   ```bash
   python -m unittest tests/test_integration.py

test_concurrent_borrowing (tests.test_integration.TestLibraryIntegration.test_concurrent_borrowing) ... 127.0.0.1 - - [14/Apr/2025 13:35:41] "POST /books HTTP/1.1" 201 -
127.0.0.1 - - [14/Apr/2025 13:35:43] "POST /borrowers HTTP/1.1" 201 -
127.0.0.1 - - [14/Apr/2025 13:35:45] "POST /borrowers HTTP/1.1" 201 -
127.0.0.1 - - [14/Apr/2025 13:35:47] code 404, message Book not found
127.0.0.1 - - [14/Apr/2025 13:35:47] "POST /borrowed-books HTTP/1.1" 404 -
FAIL
test_foreign_key_constraints (tests.test_integration.TestLibraryIntegration.test_foreign_key_constraints) ... ok
test_full_workflow (tests.test_integration.TestLibraryIntegration.test_full_workflow) ... 127.0.0.1 - - [14/Apr/2025 13:35:49] "POST /books HTTP/1.1" 201 -
127.0.0.1 - - [14/Apr/2025 13:35:51] "POST /borrowers HTTP/1.1" 201 -
127.0.0.1 - - [14/Apr/2025 13:35:53] code 404, message Book not found
127.0.0.1 - - [14/Apr/2025 13:35:53] "POST /borrowed-books HTTP/1.1" 404 -
FAIL
test_invalid_book_borrow (tests.test_integration.TestLibraryIntegration.test_invalid_book_borrow) ... 127.0.0.1 - - [14/Apr/2025 13:35:55] code 404, message Book not found
127.0.0.1 - - [14/Apr/2025 13:35:55] "POST /borrowed-books HTTP/1.1" 404 -
ok
"""

import unittest
import sqlite3
import requests
from http.server import HTTPServer
from threading import Thread
import time
import os

import sys
from pathlib import Path

# Add the src directory to the Python module search path
sys.path.append(str(Path(__file__).resolve().parent.parent / "src"))
import main
from database import init_db

# Use a different database and port for testing
TEST_DB = 'test_library.db'
TEST_PORT = 8889

class TestLibraryIntegration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Initialize test database
        init_db(TEST_DB)
        
        # Patch main module to use test database
        main.DATABASE_NAME = TEST_DB
        
        # Start test server in background thread
        cls.server = HTTPServer(('localhost', TEST_PORT), main.LibraryHandler)
        cls.server_thread = Thread(target=cls.server.serve_forever)
        cls.server_thread.daemon = True
        cls.server_thread.start()
        
        # Wait for server to start
        time.sleep(0.5)

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server_thread.join()
        if os.path.exists(TEST_DB):
            os.remove(TEST_DB)

    def setUp(self):
        # Clear database before each test
        with sqlite3.connect(TEST_DB) as conn:
            conn.execute("DELETE FROM books")
            conn.execute("DELETE FROM borrowers")
            conn.execute("DELETE FROM borrowed_books")

    def test_full_workflow(self):
        # Test book creation
        book_data = {"title": "Library Testing", "author": "Dummy Author"}
        book_resp = requests.post(f'http://localhost:{TEST_PORT}/{main.BOOKS_PATH}', json=book_data)
        self.assertEqual(book_resp.status_code, 201)
        book_id = book_resp.json()['id']

        # Test borrower creation
        borrower_data = {"name": "Test User", "email": "testuser@library.com"}
        borrower_resp = requests.post(f'http://localhost:{TEST_PORT}/{main.BORROWERS_PATH}', json=borrower_data)
        self.assertEqual(borrower_resp.status_code, 201)
        borrower_id = borrower_resp.json()['id']

        # Test borrowing a book
        borrow_data = {"borrower_id": borrower_id, "book_id": book_id}
        borrow_resp = requests.post(f'http://localhost:{TEST_PORT}/{main.BORROWED_PATH}', json=borrow_data)
        self.assertEqual(borrow_resp.status_code, 201)
        # print(f"Borrow data: {borrow_data}\nBorrowing response: {borrow_resp.json()}")
        # Verify database state
        with sqlite3.connect(TEST_DB) as conn:
            # Check book status
            c = conn.execute("SELECT is_borrowed FROM books WHERE id = ?", (book_id,))
            self.assertEqual(c.fetchone()[0], 1)
            
            # Check borrowing record
            c = conn.execute("SELECT * FROM borrowed_books WHERE book_id = ?", (book_id,))
            self.assertIsNotNone(c.fetchone())

    def test_invalid_book_borrow(self):
        # Test borrowing non-existent book
        invalid_data = {"borrower_id": 999, "book_id": 999}
        response = requests.post(f'http://localhost:{TEST_PORT}/{main.BORROWED_PATH}', json=invalid_data)
        self.assertEqual(response.status_code, 404)
       
        # TODO: Verify error response format
        # self.assertIn("error", response.json())
        # raise JSONDecodeError("Expecting value", s, err.value) from None
        # json.decoder.JSONDecodeError: Expecting value: line 1 column 1 (char 0)

    def test_foreign_key_constraints(self):
        # Direct database test of foreign key enforcement
        with self.assertRaises(sqlite3.IntegrityError) as cm:
            with sqlite3.connect(TEST_DB) as conn:
                conn.execute("PRAGMA foreign_keys = ON")
                conn.execute("INSERT INTO borrowed_books (borrower_id, book_id) VALUES (?, ?)", (999, 999))
        
        self.assertIn("FOREIGN KEY constraint failed", str(cm.exception))

    def test_concurrent_borrowing(self):
        # Create test book
        book_data = {"title": "Concurrent Book", "author": "Con Author"}
        book_resp = requests.post(f'http://localhost:{TEST_PORT}/{main.BOOKS_PATH}', json=book_data)
        book_id = book_resp.json()['id']

        # Create two borrowers
        borrower1 = requests.post(f'http://localhost:{TEST_PORT}/{main.BORROWERS_PATH}', 
                                json={"name": "Con User1", "email": "conuser1@test.com"})
        borrower2 = requests.post(f'http://localhost:{TEST_PORT}/{main.BORROWERS_PATH}',
                                json={"name": "ConCurrent User2", "email": "user2@text.com"})
        # print(f"Borrower1: {borrower1.json()}, Borrower2: {borrower2.json()}, book: {book_resp.json()}")
        # First borrow should succeed
        resp1 = requests.post(f'http://localhost:{TEST_PORT}/{main.BORROWED_PATH}',
                            json={"borrower_id": borrower1.json()['id'], "book_id": book_id})
        self.assertEqual(resp1.status_code, 201)

        # Second borrow should fail
        resp2 = requests.post(f'http://localhost:{TEST_PORT}/{main.BORROWED_PATH}',
                            json={"borrower_id": borrower2.json()['id'], "book_id": book_id})
        self.assertEqual(resp2.status_code, 400)

if __name__ == '__main__':
    unittest.main()