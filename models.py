"""
models.py
"""

from dataclasses import dataclass
from pydantic import BaseModel


# =========================================================
# CUSTOM EXCEPTIONS
# =========================================================

class LibraryError(Exception):
    pass


class BookNotFoundError(LibraryError):
    pass


class DuplicateBookError(LibraryError):
    pass


class InsufficientCopiesError(LibraryError):
    pass


class UnauthorizedError(LibraryError):
    pass


class UserNotFoundError(LibraryError):
    pass


class DuplicateUserError(LibraryError):
    pass


class BorrowRecordNotFoundError(LibraryError):
    pass


# =========================================================
# PYDANTIC BOOK VALIDATION
# =========================================================

class BookSchema(BaseModel):

    book_id: str
    title: str
    author: str
    category: str
    available_copies: int


# =========================================================
# PYDANTIC USER VALIDATION
# =========================================================

class UserSchema(BaseModel):

    username: str
    password: str
    full_name: str


# =========================================================
# BOOK
# =========================================================

@dataclass
class Book:

    book_id: str
    title: str
    author: str
    category: str
    available_copies: int

    def to_dict(self):

        return {
            "book_id": self.book_id,
            "title": self.title,
            "author": self.author,
            "category": self.category,
            "available_copies": self.available_copies
        }

    def __repr__(self):

        return f"{self.book_id} - {self.title}"


# =========================================================
# USER
# =========================================================

@dataclass
class User:

    username: str
    password: str
    full_name: str

    def to_dict(self):

        return {
            "username": self.username,
            "password": self.password,
            "full_name": self.full_name
        }

    def __repr__(self):

        return f"{self.username} - {self.full_name}"


# =========================================================
# BORROW RECORD
# =========================================================

@dataclass
class BorrowRecord:

    record_id: str
    book_id: str
    borrower_name: str
    username: str
    borrow_date: str

    def to_dict(self):

        return {
            "record_id": self.record_id,
            "book_id": self.book_id,
            "borrower_name": self.borrower_name,
            "username": self.username,
            "borrow_date": self.borrow_date
        }

    def __repr__(self):

        return f"{self.record_id} - {self.borrower_name}"
