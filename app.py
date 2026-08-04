import streamlit as st
import pandas as pd

from library_service import LibraryManager
from storage import StorageManager
from models import LibraryError

# ==========================
# Page
# ==========================

st.set_page_config(
    page_title="Library Management System",
    page_icon="📚",
    layout="wide"
)

st.title("📚 Library Management System")
st.write("Welcome to the Library Management System")

manager = LibraryManager()

# ==========================
# Menu
# ==========================

menu = [
    "Display Books",
    "Search Book",
    "Add Book",
    "Remove Book",
    "Borrow Book",
    "Return Book",
    "Borrowed Books",
    "Export CSV"
]

choice = st.sidebar.selectbox("Menu", menu)

# ==========================
# Display Books
# ==========================

if choice == "Display Books":

    st.header("All Books")

    books = manager.get_all_books()

    if len(books) == 0:

        st.info("No Books Found")

    else:

        data = []

        for book in books:

            data.append({

                "Book ID": book.book_id,
                "Title": book.title,
                "Author": book.author,
                "Category": book.category,
                "Available Copies": book.available_copies

            })

        df = pd.DataFrame(data)

        st.dataframe(df, use_container_width=True)

# ==========================
# Search Book
# ==========================

elif choice == "Search Book":

    st.header("Search Book")

    search_type = st.selectbox(

        "Search By",

        [
            "Book ID",
            "Title",
            "Author"
        ]

    )

    value = st.text_input("Enter Value")

    if st.button("Search"):

        try:

            if search_type == "Book ID":

                book = manager.search_by_id(value)

                data = [{

                    "Book ID": book.book_id,
                    "Title": book.title,
                    "Author": book.author,
                    "Category": book.category,
                    "Available Copies": book.available_copies

                }]

                st.dataframe(pd.DataFrame(data), use_container_width=True)

            elif search_type == "Title":

                books = manager.search_by_title(value)

                data = []

                for book in books:

                    data.append({

                        "Book ID": book.book_id,
                        "Title": book.title,
                        "Author": book.author,
                        "Category": book.category,
                        "Available Copies": book.available_copies

                    })

                st.dataframe(pd.DataFrame(data), use_container_width=True)

            else:

                books = manager.search_by_author(value)

                data = []

                for book in books:

                    data.append({

                        "Book ID": book.book_id,
                        "Title": book.title,
                        "Author": book.author,
                        "Category": book.category,
                        "Available Copies": book.available_copies

                    })

                st.dataframe(pd.DataFrame(data), use_container_width=True)

        except LibraryError as e:

            st.error(e)

        except Exception as e:

            st.error(e)

# ==========================
# Add Book
# ==========================

elif choice == "Add Book":

    st.header("Add Book")

    book_id = st.text_input("Book ID")

    title = st.text_input("Title")

    author = st.text_input("Author")

    category = st.text_input("Category")

    copies = st.number_input(
        "Available Copies",
        min_value=1,
        value=1
    )

    if st.button("Add Book"):

        try:

            manager.add_book(
                book_id,
                title,
                author,
                category,
                int(copies)
            )

            st.success("Book Added Successfully")

        except LibraryError as e:

            st.error(e)

        except Exception as e:

            st.error(e)

# ==========================
# Remove Book
# ==========================

elif choice == "Remove Book":

    st.header("Remove Book")

    book_id = st.text_input("Book ID")

    if st.button("Remove"):

        try:

            manager.remove_book(book_id)

            st.success("Book Removed Successfully")

        except LibraryError as e:

            st.error(e)

        except Exception as e:

            st.error(e)
# ==========================
# Borrow Book
# ==========================

elif choice == "Borrow Book":

    st.header("Borrow Book")

    book_id = st.text_input("Book ID")

    borrower = st.text_input("Borrower Name")

    if st.button("Borrow"):

        try:

            manager.borrow_book(book_id, borrower)

            st.success("Book Borrowed Successfully")

        except LibraryError as e:

            st.error(e)

        except Exception as e:

            st.error(e)

# ==========================
# Return Book
# ==========================

elif choice == "Return Book":

    st.header("Return Book")

    book_id = st.text_input("Book ID")

    borrower = st.text_input("Borrower Name")

    if st.button("Return"):

        try:

            manager.return_book(book_id, borrower)

            st.success("Book Returned Successfully")

        except LibraryError as e:

            st.error(e)

        except Exception as e:

            st.error(e)

# ==========================
# Borrowed Books
# ==========================

elif choice == "Borrowed Books":

    st.header("Borrowed Books")

    if len(manager.records) == 0:

        st.info("No Borrowed Books")

    else:

        data = []

        for record in manager.records:

            data.append({

                "Record ID": record.record_id,
                "Book ID": record.book_id,
                "Borrower": record.borrower_name,
                "Borrow Date": record.borrow_date

            })

        df = pd.DataFrame(data)

        st.dataframe(df, use_container_width=True)

# ==========================
# Export CSV
# ==========================

elif choice == "Export CSV":

    st.header("Export Books")

    if st.button("Export"):

        try:

            StorageManager.export_csv(manager.get_all_books())

            st.success("books.csv exported successfully")

        except Exception as e:

            st.error(e)