"""
models.py
"""

from dataclasses import dataclass
from pydantic import BaseModel


# ================= Custom Exceptions =================

class LibraryError(Exception):
    pass


class BookNotFoundError(LibraryError):
    pass


class DuplicateBookError(LibraryError):
    pass


class InsufficientCopiesError(LibraryError):
    pass


# ================= Pydantic =================

class BookSchema(BaseModel):

    book_id: str
    title: str
    author: str
    category: str
    available_copies: int


# ================= Book =================

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


# ================= Borrow Record =================

@dataclass
class BorrowRecord:

    record_id: str
    book_id: str
    borrower_name: str
    borrow_date: str

    def to_dict(self):

        return {
            "record_id": self.record_id,
            "book_id": self.book_id,
            "borrower_name": self.borrower_name,
            "borrow_date": self.borrow_date
        }

    def __repr__(self):

        return f"{self.record_id} - {self.borrower_name}"