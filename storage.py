import json
import csv
import logging
import hashlib
import hmac
from pathlib import Path

from models import Book, User, BorrowRecord


BASE_DIR = Path(__file__).resolve().parent

books_file = BASE_DIR / "books.json"
records_file = BASE_DIR / "borrowed_books.json"
users_file = BASE_DIR / "users.json"
owner_file = BASE_DIR / "owner_profile.json"
csv_file = BASE_DIR / "books.csv"


DEFAULT_OWNER_USERNAME = "library"
DEFAULT_OWNER_PASSWORD = "lib123456"
DEFAULT_OWNER_NAME = "Library Owner"


logging.basicConfig(
    filename=BASE_DIR / "library.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)


# ============================================================
# PASSWORDS
# ============================================================

def hash_password(password):
    return hashlib.sha256(
        str(password).encode("utf-8")
    ).hexdigest()


def is_hashed(password):
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

    if not stored_password:
        return False

    if is_hashed(stored_password):

        return hmac.compare_digest(
            hash_password(password),
            stored_password
        )

    # Backward compatibility
    return str(password) == str(stored_password)


# ============================================================
# STORAGE MANAGER
# ============================================================

class StorageManager:

    @staticmethod
    def save_data(books, records):

        books_list = [
            book.to_dict()
            for book in books.values()
        ]

        records_list = [
            record.to_dict()
            for record in records
        ]

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

    @staticmethod
    def load_data():

        books = {}
        records = []

        # Books
        if books_file.exists():

            try:

                with open(
                    books_file,
                    "r",
                    encoding="utf-8"
                ) as file:

                    data = json.load(file)

                for item in data:

                    try:

                        book = Book(
                            book_id=str(
                                item.get(
                                    "book_id",
                                    ""
                                )
                            ),
                            title=str(
                                item.get(
                                    "title",
                                    "Unknown"
                                )
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
                        TypeError,
                        ValueError
                    ):
                        continue

            except (
                json.JSONDecodeError,
                OSError
            ):

                logging.error(
                    "Could not load books.json."
                )

        # Borrowing records
        if records_file.exists():

            try:

                with open(
                    records_file,
                    "r",
                    encoding="utf-8"
                ) as file:

                    data = json.load(file)

                for item in data:

                    try:

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

                    except Exception:
                        continue

            except (
                json.JSONDecodeError,
                OSError
            ):

                logging.error(
                    "Could not load borrowed_books.json."
                )

        return books, records

    # ========================================================
    # USERS
    # ========================================================

    @staticmethod
    def save_users(users):

        users_list = [
            user.to_dict()
            for user in users.values()
        ]

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

    @staticmethod
    def load_users():

        users = {}

        if not users_file.exists():
            return users

        try:

            with open(
                users_file,
                "r",
                encoding="utf-8"
            ) as file:

                data = json.load(file)

            for item in data:

                username = str(
                    item.get(
                        "username",
                        ""
                    )
                ).strip()

                if not username:
                    continue

                user = User(
                    username=username,
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

                users[username] = user

        except (
            json.JSONDecodeError,
            OSError
        ):

            logging.error(
                "Could not load users.json."
            )

        return users

    # ========================================================
    # OWNER
    # ========================================================

    @staticmethod
    def save_owner_profile(owner):

        owner_to_save = dict(owner)

        if (
            "password" in owner_to_save
            and owner_to_save["password"]
            and not is_hashed(
                owner_to_save["password"]
            )
        ):

            owner_to_save["password"] = (
                hash_password(
                    owner_to_save["password"]
                )
            )

        with open(
            owner_file,
            "w",
            encoding="utf-8"
        ) as file:

            json.dump(
                owner_to_save,
                file,
                indent=4,
                ensure_ascii=False
            )

        logging.info(
            "Owner profile saved."
        )

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

                owner.setdefault(
                    "username",
                    DEFAULT_OWNER_USERNAME
                )

                owner.setdefault(
                    "full_name",
                    DEFAULT_OWNER_NAME
                )

                owner.setdefault(
                    "password",
                    hash_password(
                        DEFAULT_OWNER_PASSWORD
                    )
                )

                # Migrate old plaintext password
                if not is_hashed(
                    owner["password"]
                ):

                    owner["password"] = (
                        hash_password(
                            owner["password"]
                        )
                    )

                    StorageManager.save_owner_profile(
                        owner
                    )

                return owner

            except (
                json.JSONDecodeError,
                OSError
            ):

                logging.error(
                    "Could not load owner profile."
                )

        owner = {
            "username": DEFAULT_OWNER_USERNAME,
            "password": hash_password(
                DEFAULT_OWNER_PASSWORD
            ),
            "full_name": DEFAULT_OWNER_NAME
        }

        StorageManager.save_owner_profile(
            owner
        )

        return owner

    # ========================================================
    # CSV EXPORT
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