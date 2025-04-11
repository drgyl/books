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
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = cursor.fetchall()
    print(f"Columns in {table_name}: {columns}")  # Debugging line
    conn.close()
    return columns

def get_foreign_keys(db_path, table_name):
    """Helper function to retrieve foreign key constraints for a table."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute(f"PRAGMA foreign_key_list({table_name})")
    fks = cursor.fetchall()
    # print(f"Foreign keys in {table_name}: {fks}")  # Debugging line
    conn.close()
    return fks

def test_db_initialization(temp_db):
    """Verify that the database file and tables are created."""
    assert temp_db.exists(), "Database file was not created"

def test_books_table_schema(temp_db):
    columns = get_table_info(temp_db, "books")
    column_names = [col[1] for col in columns]
    # print(f"Columns in books table: {column_names}")  # Debugging line
    # Check required columns
    assert "id" in column_names
    assert "title" in column_names
    assert "author" in column_names
    assert "is_borrowed" in column_names

    # Verify constraints
    title_not_null = any(col[1] == "title" and col[3] == 1 for col in columns)
    author_not_null = any(col[1] == "author" and col[3] == 1 for col in columns)
    assert title_not_null, "title column lacks NOT NULL constraint"
    assert author_not_null, "author column lacks NOT NULL constraint"

def test_borrowers_table_schema(temp_db):
    columns = get_table_info(temp_db, "borrowers")
    column_names = [col[1] for col in columns]
    # print(f"Columns in borrowers table: {column_names}")  # Debugging line
    # Check required columns
    assert "id" in column_names
    assert "name" in column_names
    assert "email" in column_names

    conn = sqlite3.connect(temp_db)
    cursor = conn.cursor()
    cursor.execute(f"PRAGMA index_list(borrowers)")
    indexes = cursor.fetchall()
    print(f"Indexes in borrowers table: {indexes}")  # Debugging line

    # Verify email uniqueness
    # Find the unique index
    unique_index = next((idx for idx in indexes if idx[2] == 1), None)  # Check if the index is unique
    assert unique_index, "No UNIQUE index found on the borrowers table"

    # Get the columns in the unique index
    cursor.execute(f"PRAGMA index_info({unique_index[1]})")
    index_columns = cursor.fetchall()
    print(f"Columns in unique index {unique_index[1]}: {index_columns}")  # Debugging line

    # Check if the email column is part of the unique index
    email_in_unique_index = any(col[2] == "email" for col in index_columns)
    conn.close()

    assert email_in_unique_index, "The email column does not have a UNIQUE constraint"

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

def test_idempotent_initialization(temp_db):
    """Ensure init_db can be safely called multiple times."""
    init_db(temp_db)  # Call init_db again on the same database
    tables = ["books", "borrowers", "borrowed_books"]
    conn = sqlite3.connect(temp_db)
    cursor = conn.cursor()
    for table in tables:
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
    conn.close()

