"""
main.py
"""

from library_service import LibraryManager
from storage import StorageManager
from models import LibraryError


manager = LibraryManager()

# بيانات تجريبية
if len(manager.books) == 0:

    manager.add_book("B001", "Clean Code", "Robert Martin", "Programming", 3)
    manager.add_book("B002", "Python Crash Course", "Eric Matthes", "Programming", 5)
    manager.add_book("B003", "The Hobbit", "Tolkien", "Fantasy", 2)


while True:

    print("\n===== Library Management System =====")
    print("1. Add Book")
    print("2. Remove Book")
    print("3. Search By ID")
    print("4. Search By Title")
    print("5. Search By Author")
    print("6. Borrow Book")
    print("7. Return Book")
    print("8. Display Available Books")
    print("9. Display All Books")
    print("10. Display Borrowed Books")
    print("11. Export CSV")
    print("12. Bonus")
    print("0. Exit")

    choice = input("Enter Choice: ")

    try:

        if choice == "1":

            manager.add_book(

                input("Book ID: "),
                input("Title: "),
                input("Author: "),
                input("Category: "),
                int(input("Copies: "))

            )

            print("Book Added Successfully")

        elif choice == "2":

            manager.remove_book(

                input("Book ID: ")

            )

            print("Book Removed")

        elif choice == "3":

            book = manager.search_by_id(

                input("Book ID: ")

            )

            print(book)

        elif choice == "4":

            books = manager.search_by_title(

                input("Title: ")

            )

            for i, book in enumerate(books, 1):

                print(i, "-", book)

        elif choice == "5":

            books = manager.search_by_author(

                input("Author: ")

            )

            for i, book in enumerate(books, 1):

                print(i, "-", book)

        elif choice == "6":

            manager.borrow_book(

                input("Book ID: "),
                input("Borrower Name: ")

            )

            print("Book Borrowed")

        elif choice == "7":

            manager.return_book(

                input("Book ID: "),
                input("Borrower Name: ")

            )

            print("Book Returned")

        elif choice == "8":

            books = manager.get_available_books()

            for i, book in enumerate(books, 1):

                print(i, "-", book)

        elif choice == "9":

            books = manager.get_all_books()

            for i, book in enumerate(books, 1):

                print(i, "-", book)

        elif choice == "10":

            if len(manager.records) == 0:

                print("No Borrowed Books")

            else:

                for i, record in enumerate(manager.records, 1):

                    print(i, "-", record)

        elif choice == "11":

            StorageManager.export_csv(

                manager.get_all_books()

            )

            print("CSV File Created")

        elif choice == "12":

            print("Upper Titles:")
            print(manager.upper_titles())

            print("\nProgramming Books:")
            print(manager.programming_books())

            print("\nTotal Copies:")
            print(manager.total_copies())

            print("\nCatalog:")
            print(manager.catalog())

        elif choice == "0":

            print("Good Bye")

            break

        else:

            print("Invalid Choice")

    except LibraryError as e:

        print(e)

    except ValueError:

        print("Please Enter A Valid Number")

    except Exception as e:

        print(e)