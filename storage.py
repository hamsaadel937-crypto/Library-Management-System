"""
storage.py
"""

import json
import csv
import logging
from pathlib import Path

from models import Book, BorrowRecord


# الملفات
books_file = Path("books.json")
records_file = Path("borrowed_books.json")
csv_file = Path("books.csv")

# Logging
logging.basicConfig(filename="library.log")


class StorageManager:

    @staticmethod
    def save_data(books, records):

        books_list = []

        for book in books.values():
            books_list.append(book.to_dict())

        records_list = []

        for record in records:
            records_list.append(record.to_dict())

        with open(books_file, "w") as file:
            json.dump(books_list, file, indent=4)

        with open(records_file, "w") as file:
            json.dump(records_list, file, indent=4)

        logging.info("Data Saved")


    @staticmethod
    def load_data():

        books = {}
        records = []

        # تحميل الكتب
        if books_file.exists():

            with open(books_file, "r") as file:

                if file.read() != "":

                    file.seek(0)

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

        # تحميل السجلات
        if records_file.exists():

            with open(records_file, "r") as file:

                if file.read() != "":

                    file.seek(0)

                    data = json.load(file)

                    for item in data:

                        record = BorrowRecord(
                            item["record_id"],
                            item["book_id"],
                            item["borrower_name"],
                            item["borrow_date"]
                        )

                        records.append(record)

        logging.info("Data Loaded")

        return books, records


    @staticmethod
    def export_csv(books):

        with open(csv_file, "w", newline="") as file:

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

        logging.info("CSV Exported")