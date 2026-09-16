"""
library_service.py

Business logic for the Library Management System.
"""

from datetime import date

from models import (
    Book,
    User,
    BorrowRecord,
    BookSchema,
    UserSchema,
    LibraryError,
    BookNotFoundError,
    DuplicateBookError,
    InsufficientCopiesError,
    UnauthorizedError,
    UserNotFoundError,
    DuplicateUserError,
    BorrowRecordNotFoundError
)

from storage import (
    StorageManager,
    hash_password,
    verify_password
)


class LibraryManager:

    # =====================================================
    # INITIALIZATION
    # =====================================================

    def __init__(self):

        self.books, self.records = (
            StorageManager.load_data()
        )

        self.users = (
            StorageManager.load_users()
        )

        self.owner = (
            StorageManager.load_owner_profile()
        )

    # =====================================================
    # SAVE EVERYTHING
    # =====================================================

    def save(self):

        StorageManager.save_data(
            self.books,
            self.records
        )

        StorageManager.save_users(
            self.users
        )

        StorageManager.save_owner_profile(
            self.owner
        )

    # =====================================================
    # IMPORT BOOKS FROM CSV
    # =====================================================

    def import_books_from_csv(
        self,
        csv_path,
        overwrite=False
    ):

        self.books = (
            StorageManager.import_books_from_transactions(
                csv_path,
                overwrite=overwrite
            )
        )

        # Reload records
        _, self.records = (
            StorageManager.load_data()
        )

        return self.books

    # =====================================================
    # OWNER LOGIN
    # =====================================================

    def login_owner(
        self,
        username,
        password
    ):

        username = str(
            username
        ).strip()

        password = str(
            password
        )

        if (
            username.lower()
            != self.owner["username"].lower()
        ):

            raise UnauthorizedError(
                "Invalid owner username or password."
            )

        if not verify_password(
            password,
            self.owner["password"]
        ):

            raise UnauthorizedError(
                "Invalid owner username or password."
            )

        # -----------------------------------------------
        # Migrate old plain password if necessary
        # -----------------------------------------------

        if self.owner["password"] != hash_password(
            password
        ):

            self.owner["password"] = (
                hash_password(password)
            )

            StorageManager.save_owner_profile(
                self.owner
            )

        return self.owner

    # =====================================================
    # USER REGISTER
    # =====================================================

    def register_user(
        self,
        username,
        password,
        full_name
    ):

        username = str(
            username
        ).strip()

        password = str(
            password
        )

        full_name = str(
            full_name
        ).strip()

        if not username:
            raise LibraryError(
                "Username cannot be empty."
            )

        if not password:
            raise LibraryError(
                "Password cannot be empty."
            )

        if not full_name:
            raise LibraryError(
                "Full name cannot be empty."
            )

        if len(password) < 6:

            raise LibraryError(
                "Password must contain at least 6 characters."
            )

        # Validate user
        UserSchema(
            username=username,
            password=password,
            full_name=full_name
        )

        # Owner username
        if (
            username.lower()
            == self.owner["username"].lower()
        ):

            raise DuplicateUserError(
                "This username is reserved for the owner."
            )

        # Existing users
        for existing_username in self.users:

            if (
                existing_username.lower()
                == username.lower()
            ):

                raise DuplicateUserError(
                    "Username already exists."
                )

        # Hash password before storing
        hashed_password = hash_password(
            password
        )

        user = User(
            username=username,
            password=hashed_password,
            full_name=full_name
        )

        self.users[username] = user

        StorageManager.save_users(
            self.users
        )

        return user

    # =====================================================
    # USER LOGIN
    # =====================================================

    def login_user(
        self,
        username,
        password
    ):

        username = str(
            username
        ).strip()

        password = str(
            password
        )

        # Case-insensitive username search
        actual_username = None

        for existing_username in self.users:

            if (
                existing_username.lower()
                == username.lower()
            ):

                actual_username = (
                    existing_username
                )

                break

        if actual_username is None:

            raise UserNotFoundError(
                "User not found."
            )

        user = self.users[
            actual_username
        ]

        if not verify_password(
            password,
            user.password
        ):

            raise UnauthorizedError(
                "Invalid password."
            )

        # Migrate old plain password
        if user.password != hash_password(
            password
        ):

            user.password = (
                hash_password(password)
            )

            StorageManager.save_users(
                self.users
            )

        return user

    # =====================================================
    # OWNER PROFILE
    # =====================================================

    def update_owner_profile(
        self,
        current_password,
        new_username,
        new_full_name,
        new_password=None
    ):

        current_password = str(
            current_password
        )

        new_username = str(
            new_username
        ).strip()

        new_full_name = str(
            new_full_name
        ).strip()

        if not verify_password(
            current_password,
            self.owner["password"]
        ):

            raise UnauthorizedError(
                "Current password is incorrect."
            )

        if not new_username:

            raise LibraryError(
                "Username cannot be empty."
            )

        if not new_full_name:

            raise LibraryError(
                "Full name cannot be empty."
            )

        # Check users
        for username in self.users:

            if (
                username.lower()
                == new_username.lower()
            ):

                raise DuplicateUserError(
                    "This username is already used by a user."
                )

        self.owner["username"] = (
            new_username
        )

        self.owner["full_name"] = (
            new_full_name
        )

        if new_password:

            new_password = str(
                new_password
            )

            if len(new_password) < 6:

                raise LibraryError(
                    "New password must contain at least 6 characters."
                )

            self.owner["password"] = (
                hash_password(new_password)
            )

        StorageManager.save_owner_profile(
            self.owner
        )

        return self.owner

    # =====================================================
    # USER PROFILE
    # =====================================================

    def update_user_profile(
        self,
        username,
        current_password,
        new_username,
        new_full_name,
        new_password=None
    ):

        if username not in self.users:

            raise UserNotFoundError(
                "User not found."
            )

        user = self.users[
            username
        ]

        if not verify_password(
            current_password,
            user.password
        ):

            raise UnauthorizedError(
                "Current password is incorrect."
            )

        new_username = str(
            new_username
        ).strip()

        new_full_name = str(
            new_full_name
        ).strip()

        if not new_username:

            raise LibraryError(
                "Username cannot be empty."
            )

        if not new_full_name:

            raise LibraryError(
                "Full name cannot be empty."
            )

        if (
            new_username.lower()
            == self.owner["username"].lower()
        ):

            raise DuplicateUserError(
                "This username is used by the owner."
            )

        # Check other users
        for existing_username in self.users:

            if (
                existing_username != username
                and
                existing_username.lower()
                == new_username.lower()
            ):

                raise DuplicateUserError(
                    "This username is already used."
                )

        # Password
        if new_password:

            new_password = str(
                new_password
            )

            if len(new_password) < 6:

                raise LibraryError(
                    "New password must contain at least 6 characters."
                )

            updated_password = (
                hash_password(new_password)
            )

        else:

            updated_password = (
                user.password
            )

        updated_user = User(
            username=new_username,
            password=updated_password,
            full_name=new_full_name
        )

        # Keep borrowed records connected
        # to the new username.
        for record in self.records:

            if record.username == username:

                record.username = (
                    new_username
                )

        del self.users[
            username
        ]

        self.users[
            new_username
        ] = updated_user

        self.save()

        return updated_user

    # =====================================================
    # ADD BOOK
    # =====================================================

    def add_book(
        self,
        book_id,
        title,
        author,
        category,
        copies
    ):

        book_id = str(
            book_id
        ).strip()

        title = str(
            title
        ).strip()

        author = str(
            author
        ).strip()

        category = str(
            category
        ).strip()

        try:

            copies = int(copies)

        except (
            ValueError,
            TypeError
        ):

            raise ValueError(
                "Copies must be a number."
            )

        if not book_id:

            raise LibraryError(
                "Book ID cannot be empty."
            )

        if not title:

            raise LibraryError(
                "Book title cannot be empty."
            )

        if book_id in self.books:

            raise DuplicateBookError(
                "Book ID already exists."
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

        self.books[
            book_id
        ] = book

        self.save()

        return book

    # =====================================================
    # UPDATE BOOK
    # =====================================================

    def update_book(
        self,
        book_id,
        title,
        author,
        category,
        copies
    ):

        book_id = str(
            book_id
        ).strip()

        if book_id not in self.books:

            raise BookNotFoundError(
                "Book not found."
            )

        try:

            copies = int(copies)

        except (
            ValueError,
            TypeError
        ):

            raise ValueError(
                "Copies must be a number."
            )

        if copies < 0:

            raise ValueError(
                "Copies cannot be negative."
            )

        title = str(
            title
        ).strip()

        author = str(
            author
        ).strip()

        category = str(
            category
        ).strip()

        if not title:

            raise LibraryError(
                "Title cannot be empty."
            )

        BookSchema(
            book_id=book_id,
            title=title,
            author=author,
            category=category,
            available_copies=copies
        )

        book = self.books[
            book_id
        ]

        book.title = title
        book.author = author
        book.category = category
        book.available_copies = copies

        self.save()

        return book

    # =====================================================
    # REMOVE BOOK
    # =====================================================

    def remove_book(
        self,
        book_id
    ):

        book_id = str(
            book_id
        ).strip()

        if book_id not in self.books:

            raise BookNotFoundError(
                "Book not found."
            )

        # Don't delete a book currently borrowed
        for record in self.records:

            if record.book_id == book_id:

                raise LibraryError(
                    "Cannot delete this book because it is currently borrowed."
                )

        del self.books[
            book_id
        ]

        self.save()

    # =====================================================
    # SEARCH BY ID
    # =====================================================

    def search_by_id(
        self,
        book_id
    ):

        book_id = str(
            book_id
        ).strip()

        if book_id not in self.books:

            raise BookNotFoundError(
                "Book not found."
            )

        return self.books[
            book_id
        ]

    # =====================================================
    # SEARCH BY TITLE
    # =====================================================

    def search_by_title(
        self,
        title
    ):

        title = str(
            title
        ).lower().strip()

        result = [
            book
            for book in self.books.values()
            if title in book.title.lower()
        ]

        return sorted(
            result,
            key=lambda book:
                book.title.lower()
        )

    # =====================================================
    # SEARCH BY AUTHOR
    # =====================================================

    def search_by_author(
        self,
        author
    ):

        author = str(
            author
        ).lower().strip()

        result = [
            book
            for book in self.books.values()
            if author in book.author.lower()
        ]

        return sorted(
            result,
            key=lambda book:
                book.title.lower()
        )

    # =====================================================
    # GENERAL SEARCH
    # =====================================================

    def search_books(
        self,
        query
    ):

        query = str(
            query
        ).lower().strip()

        result = []

        for book in self.books.values():

            if (
                query in book.book_id.lower()
                or query in book.title.lower()
                or query in book.author.lower()
                or query in book.category.lower()
            ):

                result.append(book)

        return sorted(
            result,
            key=lambda book:
                book.title.lower()
        )

    # =====================================================
    # BORROW BOOK
    # =====================================================

    def borrow_book(
        self,
        book_id,
        borrower_name,
        username=""
    ):

        book = self.search_by_id(
            book_id
        )

        username = str(
            username
        ).strip()

        borrower_name = str(
            borrower_name
        ).strip()

        if book.available_copies <= 0:

            raise InsufficientCopiesError(
                "No available copies for this book."
            )

        # Prevent duplicate active borrowing
        for record in self.records:

            if (
                record.book_id == book_id
                and record.username == username
            ):

                raise LibraryError(
                    "You already borrowed this book."
                )

        book.available_copies -= 1

        # Generate unique record ID
        record_number = (
            len(self.records) + 1
        )

        existing_ids = {
            record.record_id
            for record in self.records
        }

        record_id = (
            f"R{record_number:04d}"
        )

        while record_id in existing_ids:

            record_number += 1

            record_id = (
                f"R{record_number:04d}"
            )

        record = BorrowRecord(
            record_id=record_id,
            book_id=book_id,
            borrower_name=borrower_name,
            username=username,
            borrow_date=str(
                date.today()
            )
        )

        self.records.append(
            record
        )

        self.save()

        return record

    # =====================================================
    # RETURN BOOK
    # =====================================================

    def return_book(
        self,
        book_id,
        borrower_name=None,
        username=None
    ):

        book_id = str(
            book_id
        ).strip()

        for record in self.records:

            same_book = (
                record.book_id
                == book_id
            )

            same_user = True

            if username:

                same_user = (
                    record.username
                    == username
                )

            elif borrower_name:

                same_user = (
                    record.borrower_name
                    == borrower_name
                )

            if same_book and same_user:

                if book_id in self.books:

                    self.books[
                        book_id
                    ].available_copies += 1

                self.records.remove(
                    record
                )

                self.save()

                return record

        raise BorrowRecordNotFoundError(
            "Borrow record not found."
        )

    # =====================================================
    # GET ALL BOOKS
    # =====================================================

    def get_all_books(self):

        return sorted(
            self.books.values(),
            key=lambda book:
                book.title.lower()
        )

    # =====================================================
    # AVAILABLE BOOKS
    # =====================================================

    def get_available_books(self):

        return [
            book
            for book in self.books.values()
            if book.available_copies > 0
        ]

    # =====================================================
    # USER BORROWED BOOKS
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
    # TOTAL COPIES
    # =====================================================

    def total_copies(self):

        return sum(
            book.available_copies
            for book in self.books.values()
        )

    # =====================================================
    # TOTAL BOOK TITLES
    # =====================================================

    def total_books(self):

        return len(
            self.books
        )

    # =====================================================
    # TOTAL BORROWED
    # =====================================================

    def total_borrowed(self):

        return len(
            self.records
        )

    # =====================================================
    # BONUS - UPPER TITLES
    # =====================================================

    def upper_titles(self):

        return [
            book.title.upper()
            for book in self.books.values()
        ]

    # =====================================================
    # BONUS - PROGRAMMING BOOKS
    # =====================================================

    def programming_books(self):

        return [
            book
            for book in self.books.values()
            if (
                "program"
                in book.category.lower()
            )
        ]

    # =====================================================
    # BONUS - CATALOG
    # =====================================================

    def catalog(self):

        return {
            book.book_id: book.title
            for book in self.books.values()
        }

    # =====================================================
    # STATISTICAL ANALYSIS
    # =====================================================

    def statistical_analysis(self):

        books = self.get_all_books()

        print(
            "\n===== Statistical Analysis ====="
        )

        print(
            "Total Book Titles:",
            len(books)
        )

        print(
            "Total Available Copies:",
            self.total_copies()
        )

        print(
            "Total Borrowed Records:",
            len(self.records)
        )

        if books:

            average = (
                self.total_copies()
                / len(books)
            )

            print(
                "Average Available Copies Per Book:",
                round(average, 2)
            )

        print(
            "================================"
        )