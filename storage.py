"""
storage.py
"""

import json
import csv
import logging
from pathlib import Path

from models import Book, User, BorrowRecord


# =========================================================
# FILES
# =========================================================

books_file = Path("books.json")
records_file = Path("borrowed_books.json")
users_file = Path("users.json")
csv_file = Path("books.csv")


# =========================================================
# LOGGING
# =========================================================

logging.basicConfig(
    filename="library.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)


# =========================================================
# STORAGE MANAGER
# =========================================================

class StorageManager:

    # =====================================================
    # SAVE DATA
    # =====================================================

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

        logging.info("Books and borrowing records saved")


    # =====================================================
    # LOAD BOOKS AND RECORDS
    # =====================================================

    @staticmethod
    def load_data():

        books = {}
        records = []

        # -------------------------------------------------
        # LOAD BOOKS
        # -------------------------------------------------

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
                            item["book_id"],
                            item["title"],
                            item["author"],
                            item["category"],
                            item["available_copies"]
                        )

                        books[book.book_id] = book

            except (json.JSONDecodeError, KeyError):

                logging.error("Could not load books.json")


        # -------------------------------------------------
        # LOAD BORROW RECORDS
        # -------------------------------------------------

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
                            item["record_id"],
                            item["book_id"],
                            item["borrower_name"],
                            item.get("username", ""),
                            item["borrow_date"]
                        )

                        records.append(record)

            except (json.JSONDecodeError, KeyError):

                logging.error(
                    "Could not load borrowed_books.json"
                )

        logging.info("Data loaded")

        return books, records


    # =====================================================
    # SAVE USERS
    # =====================================================

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

        logging.info("Users saved")


    # =====================================================
    # LOAD USERS
    # =====================================================

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
                            item["username"],
                            item["password"],
                            item["full_name"]
                        )

                        users[user.username] = user

            except (json.JSONDecodeError, KeyError):

                logging.error(
                    "Could not load users.json"
                )

        return users


    # =====================================================
    # EXPORT CSV
    # =====================================================

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
                "Copies"
            ])

            for book in books:

                writer.writerow([
                    book.book_id,
                    book.title,
                    book.author,
                    book.category,
                    book.available_copies
                ])

        logging.info("CSV exported")
