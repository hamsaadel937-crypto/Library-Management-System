"""
main.py

Console version of the Library Management System.

The library books are imported from:
library_transactions.csv
"""

from pathlib import Path

from library_service import LibraryManager
from storage import StorageManager
from models import LibraryError


# =========================================================
# INITIALIZATION
# =========================================================

manager = LibraryManager()

BASE_DIR = Path(
    __file__
).resolve().parent

transactions_file = (
    BASE_DIR / "library_transactions.csv"
)


# =========================================================
# IMPORT CSV BOOKS
# =========================================================

if transactions_file.exists():

    # Import CSV books only if the library
    # does not already contain books.

    if len(manager.books) == 0:

        try:

            manager.import_books_from_csv(
                transactions_file,
                overwrite=False
            )

            print(
                "\nBooks loaded successfully "
                "from library_transactions.csv."
            )

        except Exception as e:

            print(
                "\nCould not import CSV books:"
            )

            print(e)

else:

    print(
        "\nWarning:"
        "\nlibrary_transactions.csv was not found."
        "\nPlace the file inside the project folder."
    )


# =========================================================
# MAIN MENU
# =========================================================

while True:

    print(
        "\n========================================"
    )

    print(
        "      LIBRARY MANAGEMENT SYSTEM"
    )

    print(
        "========================================"
    )

    print(
        "1. Add Book"
    )

    print(
        "2. Update Book"
    )

    print(
        "3. Remove Book"
    )

    print(
        "4. Search By ID"
    )

    print(
        "5. Search By Title"
    )

    print(
        "6. Search By Author"
    )

    print(
        "7. Search General"
    )

    print(
        "8. Borrow Book"
    )

    print(
        "9. Return Book"
    )

    print(
        "10. Display Available Books"
    )

    print(
        "11. Display All Books"
    )

    print(
        "12. Display Borrowed Books"
    )

    print(
        "13. Export Books CSV"
    )

    print(
        "14. Bonus Functions"
    )

    print(
        "15. Statistical Analysis"
    )

    print(
        "16. Reload Books From CSV"
    )

    print(
        "0. Exit"
    )

    print(
        "========================================"
    )

    choice = input(
        "Enter Choice: "
    ).strip()

    try:

        # =================================================
        # ADD BOOK
        # =================================================

        if choice == "1":

            manager.add_book(

                input(
                    "Book ID: "
                ),

                input(
                    "Title: "
                ),

                input(
                    "Author: "
                ),

                input(
                    "Category: "
                ),

                int(
                    input(
                        "Copies: "
                    )
                )

            )

            print(
                "Book Added Successfully."
            )

        # =================================================
        # UPDATE BOOK
        # =================================================

        elif choice == "2":

            book_id = input(
                "Book ID: "
            )

            book = manager.search_by_id(
                book_id
            )

            print(
                f"\nCurrent Title: {book.title}"
            )

            print(
                f"Current Author: {book.author}"
            )

            print(
                f"Current Category: {book.category}"
            )

            print(
                f"Current Copies: {book.available_copies}"
            )

            title = input(
                "New Title: "
            )

            author = input(
                "New Author: "
            )

            category = input(
                "New Category: "
            )

            copies = int(
                input(
                    "New Copies: "
                )
            )

            manager.update_book(
                book_id,
                title,
                author,
                category,
                copies
            )

            print(
                "Book Updated Successfully."
            )

        # =================================================
        # REMOVE BOOK
        # =================================================

        elif choice == "3":

            book_id = input(
                "Book ID: "
            )

            manager.remove_book(
                book_id
            )

            print(
                "Book Removed Successfully."
            )

        # =================================================
        # SEARCH BY ID
        # =================================================

        elif choice == "4":

            book = manager.search_by_id(
                input(
                    "Book ID: "
                )
            )

            print(
                "\nBook:"
            )

            print(
                book
            )

            print(
                "Title:",
                book.title
            )

            print(
                "Author:",
                book.author
            )

            print(
                "Category:",
                book.category
            )

            print(
                "Available Copies:",
                book.available_copies
            )

        # =================================================
        # SEARCH BY TITLE
        # =================================================

        elif choice == "5":

            books = manager.search_by_title(
                input(
                    "Title: "
                )
            )

            if not books:

                print(
                    "No books found."
                )

            else:

                for i, book in enumerate(
                    books,
                    1
                ):

                    print(
                        i,
                        "-",
                        book
                    )

        # =================================================
        # SEARCH BY AUTHOR
        # =================================================

        elif choice == "6":

            books = manager.search_by_author(
                input(
                    "Author: "
                )
            )

            if not books:

                print(
                    "No books found."
                )

            else:

                for i, book in enumerate(
                    books,
                    1
                ):

                    print(
                        i,
                        "-",
                        book
                    )

        # =================================================
        # GENERAL SEARCH
        # =================================================

        elif choice == "7":

            books = manager.search_books(
                input(
                    "Search: "
                )
            )

            if not books:

                print(
                    "No books found."
                )

            else:

                for i, book in enumerate(
                    books,
                    1
                ):

                    print(
                        i,
                        "-",
                        book
                    )

        # =================================================
        # BORROW BOOK
        # =================================================

        elif choice == "8":

            book_id = input(
                "Book ID: "
            )

            borrower_name = input(
                "Borrower Name: "
            )

            username = input(
                "Username (optional): "
            )

            record = manager.borrow_book(
                book_id,
                borrower_name,
                username
            )

            print(
                "\nBook Borrowed Successfully."
            )

            print(
                "Record ID:",
                record.record_id
            )

            print(
                "Borrow Date:",
                record.borrow_date
            )

        # =================================================
        # RETURN BOOK
        # =================================================

        elif choice == "9":

            book_id = input(
                "Book ID: "
            )

            username = input(
                "Username: "
            )

            record = manager.return_book(
                book_id,
                username=username
            )

            print(
                "\nBook Returned Successfully."
            )

            print(
                "Record ID:",
                record.record_id
            )

        # =================================================
        # AVAILABLE BOOKS
        # =================================================

        elif choice == "10":

            books = (
                manager.get_available_books()
            )

            if not books:

                print(
                    "No available books."
                )

            else:

                print(
                    "\n===== Available Books ====="
                )

                for i, book in enumerate(
                    books,
                    1
                ):

                    print(
                        f"{i}. "
                        f"{book.book_id} | "
                        f"{book.title} | "
                        f"{book.author} | "
                        f"{book.category} | "
                        f"Copies: "
                        f"{book.available_copies}"
                    )

        # =================================================
        # ALL BOOKS
        # =================================================

        elif choice == "11":

            books = (
                manager.get_all_books()
            )

            if not books:

                print(
                    "No books in library."
                )

            else:

                print(
                    "\n===== All Books ====="
                )

                for i, book in enumerate(
                    books,
                    1
                ):

                    print(
                        f"{i}. "
                        f"{book.book_id} | "
                        f"{book.title} | "
                        f"{book.author} | "
                        f"{book.category} | "
                        f"Available: "
                        f"{book.available_copies}"
                    )

        # =================================================
        # BORROWED BOOKS
        # =================================================

        elif choice == "12":

            if not manager.records:

                print(
                    "No Borrowed Books."
                )

            else:

                print(
                    "\n===== Borrowed Books ====="
                )

                for i, record in enumerate(
                    manager.records,
                    1
                ):

                    print(
                        f"{i}. "
                        f"Record: "
                        f"{record.record_id} | "
                        f"Book: "
                        f"{record.book_id} | "
                        f"Borrower: "
                        f"{record.borrower_name} | "
                        f"Username: "
                        f"{record.username} | "
                        f"Date: "
                        f"{record.borrow_date}"
                    )

        # =================================================
        # EXPORT CSV
        # =================================================

        elif choice == "13":

            StorageManager.export_csv(
                manager.get_all_books()
            )

            print(
                "\nBooks CSV exported successfully."
            )

        # =================================================
        # BONUS
        # =================================================

        elif choice == "14":

            print(
                "\n===== Upper Titles ====="
            )

            print(
                manager.upper_titles()
            )

            print(
                "\n===== Programming Books ====="
            )

            print(
                manager.programming_books()
            )

            print(
                "\n===== Total Available Copies ====="
            )

            print(
                manager.total_copies()
            )

            print(
                "\n===== Catalog ====="
            )

            print(
                manager.catalog()
            )

        # =================================================
        # STATISTICS
        # =================================================

        elif choice == "15":

            manager.statistical_analysis()

        # =================================================
        # RELOAD CSV
        # =================================================

        elif choice == "16":

            if not transactions_file.exists():

                print(
                    "library_transactions.csv "
                    "was not found."
                )

            else:

                confirm = input(
                    "\nThis will replace the current "
                    "library books with books from CSV.\n"
                    "Type YES to continue: "
                )

                if confirm == "YES":

                    manager.import_books_from_csv(
                        transactions_file,
                        overwrite=True
                    )

                    print(
                        "\nBooks reloaded from CSV successfully."
                    )

                else:

                    print(
                        "Operation cancelled."
                    )

        # =================================================
        # EXIT
        # =================================================

        elif choice == "0":

            print(
                "\nGood Bye!"
            )

            break

        # =================================================
        # INVALID
        # =================================================

        else:

            print(
                "Invalid Choice."
            )

    # =====================================================
    # ERROR HANDLING
    # =====================================================

    except LibraryError as e:

        print(
            "\nLibrary Error:"
        )

        print(e)

    except ValueError:

        print(
            "\nPlease enter a valid number."
        )

    except Exception as e:

        print(
            "\nUnexpected Error:"
        )

        print(e)