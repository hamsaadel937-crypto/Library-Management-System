"""
library_service.py
"""

from datetime import date
from functools import reduce

from models import (
    Book,
    BorrowRecord,
    BookSchema,
    BookNotFoundError,
    DuplicateBookError,
    InsufficientCopiesError
)

from storage import StorageManager


class LibraryManager:

    def __init__(self):

        self.books, self.records = StorageManager.load_data()

    def save(self):

        StorageManager.save_data(self.books, self.records)

    # ================= Add Book =================

    def add_book(self, book_id, title, author, category, copies):

        if book_id in self.books:
            raise DuplicateBookError("Book already exists")

        if copies < 0:
            raise ValueError("Copies cannot be negative")

        BookSchema(
            book_id=book_id,
            title=title,
            author=author,
            category=category,
            available_copies=copies
        )

        book = Book(book_id, title, author, category, copies)

        self.books[book_id] = book

        self.save()

    # ================= Remove Book =================

    def remove_book(self, book_id):

        if book_id not in self.books:
            raise BookNotFoundError("Book not found")

        del self.books[book_id]

        self.save()

    # ================= Search By ID =================

    def search_by_id(self, book_id):

        if book_id not in self.books:
            raise BookNotFoundError("Book not found")

        return self.books[book_id]

    # ================= Search By Title =================

    def search_by_title(self, title):

        result = []

        for book in self.books.values():

            if title.lower() in book.title.lower():

                result.append(book)

        return sorted(result, key=lambda book: book.title)

    # ================= Search By Author =================

    def search_by_author(self, author):

        result = []

        for book in self.books.values():

            if author.lower() in book.author.lower():

                result.append(book)

        return result

    # ================= Borrow Book =================

    def borrow_book(self, book_id, borrower):

        book = self.search_by_id(book_id)

        if book.available_copies == 0:
            raise InsufficientCopiesError("No copies available")

        book.available_copies -= 1

        record = BorrowRecord(

            "R" + str(len(self.records) + 1),

            book_id,

            borrower,

            str(date.today())

        )

        self.records.append(record)

        self.save()

    # ================= Return Book =================

    def return_book(self, book_id, borrower):

        for record in self.records:

            if record.book_id == book_id and record.borrower_name == borrower:

                self.books[book_id].available_copies += 1

                self.records.remove(record)

                self.save()

                return

        raise BookNotFoundError("Borrow record not found")

    # ================= Display =================

    def get_all_books(self):

        return sorted(self.books.values(), key=lambda book: book.title)

    def get_available_books(self):

        result = []

        for book in self.books.values():

            if book.available_copies > 0:

                result.append(book)

        return result

    # ================= Bonus =================

    # map()

    def upper_titles(self):

        return list(

            map(

                lambda book: book.title.upper(),

                self.books.values()

            )

        )

    # filter()

    def programming_books(self):

        return list(

            filter(

                lambda book: book.category == "Programming",

                self.books.values()

            )

        )

    # reduce()

    def total_copies(self):

        return reduce(

            lambda total, book: total + book.available_copies,

            self.books.values(),

            0

        )

    # zip()

    def catalog(self):

        titles = []
        authors = []

        for book in self.books.values():

            titles.append(book.title)
            authors.append(book.author)

        return list(zip(titles, authors))