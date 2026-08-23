import streamlit as st
import pandas as pd
import numpy as np
import math
import random
from scipy import stats
import matplotlib.pyplot as plt

from library_service import LibraryManager
from storage import StorageManager
from models import LibraryError


# =========================================================
# PAGE CONFIGURATION
# =========================================================

st.set_page_config(
    page_title="Library Management System",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)


# =========================================================
# STYLE
# =========================================================

st.markdown("""
<style>

.block-container {
    padding-top: 2rem;
}

.stButton > button {
    width: 100%;
}

[data-testid="stMetricValue"] {
    font-size: 1.7rem;
}

</style>
""", unsafe_allow_html=True)


# =========================================================
# INITIALIZE
# =========================================================

manager = LibraryManager()


# =========================================================
# SESSION STATE
# =========================================================

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "role" not in st.session_state:
    st.session_state.role = None

if "username" not in st.session_state:
    st.session_state.username = None

if "full_name" not in st.session_state:
    st.session_state.full_name = None


# =========================================================
# HELPER
# =========================================================

def books_to_dataframe(books):

    data = []

    for book in books:

        data.append({
            "Book ID": book.book_id,
            "Title": book.title,
            "Author": book.author,
            "Category": book.category,
            "Available Copies": book.available_copies
        })

    return pd.DataFrame(data)


# =========================================================
# LOGIN PAGE
# =========================================================

if not st.session_state.logged_in:

    st.title("📚 Library Management System")

    st.markdown(
        "### Welcome to the Library"
    )

    st.markdown("---")

    login_type = st.radio(
        "Choose Account Type",
        [
            "👨‍💼 Owner",
            "👤 User"
        ],
        horizontal=True
    )

    st.markdown("---")

    # =====================================================
    # OWNER LOGIN
    # =====================================================

    if login_type == "👨‍💼 Owner":

        st.subheader(
            "👨‍💼 Owner Login"
        )

        username = st.text_input(
            "Username"
        )

        password = st.text_input(
            "Password",
            type="password"
        )

        if st.button(
            "🔐 Login as Owner"
        ):

            # Owner account
            # Change these credentials if needed

            if (
                username == "library"
                and password == "lib123456"
            ):

                st.session_state.logged_in = True
                st.session_state.role = "owner"
                st.session_state.username = "library"
                st.session_state.full_name = "Library Owner"

                st.success(
                    "Login successful!"
                )

                st.rerun()

            else:

                st.error(
                    "Incorrect owner username or password."
                )


    # =====================================================
    # USER LOGIN
    # =====================================================

    else:

        st.subheader(
            "👤 User Login"
        )

        username = st.text_input(
            "Username"
        )

        password = st.text_input(
            "Password",
            type="password"
        )

        if st.button(
            "🔐 Login as User"
        ):

            try:

                user = manager.login_user(
                    username,
                    password
                )

                st.session_state.logged_in = True
                st.session_state.role = "user"
                st.session_state.username = user.username
                st.session_state.full_name = user.full_name

                st.success(
                    "Login successful!"
                )

                st.rerun()

            except LibraryError as e:

                st.error(e)

        st.markdown("---")

        st.subheader(
            "📝 Create User Account"
        )

        new_username = st.text_input(
            "New Username",
            key="new_username"
        )

        new_name = st.text_input(
            "Full Name",
            key="new_name"
        )

        new_password = st.text_input(
            "New Password",
            type="password",
            key="new_password"
        )

        if st.button(
            "📝 Register"
        ):

            try:

                manager.register_user(
                    new_username,
                    new_password,
                    new_name
                )

                st.success(
                    "Account created successfully. "
                    "You can now login."
                )

            except LibraryError as e:

                st.error(e)

            except ValueError as e:

                st.error(e)

    st.stop()


# =========================================================
# SIDEBAR
# =========================================================

st.sidebar.title("📚 Library System")

st.sidebar.success(
    f"Welcome, {st.session_state.full_name}"
)

st.sidebar.markdown("---")


# =========================================================
# OWNER MENU
# =========================================================

if st.session_state.role == "owner":

    menu = [
        "🏠 Dashboard",
        "📖 All Books",
        "➕ Add Book",
        "✏️ Update Book",
        "🗑️ Remove Book",
        "📋 Borrowing Records",
        "📊 Statistical Analysis",
        "📁 Export CSV"
    ]


# =========================================================
# USER MENU
# =========================================================

else:

    menu = [
        "🏠 Home",
        "📖 Available Books",
        "🔎 Search Book",
        "📤 Borrow Book",
        "📥 Return Book",
        "📋 My Borrowed Books"
    ]


choice = st.sidebar.selectbox(
    "Navigation",
    menu
)


# =========================================================
# LOGOUT
# =========================================================

st.sidebar.markdown("---")

if st.sidebar.button(
    "🚪 Logout"
):

    st.session_state.logged_in = False
    st.session_state.role = None
    st.session_state.username = None
    st.session_state.full_name = None

    st.rerun()


# =========================================================
# OWNER DASHBOARD
# =========================================================

if (
    st.session_state.role == "owner"
    and choice == "🏠 Dashboard"
):

    st.title(
        "👨‍💼 Owner Dashboard"
    )

    books = manager.get_all_books()

    total_books = len(books)

    total_copies = sum(
        book.available_copies
        for book in books
    )

    available_books = sum(
        book.available_copies > 0
        for book in books
    )

    borrowed_books = len(
        manager.records
    )

    col1, col2, col3, col4 = st.columns(4)

    col1.metric(
        "📚 Total Books",
        total_books
    )

    col2.metric(
        "📦 Available Copies",
        total_copies
    )

    col3.metric(
        "✅ Available Books",
        available_books
    )

    col4.metric(
        "📤 Borrowing Records",
        borrowed_books
    )

    st.markdown("---")

    if books:

        df = books_to_dataframe(
            books
        )

        st.subheader(
            "📖 Library Inventory"
        )

        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True
        )

        st.subheader(
            "📊 Books by Category"
        )

        category_counts = (
            df["Category"]
            .value_counts()
        )

        st.bar_chart(
            category_counts
        )

    else:

        st.info(
            "No books available."
        )


# =========================================================
# OWNER - ALL BOOKS
# =========================================================

elif (
    st.session_state.role == "owner"
    and choice == "📖 All Books"
):

    st.title(
        "📖 All Books"
    )

    books = manager.get_all_books()

    if books:

        st.dataframe(
            books_to_dataframe(books),
            use_container_width=True,
            hide_index=True
        )

    else:

        st.info(
            "No books found."
        )


# =========================================================
# OWNER - ADD BOOK
# =========================================================

elif (
    st.session_state.role == "owner"
    and choice == "➕ Add Book"
):

    st.title(
        "➕ Add New Book"
    )

    col1, col2 = st.columns(2)

    with col1:

        book_id = st.text_input(
            "Book ID"
        )

        title = st.text_input(
            "Title"
        )

        author = st.text_input(
            "Author"
        )

    with col2:

        category = st.text_input(
            "Category"
        )

        copies = st.number_input(
            "Copies",
            min_value=1,
            value=1,
            step=1
        )

    if st.button(
        "➕ Add Book"
    ):

        try:

            manager.add_book(
                book_id,
                title,
                author,
                category,
                int(copies),
                role="owner"
            )

            st.success(
                "✅ Book Added Successfully"
            )

            st.rerun()

        except LibraryError as e:

            st.error(e)

        except ValueError as e:

            st.error(e)


# =========================================================
# OWNER - UPDATE BOOK
# =========================================================

elif (
    st.session_state.role == "owner"
    and choice == "✏️ Update Book"
):

    st.title(
        "✏️ Update Book"
    )

    books = manager.get_all_books()

    if not books:

        st.info(
            "No books available."
        )

    else:

        book_options = {
            f"{book.book_id} - {book.title}":
            book.book_id
            for book in books
        }

        selected = st.selectbox(
            "Select Book",
            list(book_options.keys())
        )

        book_id = book_options[selected]

        book = manager.search_by_id(
            book_id
        )

        title = st.text_input(
            "Title",
            value=book.title
        )

        author = st.text_input(
            "Author",
            value=book.author
        )

        category = st.text_input(
            "Category",
            value=book.category
        )

        copies = st.number_input(
            "Available Copies",
            min_value=0,
            value=book.available_copies,
            step=1
        )

        if st.button(
            "💾 Save Changes"
        ):

            try:

                manager.update_book(
                    book_id,
                    title,
                    author,
                    category,
                    int(copies),
                    role="owner"
                )

                st.success(
                    "Book updated successfully."
                )

                st.rerun()

            except LibraryError as e:

                st.error(e)


# =========================================================
# OWNER - REMOVE BOOK
# =========================================================

elif (
    st.session_state.role == "owner"
    and choice == "🗑️ Remove Book"
):

    st.title(
        "🗑️ Remove Book"
    )

    books = manager.get_all_books()

    if books:

        book_options = {
            f"{book.book_id} - {book.title}":
            book.book_id
            for book in books
        }

        selected = st.selectbox(
            "Select Book",
            list(book_options.keys())
        )

        if st.button(
            "🗑️ Remove Book"
        ):

            try:

                manager.remove_book(
                    book_options[selected],
                    role="owner"
                )

                st.success(
                    "Book removed successfully."
                )

                st.rerun()

            except LibraryError as e:

                st.error(e)

    else:

        st.info(
            "No books available."
        )


# =========================================================
# OWNER - BORROWING RECORDS
# =========================================================

elif (
    st.session_state.role == "owner"
    and choice == "📋 Borrowing Records"
):

    st.title(
        "📋 Borrowing Records"
    )

    records = manager.get_all_borrowed_books(
        role="owner"
    )

    if not records:

        st.info(
            "No borrowing records."
        )

    else:

        data = []

        for record in records:

            book = manager.books.get(
                record.book_id
            )

            data.append({
                "Record ID": record.record_id,
                "Book ID": record.book_id,
                "Book": (
                    book.title
                    if book
                    else "Unknown"
                ),
                "Borrower": record.borrower_name,
                "Username": record.username,
                "Borrow Date": record.borrow_date
            })

        st.dataframe(
            pd.DataFrame(data),
            use_container_width=True,
            hide_index=True
        )


# =========================================================
# OWNER - STATISTICS
# =========================================================

elif (
    st.session_state.role == "owner"
    and choice == "📊 Statistical Analysis"
):

    st.title(
        "📊 Statistical Analysis"
    )

    result = manager.get_statistical_data()

    if result is None:

        st.warning(
            "No data available."
        )

    else:

        values = result["values"]

        st.subheader(
            "📌 Descriptive Statistics"
        )

        c1, c2, c3, c4 = st.columns(4)

        c1.metric(
            "Mean",
            round(result["mean"], 2)
        )

        c2.metric(
            "Median",
            round(result["median"], 2)
        )

        c3.metric(
            "Mode",
            round(
                float(result["mode"]),
                2
            )
        )

        c4.metric(
            "Range",
            round(result["range"], 2)
        )

        c5, c6, c7, c8 = st.columns(4)

        c5.metric(
            "Variance",
            round(result["variance"], 2)
        )

        c6.metric(
            "Std. Deviation",
            round(result["std"], 2)
        )

        c7.metric(
            "IQR",
            round(result["iqr"], 2)
        )

        c8.metric(
            "Skewness",
            round(result["skewness"], 4)
        )

        st.markdown("---")

        st.subheader(
            "📊 Distribution"
        )

        frequency = (
            pd.Series(values)
            .value_counts()
            .sort_index()
        )

        st.dataframe(
            pd.DataFrame({
                "Copies": frequency.index,
                "Frequency": frequency.values
            }),
            use_container_width=True,
            hide_index=True
        )

        st.write(
            f"Q1 = {result['q1']:.2f}"
        )

        st.write(
            f"Q2 = {result['q2']:.2f}"
        )

        st.write(
            f"Q3 = {result['q3']:.2f}"
        )

        st.write(
            f"Lower Bound = {result['lower']:.2f}"
        )

        st.write(
            f"Upper Bound = {result['upper']:.2f}"
        )

        if len(result["outliers"]):

            st.warning(
                f"Outliers: "
                f"{result['outliers'].tolist()}"
            )

        else:

            st.success(
                "No outliers detected."
            )

        st.markdown("---")

        st.subheader(
            "🧮 Linear Algebra"
        )

        vector = np.array(values)

        st.write(
            "Vector:"
        )

        st.code(
            str(vector)
        )

        st.write(
            "Vector × 2:"
        )

        st.code(
            str(vector * 2)
        )

        st.write(
            f"Dot Product: "
            f"{np.dot(vector, vector)}"
        )

        st.markdown("---")

        st.subheader(
            "🎲 Probability"
        )

        st.write(
            f"Probability of selecting an available book: "
            f"{result['probability']:.2%}"
        )

        st.markdown("---")

        st.subheader(
            "📈 Visualization"
        )

        chart_type = st.selectbox(
            "Choose Chart",
            [
                "Bar Chart",
                "Histogram",
                "Box Plot",
                "Scatter Plot",
                "Line Chart"
            ]
        )

        books = manager.get_all_books()

        df = books_to_dataframe(
            books
        )

        if chart_type == "Bar Chart":

            st.bar_chart(
                df["Category"].value_counts()
            )

        elif chart_type == "Histogram":

            fig, ax = plt.subplots()

            ax.hist(values)

            ax.set_title(
                "Available Copies"
            )

            ax.set_xlabel(
                "Copies"
            )

            ax.set_ylabel(
                "Frequency"
            )

            st.pyplot(fig)

        elif chart_type == "Box Plot":

            fig, ax = plt.subplots()

            ax.boxplot(values)

            ax.set_title(
                "Available Copies"
            )

            st.pyplot(fig)

        elif chart_type == "Scatter Plot":

            x = np.arange(
                1,
                len(values) + 1
            )

            fig, ax = plt.subplots()

            ax.scatter(
                x,
                values
            )

            ax.set_xlabel(
                "Book Index"
            )

            ax.set_ylabel(
                "Available Copies"
            )

            st.pyplot(fig)

        elif chart_type == "Line Chart":

            line_df = pd.DataFrame({
                "Book": np.arange(
                    1,
                    len(values) + 1
                ),
                "Available Copies": values
            })

            st.line_chart(
                line_df.set_index(
                    "Book"
                )
            )


# =========================================================
# OWNER - EXPORT CSV
# =========================================================

elif (
    st.session_state.role == "owner"
    and choice == "📁 Export CSV"
):

    st.title(
        "📁 Export Books"
    )

    books = manager.get_all_books()

    if books:

        df = books_to_dataframe(
            books
        )

        csv_data = df.to_csv(
            index=False
        ).encode(
            "utf-8-sig"
        )

        st.download_button(
            "⬇️ Download books.csv",
            data=csv_data,
            file_name="books.csv",
            mime="text/csv"
        )

    else:

        st.info(
            "No books available."
        )


# =========================================================
# USER HOME
# =========================================================

elif (
    st.session_state.role == "user"
    and choice == "🏠 Home"
):

    st.title(
        f"👋 Welcome, "
        f"{st.session_state.full_name}"
    )

    books = manager.get_available_books()

    total_books = len(
        manager.books
    )

    available_books = len(
        books
    )

    my_records = manager.get_user_borrowed_books(
        st.session_state.username
    )

    col1, col2, col3 = st.columns(3)

    col1.metric(
        "📚 Total Books",
        total_books
    )

    col2.metric(
        "✅ Available Books",
        available_books
    )

    col3.metric(
        "📤 My Borrowed Books",
        len(my_records)
    )

    st.markdown("---")

    st.info(
        "Use the menu on the left to search, "
        "borrow, or return books."
    )


# =========================================================
# USER - AVAILABLE BOOKS
# =========================================================

elif (
    st.session_state.role == "user"
    and choice == "📖 Available Books"
):

    st.title(
        "📖 Available Books"
    )

    books = manager.get_available_books()

    if books:

        st.dataframe(
            books_to_dataframe(books),
            use_container_width=True,
            hide_index=True
        )

    else:

        st.warning(
            "No books are currently available."
        )


# =========================================================
# USER - SEARCH
# =========================================================

elif (
    st.session_state.role == "user"
    and choice == "🔎 Search Book"
):

    st.title(
        "🔎 Search Book"
    )

    search_type = st.selectbox(
        "Search By",
        [
            "Book ID",
            "Title",
            "Author"
        ]
    )

    value = st.text_input(
        "Enter Search Value"
    )

    if st.button(
        "🔎 Search"
    ):

        try:

            if not value.strip():

                st.warning(
                    "Please enter a search value."
                )

            elif search_type == "Book ID":

                book = manager.search_by_id(
                    value
                )

                st.dataframe(
                    books_to_dataframe([book]),
                    use_container_width=True,
                    hide_index=True
                )

            elif search_type == "Title":

                books = manager.search_by_title(
                    value
                )

                if books:

                    st.dataframe(
                        books_to_dataframe(books),
                        use_container_width=True,
                        hide_index=True
                    )

                else:

                    st.warning(
                        "No books found."
                    )

            else:

                books = manager.search_by_author(
                    value
                )

                if books:

                    st.dataframe(
                        books_to_dataframe(books),
                        use_container_width=True,
                        hide_index=True
                    )

                else:

                    st.warning(
                        "No books found."
                    )

        except LibraryError as e:

            st.error(e)


# =========================================================
# USER - BORROW
# =========================================================

elif (
    st.session_state.role == "user"
    and choice == "📤 Borrow Book"
):

    st.title(
        "📤 Borrow Book"
    )

    books = manager.get_available_books()

    if not books:

        st.warning(
            "No books are currently available."
        )

    else:

        book_options = {
            f"{book.book_id} - {book.title}":
            book.book_id
            for book in books
        }

        selected = st.selectbox(
            "Select Book",
            list(book_options.keys())
        )

        if st.button(
            "📤 Borrow Book"
        ):

            try:

                manager.borrow_book(
                    book_options[selected],
                    st.session_state.full_name,
                    st.session_state.username,
                    role="user"
                )

                st.success(
                    "✅ Book Borrowed Successfully"
                )

                st.rerun()

            except LibraryError as e:

                st.error(e)


# =========================================================
# USER - RETURN
# =========================================================

elif (
    st.session_state.role == "user"
    and choice == "📥 Return Book"
):

    st.title(
        "📥 Return Book"
    )

    records = manager.get_user_borrowed_books(
        st.session_state.username
    )

    if not records:

        st.info(
            "You have no borrowed books."
        )

    else:

        book_options = {}

        for record in records:

            book = manager.books.get(
                record.book_id
            )

            if book:

                book_options[
                    f"{book.book_id} - {book.title}"
                ] = book.book_id

        selected = st.selectbox(
            "Select Book",
            list(book_options.keys())
        )

        if st.button(
            "📥 Return Book"
        ):

            try:

                manager.return_book(
                    book_options[selected],
                    st.session_state.username,
                    role="user"
                )

                st.success(
                    "✅ Book Returned Successfully"
                )

                st.rerun()

            except LibraryError as e:

                st.error(e)


# =========================================================
# USER - MY BORROWED BOOKS
# =========================================================

elif (
    st.session_state.role == "user"
    and choice == "📋 My Borrowed Books"
):

    st.title(
        "📋 My Borrowed Books"
    )

    records = manager.get_user_borrowed_books(
        st.session_state.username
    )

    if not records:

        st.info(
            "You have no borrowed books."
        )

    else:

        data = []

        for record in records:

            book = manager.books.get(
                record.book_id
            )

            data.append({
                "Record ID": record.record_id,
                "Book ID": record.book_id,
                "Book": (
                    book.title
                    if book
                    else "Unknown"
                ),
                "Borrow Date": record.borrow_date
            })

        st.dataframe(
            pd.DataFrame(data),
            use_container_width=True,
            hide_index=True
        )
