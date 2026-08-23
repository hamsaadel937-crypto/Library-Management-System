"""
library_service.py
"""

from datetime import date
from functools import reduce
import math
import random

import numpy as np
from scipy import stats
import matplotlib.pyplot as plt

from models import (
    Book,
    User,
    BorrowRecord,
    BookSchema,
    UserSchema,
    BookNotFoundError,
    DuplicateBookError,
    InsufficientCopiesError,
    UnauthorizedError,
    UserNotFoundError,
    DuplicateUserError,
    BorrowRecordNotFoundError
)

from storage import StorageManager


# =========================================================
# LIBRARY MANAGER
# =========================================================

class LibraryManager:

    def __init__(self):

        self.books, self.records = StorageManager.load_data()

        self.users = StorageManager.load_users()


    # =====================================================
    # SAVE
    # =====================================================

    def save(self):

        StorageManager.save_data(
            self.books,
            self.records
        )

        StorageManager.save_users(
            self.users
        )


    # =====================================================
    # USER MANAGEMENT
    # =====================================================

    def register_user(
        self,
        username,
        password,
        full_name
    ):

        if username in self.users:

            raise DuplicateUserError(
                "Username already exists."
            )

        if not username.strip():

            raise ValueError(
                "Username cannot be empty."
            )

        if not password.strip():

            raise ValueError(
                "Password cannot be empty."
            )

        if not full_name.strip():

            raise ValueError(
                "Full name cannot be empty."
            )

        UserSchema(
            username=username,
            password=password,
            full_name=full_name
        )

        user = User(
            username,
            password,
            full_name
        )

        self.users[username] = user

        self.save()


    # =====================================================
    # USER LOGIN
    # =====================================================

    def login_user(
        self,
        username,
        password
    ):

        if username not in self.users:

            raise UserNotFoundError(
                "User not found."
            )

        user = self.users[username]

        if user.password != password:

            raise UnauthorizedError(
                "Incorrect password."
            )

        return user


    # =====================================================
    # ADD BOOK
    # OWNER ONLY
    # =====================================================

    def add_book(
        self,
        book_id,
        title,
        author,
        category,
        copies,
        role="user"
    ):

        if role != "owner":

            raise UnauthorizedError(
                "Only the library owner can add books."
            )

        if book_id in self.books:

            raise DuplicateBookError(
                "Book already exists."
            )

        if copies < 0:

            raise ValueError(
                "Copies cannot be negative."
            )

        BookSchema(
            book_id=book_id,
            title=title,
            author=author,
            category=category,
            available_copies=copies
        )

        book = Book(
            book_id,
            title,
            author,
            category,
            copies
        )

        self.books[book_id] = book

        self.save()


    # =====================================================
    # REMOVE BOOK
    # OWNER ONLY
    # =====================================================

    def remove_book(
        self,
        book_id,
        role="user"
    ):

        if role != "owner":

            raise UnauthorizedError(
                "Only the library owner can remove books."
            )

        if book_id not in self.books:

            raise BookNotFoundError(
                "Book not found."
            )

        # Don't remove a book that is currently borrowed
        for record in self.records:

            if record.book_id == book_id:

                raise LibraryError(
                    "Cannot remove a borrowed book."
                )

        del self.books[book_id]

        self.save()


    # =====================================================
    # UPDATE BOOK
    # OWNER ONLY
    # =====================================================

    def update_book(
        self,
        book_id,
        title,
        author,
        category,
        copies,
        role="user"
    ):

        if role != "owner":

            raise UnauthorizedError(
                "Only the library owner can update books."
            )

        if book_id not in self.books:

            raise BookNotFoundError(
                "Book not found."
            )

        if copies < 0:

            raise ValueError(
                "Copies cannot be negative."
            )

        book = self.books[book_id]

        book.title = title
        book.author = author
        book.category = category
        book.available_copies = copies

        self.save()


    # =====================================================
    # SEARCH BY ID
    # =====================================================

    def search_by_id(self, book_id):

        if book_id not in self.books:

            raise BookNotFoundError(
                "Book not found."
            )

        return self.books[book_id]


    # =====================================================
    # SEARCH BY TITLE
    # =====================================================

    def search_by_title(self, title):

        result = []

        for book in self.books.values():

            if title.lower() in book.title.lower():

                result.append(book)

        return sorted(
            result,
            key=lambda book: book.title
        )


    # =====================================================
    # SEARCH BY AUTHOR
    # =====================================================

    def search_by_author(self, author):

        result = []

        for book in self.books.values():

            if author.lower() in book.author.lower():

                result.append(book)

        return result


    # =====================================================
    # BORROW BOOK
    # USER ONLY
    # =====================================================

    def borrow_book(
        self,
        book_id,
        borrower,
        username,
        role="user"
    ):

        if role != "user":

            raise UnauthorizedError(
                "Only users can borrow books."
            )

        book = self.search_by_id(book_id)

        if book.available_copies <= 0:

            raise InsufficientCopiesError(
                "No copies available."
            )

        # Prevent same user from borrowing
        # the same book twice
        for record in self.records:

            if (
                record.book_id == book_id
                and record.username == username
            ):

                raise LibraryError(
                    "You already borrowed this book."
                )

        book.available_copies -= 1

        record_id = (
            "R" +
            str(len(self.records) + 1)
        )

        record = BorrowRecord(
            record_id,
            book_id,
            borrower,
            username,
            str(date.today())
        )

        self.records.append(record)

        self.save()


    # =====================================================
    # RETURN BOOK
    # USER ONLY
    # =====================================================

    def return_book(
        self,
        book_id,
        username,
        role="user"
    ):

        if role != "user":

            raise UnauthorizedError(
                "Only users can return books."
            )

        for record in self.records:

            if (
                record.book_id == book_id
                and record.username == username
            ):

                self.books[book_id].available_copies += 1

                self.records.remove(record)

                self.save()

                return

        raise BorrowRecordNotFoundError(
            "You do not have this book borrowed."
        )


    # =====================================================
    # USER'S BORROWED BOOKS
    # =====================================================

    def get_user_borrowed_books(
        self,
        username
    ):

        return [
            record
            for record in self.records
            if record.username == username
        ]


    # =====================================================
    # ALL BORROWED BOOKS
    # OWNER ONLY
    # =====================================================

    def get_all_borrowed_books(
        self,
        role="user"
    ):

        if role != "owner":

            raise UnauthorizedError(
                "Only the owner can view all borrowing records."
            )

        return self.records


    # =====================================================
    # DISPLAY
    # =====================================================

    def get_all_books(self):

        return sorted(
            self.books.values(),
            key=lambda book: book.title
        )


    def get_available_books(self):

        result = []

        for book in self.books.values():

            if book.available_copies > 0:

                result.append(book)

        return sorted(
            result,
            key=lambda book: book.title
        )


    # =====================================================
    # BONUS - MAP
    # =====================================================

    def upper_titles(self):

        return list(
            map(
                lambda book: book.title.upper(),
                self.books.values()
            )
        )


    # =====================================================
    # BONUS - FILTER
    # =====================================================

    def programming_books(self):

        return list(
            filter(
                lambda book:
                book.category.lower() == "programming",
                self.books.values()
            )
        )


    # =====================================================
    # BONUS - REDUCE
    # =====================================================

    def total_copies(self):

        return reduce(
            lambda total, book:
            total + book.available_copies,
            self.books.values(),
            0
        )


    # =====================================================
    # BONUS - ZIP
    # =====================================================

    def catalog(self):

        titles = []
        authors = []

        for book in self.books.values():

            titles.append(book.title)
            authors.append(book.author)

        return list(
            zip(
                titles,
                authors
            )
        )


    # =====================================================
    # STATISTICAL ANALYSIS
    # =====================================================

    def get_statistical_data(self):

        if len(self.books) == 0:

            return None

        values = np.array([
            book.available_copies
            for book in self.books.values()
        ])

        mean = np.mean(values)

        median = np.median(values)

        mode = stats.mode(
            values,
            keepdims=True
        ).mode[0]

        data_range = (
            np.max(values) -
            np.min(values)
        )

        variance = np.var(values)

        standard_deviation = np.std(values)

        q1 = np.percentile(
            values,
            25
        )

        q2 = np.percentile(
            values,
            50
        )

        q3 = np.percentile(
            values,
            75
        )

        iqr = q3 - q1

        lower = q1 - 1.5 * iqr

        upper = q3 + 1.5 * iqr

        outliers = values[
            (values < lower) |
            (values > upper)
        ]

        skewness = stats.skew(values)

        available = sum(
            value > 0
            for value in values
        )

        probability = (
            available /
            len(values)
        )

        return {
            "values": values,
            "mean": mean,
            "median": median,
            "mode": mode,
            "range": data_range,
            "variance": variance,
            "std": standard_deviation,
            "q1": q1,
            "q2": q2,
            "q3": q3,
            "iqr": iqr,
            "lower": lower,
            "upper": upper,
            "outliers": outliers,
            "skewness": skewness,
            "probability": probability
        }
