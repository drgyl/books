"""
test_database.py
================

This module contains unit tests for verifying the functionality of the SQLite database
used in the Library Management System. It ensures that the database schema, constraints,
and initialization logic are implemented correctly.

Features:
---------
- Verifies that the database file and tables are created correctly.
- Ensures that the schema for `books`, `borrowers`, and `borrowed_books` tables matches the expected structure.
- Validates foreign key constraints and ensures they are enforced.
- Tests for unique constraints, such as the `email` column in the `borrowers` table.
- Ensures that the `init_db` function is idempotent and can be safely called multiple times.

Dependencies:
-------------
- pytest: For writing and running unit tests.
- sqlite3: For interacting with the SQLite database.

Usage:
------
Run the tests using pytest:
>>> pytest -v tests/test_database.py

Example:
--------
>>> pytest -v tests/test_database.py
============================= test session starts ==============================
collected 7 items

tests/test_database.py::test_db_initialization PASSED
tests/test_database.py::test_table_schema[books] PASSED
tests/test_database.py::test_table_schema[borrowers] PASSED
tests/test_database.py::test_table_schema[borrowed_books] PASSED
tests/test_database.py::test_borrowed_books_foreign_keys PASSED
tests/test_database.py::test_foreign_key_constraints PASSED
tests/test_database.py::test_idempotent_initialization PASSED
============================== 6 passed in 0.12s ===============================
"""

import sqlite3
import pytest
import sys
from pathlib import Path

# Add the src directory to the Python module search path
sys.path.append(str(Path(__file__).resolve().parent.parent / "src"))
from database import init_db

@pytest.fixture
def temp_db(tmp_path):
    """Fixture to create a temporary database for testing."""
    db_path = tmp_path / "test_library.db"
    if db_path.exists():
        db_path.unlink() # Delete the existing DB if it exists
    init_db(db_path)   
    return db_path

def get_table_info(db_path, table_name):
    """Helper function to retrieve column details for a table."""
    with sqlite3.connect(db_path) as conn:
        conn.execute("PRAGMA foreign_keys = ON;")  # Enable foreign key constraints
        cursor = conn.cursor()
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = cursor.fetchall()
        # print(f"Columns in {table_name}: {columns}")  # Debugging line
        return columns

def get_foreign_keys(db_path, table_name):
    """Helper function to retrieve foreign key constraints for a table."""
    with sqlite3.connect(db_path) as conn:
        conn.execute("PRAGMA foreign_keys = ON;")
        cursor = conn.cursor()    
        cursor.execute(f"PRAGMA foreign_key_list({table_name})")
        fks = cursor.fetchall()
        # print(f"Foreign keys in {table_name}: {fks}")  # Debugging line
        return fks

def test_db_initialization(temp_db):
    """Verify that the database file and tables are created."""
    assert temp_db.exists(), "Database file was not created"

@pytest.mark.parametrize("table_name, expected_columns", [
    ("books", ["id", "title", "author", "is_borrowed"]),
    ("borrowers", ["id", "name", "email"]),
    ("borrowed_books", ["id", "book_id", "borrower_id", "borrow_date"]),
])
def test_table_schema(temp_db, table_name, expected_columns):
    columns = get_table_info(temp_db, table_name)
    column_names = [col[1] for col in columns]
    for col in expected_columns:
        assert col in column_names, f"Column '{col}' is missing in the {table_name} table"

    # Verify constraints
    if table_name == "books":
        title_not_null = any(col[1] == "title" and col[3] == 1 for col in columns)
        author_not_null = any(col[1] == "author" and col[3] == 1 for col in columns)
        assert title_not_null, f"title column lacks NOT NULL constraint in the {table_name} table"
        assert author_not_null, f"author column lacks NOT NULL constraint in the {table_name} table"

    elif table_name == "borrowers":
        with sqlite3.connect(temp_db) as conn:
            conn.execute("PRAGMA foreign_keys = ON;")
            cursor = conn.cursor()
            cursor.execute(f"PRAGMA index_list(borrowers)")
            indexes = cursor.fetchall()
            # print(f"Indexes in borrowers table: {indexes}")  # Debugging line
 
            # Verify email uniqueness
            # Find the unique index
            unique_index = next((idx for idx in indexes if idx[2] == 1), None)  # Check if the index is unique
            assert unique_index, f"No UNIQUE index found on the {table_name} table"

            # Get the columns in the unique index
            cursor.execute(f"PRAGMA index_info({unique_index[1]})")
            index_columns = cursor.fetchall()
            # print(f"Columns in unique index {unique_index[1]}: {index_columns}")  # Debugging line

            # Check if the email column is part of the unique index
            email_in_unique_index = any(col[2] == "email" for col in index_columns)
            assert email_in_unique_index, f"The email column does not have a UNIQUE constraint in the {table_name} table"

def test_borrowed_books_foreign_keys(temp_db):
    fks = get_foreign_keys(temp_db, "borrowed_books")
    assert len(fks) == 2, "Expected 2 foreign key constraints"

    # Verify foreign key to books
    book_fk = [fk for fk in fks if fk[2] == "books"]
    print(f"Foreign keys in borrowed_books table: {book_fk}")  # Debugging line
    assert book_fk, "Missing foreign key to books table"

    # Verify foreign key to borrowers
    borrower_fk = [fk for fk in fks if fk[2] == "borrowers"]
    # print(f"Foreign keys in borrowed_books table: {borrower_fk}")  # Debugging line
    assert borrower_fk, "Missing foreign key to borrowers table"

# Verify that foreign key constraints are enforced by attempting invalid inserts.
def test_foreign_key_constraints(temp_db):
    with sqlite3.connect(temp_db) as conn:
        conn.execute("PRAGMA foreign_keys = ON;")  # Enable foreign key constraints
        cursor = conn.cursor()
        
        # Attempt to insert a borrowed book with a non-existent book_id
        with pytest.raises(sqlite3.IntegrityError):
            cursor.execute("INSERT INTO borrowed_books (book_id, borrower_id, borrow_date) VALUES (999, 1, '2025-01-01')")

        # Attempt to insert a borrowed book with a non-existent borrower_id
        with pytest.raises(sqlite3.IntegrityError):
            cursor.execute("INSERT INTO borrowed_books (book_id, borrower_id, borrow_date) VALUES (1, 999, '2025-01-01')")

def test_idempotent_initialization(temp_db):
    """Ensure init_db can be safely called multiple times."""
    init_db(temp_db)  # Call init_db again on the same database
    tables = ["books", "borrowers", "borrowed_books"]

    with sqlite3.connect(temp_db) as conn:
        conn.execute("PRAGMA foreign_keys = ON;")
        cursor = conn.cursor()
        for table in tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            assert count == 0, f"Table {table} should be empty after idempotent initialization"
