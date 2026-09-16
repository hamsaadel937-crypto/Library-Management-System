# ============================================================
# storage.py
# Library Management System
# ============================================================

import json
import csv
import logging
import hashlib
from pathlib import Path

from models import Book, User, BorrowRecord


# ============================================================
# BASE DIRECTORY
# ============================================================

BASE_DIR = Path(__file__).resolve().parent

books_file = BASE_DIR / "books.json"
records_file = BASE_DIR / "borrowed_books.json"
users_file = BASE_DIR / "users.json"
owner_file = BASE_DIR / "owner_profile.json"
csv_file = BASE_DIR / "books.csv"


# ============================================================
# DEFAULT OWNER
# ============================================================

DEFAULT_OWNER = {
    "username": "library",
    "password": "lib123456",
    "full_name": "Library Owner"
}


# ============================================================
# LOGGING
# ============================================================

logging.basicConfig(
    filename=BASE_DIR / "library.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)


# ============================================================
# PASSWORD HELPERS
# ============================================================

def hash_password(password):
    """
    Hash password using SHA-256.
    """

    return hashlib.sha256(
        password.encode("utf-8")
    ).hexdigest()


def is_hashed(password):
    """
    Check whether a password is already SHA-256 hashed.
    """

    if not isinstance(password, str):
        return False

    return (
        len(password) == 64
        and all(
            char in "0123456789abcdef"
            for char in password.lower()
        )
    )


def verify_password(password, stored_password):
    """
    Supports both old plaintext passwords and new hashed passwords.
    """

    if not stored_password:
        return False

    # New hashed password
    if is_hashed(stored_password):
        return hash_password(password) == stored_password

    # Old plaintext password
    return password == stored_password


# ============================================================
# STORAGE MANAGER
# ============================================================

class StorageManager:

    # ========================================================
    # BOOKS + RECORDS
    # ========================================================

    @staticmethod
    def save_data(books, records):

        books_list = []

        for book in books.values():

            books_list.append(
                book.to_dict()
            )

        records_list = []

        for record in records:

            records_list.append(
                record.to_dict()
            )

        with open(
            books_file,
            "w",
            encoding="utf-8"
        ) as file:

            json.dump(
                books_list,
                file,
                indent=4,
                ensure_ascii=False
            )

        with open(
            records_file,
            "w",
            encoding="utf-8"
        ) as file:

            json.dump(
                records_list,
                file,
                indent=4,
                ensure_ascii=False
            )

        logging.info(
            "Books and borrowing records saved."
        )

    # ========================================================
    # LOAD BOOKS + RECORDS
    # ========================================================

    @staticmethod
    def load_data():

        books = {}
        records = []

        # ----------------------------------------------------
        # Books
        # ----------------------------------------------------

        if books_file.exists():

            try:

                with open(
                    books_file,
                    "r",
                    encoding="utf-8"
                ) as file:

                    data = json.load(file)

                    for item in data:

                        book = Book(
                            book_id=str(
                                item.get("book_id", "")
                            ),
                            title=str(
                                item.get("title", "")
                            ),
                            author=str(
                                item.get(
                                    "author",
                                    "Unknown"
                                )
                            ),
                            category=str(
                                item.get(
                                    "category",
                                    "Unknown"
                                )
                            ),
                            available_copies=int(
                                item.get(
                                    "available_copies",
                                    0
                                )
                            )
                        )

                        if book.book_id:
                            books[
                                book.book_id
                            ] = book

            except (
                json.JSONDecodeError,
                KeyError,
                TypeError,
                ValueError
            ):

                logging.error(
                    "Could not load books.json."
                )

        # ----------------------------------------------------
        # Borrow Records
        # ----------------------------------------------------

        if records_file.exists():

            try:

                with open(
                    records_file,
                    "r",
                    encoding="utf-8"
                ) as file:

                    data = json.load(file)

                    for item in data:

                        record = BorrowRecord(
                            record_id=str(
                                item.get(
                                    "record_id",
                                    ""
                                )
                            ),
                            book_id=str(
                                item.get(
                                    "book_id",
                                    ""
                                )
                            ),
                            borrower_name=str(
                                item.get(
                                    "borrower_name",
                                    ""
                                )
                            ),
                            username=str(
                                item.get(
                                    "username",
                                    ""
                                )
                            ),
                            borrow_date=str(
                                item.get(
                                    "borrow_date",
                                    ""
                                )
                            )
                        )

                        records.append(record)

            except (
                json.JSONDecodeError,
                KeyError,
                TypeError,
                ValueError
            ):

                logging.error(
                    "Could not load borrowed_books.json."
                )

        logging.info(
            "Books and records loaded."
        )

        return books, records

    # ========================================================
    # USERS
    # ========================================================

    @staticmethod
    def save_users(users):

        users_list = []

        for user in users.values():

            users_list.append(
                user.to_dict()
            )

        with open(
            users_file,
            "w",
            encoding="utf-8"
        ) as file:

            json.dump(
                users_list,
                file,
                indent=4,
                ensure_ascii=False
            )

        logging.info(
            "Users saved."
        )

    # ========================================================
    # LOAD USERS
    # ========================================================

    @staticmethod
    def load_users():

        users = {}

        if users_file.exists():

            try:

                with open(
                    users_file,
                    "r",
                    encoding="utf-8"
                ) as file:

                    data = json.load(file)

                    for item in data:

                        user = User(
                            username=str(
                                item.get(
                                    "username",
                                    ""
                                )
                            ),
                            password=str(
                                item.get(
                                    "password",
                                    ""
                                )
                            ),
                            full_name=str(
                                item.get(
                                    "full_name",
                                    ""
                                )
                            )
                        )

                        if user.username:

                            users[
                                user.username
                            ] = user

            except (
                json.JSONDecodeError,
                KeyError
            ):

                logging.error(
                    "Could not load users.json."
                )

        return users

    # ========================================================
    # OWNER PROFILE
    # ========================================================

    @staticmethod
    def save_owner_profile(owner):

        with open(
            owner_file,
            "w",
            encoding="utf-8"
        ) as file:

            json.dump(
                owner,
                file,
                indent=4,
                ensure_ascii=False
            )

        logging.info(
            "Owner profile saved."
        )

    # ========================================================
    # LOAD OWNER
    # ========================================================

    @staticmethod
    def load_owner_profile():

        if owner_file.exists():

            try:

                with open(
                    owner_file,
                    "r",
                    encoding="utf-8"
                ) as file:

                    owner = json.load(file)

                    return owner

            except (
                json.JSONDecodeError,
                KeyError
            ):

                logging.error(
                    "Could not load owner profile."
                )

        # ----------------------------------------------------
        # Create default owner
        # ----------------------------------------------------

        owner = dict(DEFAULT_OWNER)

        StorageManager.save_owner_profile(
            owner
        )

        return owner

    # ========================================================
    # EXPORT BOOKS TO CSV
    # ========================================================

    @staticmethod
    def export_csv(books):

        with open(
            csv_file,
            "w",
            newline="",
            encoding="utf-8-sig"
        ) as file:

            writer = csv.writer(file)

            writer.writerow([
                "Book ID",
                "Title",
                "Author",
                "Category",
                "Available Copies"
            ])

            for book in books.values():

                writer.writerow([
                    book.book_id,
                    book.title,
                    book.author,
                    book.category,
                    book.available_copies
                ])

        logging.info(
            "Books exported to CSV."
        )