# ============================================================
# Library Management System
# Module 3 - Data Wrangling, EDA & Visualization
# ============================================================

import io
import re
import hashlib
from pathlib import Path
from datetime import date

import numpy as np
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
import seaborn as sns

try:
    import polars as pl
    POLARS_AVAILABLE = True
except ImportError:
    POLARS_AVAILABLE = False

try:
    import plotly.express as px
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False

from models import Book, BorrowRecord, User
from storage import (
    StorageManager,
    hash_password,
    verify_password
)


# ============================================================
# CONFIG
# ============================================================

st.set_page_config(
    page_title="Library Management System",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

BASE_DIR = Path(__file__).resolve().parent

TRANSACTIONS_FILE = (
    BASE_DIR / "library_transactions.csv"
)


# ============================================================
# CSS
# ============================================================

st.markdown(
    """
    <style>

    .main {
        padding-top: 1rem;
    }

    .title-box {
        padding: 20px;
        border-radius: 15px;
        background: linear-gradient(
            135deg,
            #667eea,
            #764ba2
        );
        color: white;
        margin-bottom: 20px;
    }

    .metric-card {
        padding: 15px;
        border-radius: 12px;
        background-color: #f7f7f7;
        border: 1px solid #ddd;
        text-align: center;
    }

    </style>
    """,
    unsafe_allow_html=True
)


# ============================================================
# SESSION STATE
# ============================================================

DEFAULT_SESSION = {
    "logged_in": False,
    "role": None,
    "username": None,
    "full_name": None,
    "transactions_bytes": None,
    "transactions_filename": None,
    "books_synced": False
}

for key, value in DEFAULT_SESSION.items():

    if key not in st.session_state:

        st.session_state[key] = value


# ============================================================
# HELPERS
# ============================================================

def normalize_text(value):

    if pd.isna(value):
        return np.nan

    value = str(value)

    value = value.replace("**", "")

    value = re.sub(
        r"\s+",
        " ",
        value
    )

    return value.strip()


def section_title(
    title,
    description=None
):

    st.markdown(
        f"## {title}"
    )

    if description:

        st.caption(
            description
        )

    st.divider()


def dataframe_download(
    df,
    filename
):

    csv_data = df.to_csv(
        index=False
    ).encode(
        "utf-8-sig"
    )

    st.download_button(
        label=f"⬇️ Download {filename}",
        data=csv_data,
        file_name=filename,
        mime="text/csv"
    )


# ============================================================
# READ CSV
# ============================================================

def read_transactions(
    uploaded_file=None
):

    try:

        if uploaded_file is not None:

            uploaded_file.seek(0)

            df = pd.read_csv(
                uploaded_file
            )

            st.session_state[
                "transactions_bytes"
            ] = uploaded_file.getvalue()

            st.session_state[
                "transactions_filename"
            ] = uploaded_file.name

            return (
                df,
                f"Uploaded file: {uploaded_file.name}"
            )

        if (
            st.session_state.get(
                "transactions_bytes"
            ) is not None
        ):

            df = pd.read_csv(
                io.BytesIO(
                    st.session_state[
                        "transactions_bytes"
                    ]
                )
            )

            filename = (
                st.session_state.get(
                    "transactions_filename",
                    "Uploaded file"
                )
            )

            return (
                df,
                f"Uploaded file: {filename}"
            )

        if TRANSACTIONS_FILE.exists():

            df = pd.read_csv(
                TRANSACTIONS_FILE
            )

            return (
                df,
                f"Local file: {TRANSACTIONS_FILE}"
            )

        return (
            pd.DataFrame(),
            "No dataset found."
        )

    except Exception as e:

        st.error(
            f"Could not read CSV file: {e}"
        )

        return (
            pd.DataFrame(),
            "Error while reading dataset."
        )


# ============================================================
# STANDARDIZE COLUMNS
# ============================================================

def standardize_columns(df):

    if df.empty:
        return df.copy()

    df = df.copy()

    df.columns = [
        str(col)
        .replace("**", "")
        .strip()
        .replace(" ", "_")
        for col in df.columns
    ]

    for col in df.select_dtypes(
        include=["object"]
    ).columns:

        df[col] = df[col].apply(
            normalize_text
        )

    for col in [
        "Borrow_Date",
        "Due_Date",
        "Return_Date"
    ]:

        if col in df.columns:

            df[col] = pd.to_datetime(
                df[col],
                errors="coerce"
            )

    if "Fine_Amount" in df.columns:

        df["Fine_Amount"] = pd.to_numeric(
            df["Fine_Amount"],
            errors="coerce"
        )

    return df


# ============================================================
# IMPORT CSV BOOKS INTO LIBRARY
# ============================================================

def create_books_from_csv(df):

    """
    Convert unique books from the transaction dataset
    into actual library books.

    The CSV does not contain total copies,
    therefore every unique Book_ID starts with
    one available copy.
    """

    books = {}

    if df.empty:
        return books

    required = [
        "Book_ID",
        "Book_Title"
    ]

    for column in required:

        if column not in df.columns:
            return books

    working = df.copy()

    working["Book_ID"] = (
        working["Book_ID"]
        .astype("string")
        .str.strip()
    )

    working = working[
        working["Book_ID"].notna()
        & (working["Book_ID"] != "")
    ]

    for book_id, group in working.groupby(
        "Book_ID",
        sort=True
    ):

        title = "Unknown"

        if "Book_Title" in group.columns:

            titles = (
                group["Book_Title"]
                .dropna()
                .astype(str)
                .str.strip()
            )

            titles = titles[
                titles != ""
            ]

            if not titles.empty:
                title = titles.iloc[0]

        author = "Unknown"

        if "Author" in group.columns:

            authors = (
                group["Author"]
                .dropna()
                .astype(str)
                .str.strip()
            )

            authors = authors[
                authors != ""
            ]

            if not authors.empty:
                author = authors.iloc[0]

        category = "Unknown"

        if "Category" in group.columns:

            categories = (
                group["Category"]
                .dropna()
                .astype(str)
                .str.strip()
            )

            categories = categories[
                categories != ""
            ]

            if not categories.empty:
                category = categories.iloc[0]

        books[str(book_id)] = Book(
            book_id=str(book_id),
            title=title,
            author=author,
            category=category,
            available_copies=1
        )

    return books


def sync_books_from_csv(
    df,
    force=False
):

    """
    Import books from CSV.

    If force=True, current books are replaced
    with the books from the uploaded CSV.
    """

    if df.empty:
        return False, 0

    current_books, records = (
        StorageManager.load_data()
    )

    # --------------------------------------------------------
    # Do not overwrite existing books automatically
    # --------------------------------------------------------

    if current_books and not force:

        return False, len(current_books)

    # --------------------------------------------------------
    # Create books
    # --------------------------------------------------------

    new_books = create_books_from_csv(
        df
    )

    if not new_books:

        return False, 0

    # --------------------------------------------------------
    # Save
    # --------------------------------------------------------

    StorageManager.save_data(
        new_books,
        records
    )

    st.session_state[
        "books_synced"
    ] = True

    return True, len(new_books)


def load_library_data(
    df=None
):

    books, records = (
        StorageManager.load_data()
    )

    # --------------------------------------------------------
    # IMPORTANT:
    # If books.json is empty, import CSV books.
    # --------------------------------------------------------

    if (
        not books
        and df is not None
        and not df.empty
    ):

        new_books = create_books_from_csv(
            df
        )

        if new_books:

            StorageManager.save_data(
                new_books,
                records
            )

            books = new_books

    return books, records


def save_library_data(
    books,
    records
):

    StorageManager.save_data(
        books,
        records
    )


# ============================================================
# USERS / OWNER
# ============================================================

def load_users():

    return StorageManager.load_users()


def load_owner():

    return StorageManager.load_owner_profile()


# ============================================================
# AUTHENTICATION
# ============================================================

def login_user(
    username,
    password
):

    users = load_users()

    username = username.strip()

    if username not in users:
        return None

    user = users[username]

    if verify_password(
        password,
        user.password
    ):

        # ----------------------------------------------------
        # Migrate old plaintext password to hash
        # ----------------------------------------------------

        if user.password != hash_password(
            password
        ):

            user.password = hash_password(
                password
            )

            users[username] = user

            StorageManager.save_users(
                users
            )

        return user

    return None


def login_owner(
    username,
    password
):

    owner = load_owner()

    if username.strip() != owner.get(
        "username",
        ""
    ):

        return None

    if verify_password(
        password,
        owner.get(
            "password",
            ""
        )
    ):

        # ----------------------------------------------------
        # Migrate old plaintext password
        # ----------------------------------------------------

        if owner["password"] != hash_password(
            password
        ):

            owner["password"] = hash_password(
                password
            )

            StorageManager.save_owner_profile(
                owner
            )

        return owner

    return None


def register_user(
    username,
    password,
    full_name
):

    username = username.strip()
    full_name = full_name.strip()

    if not username:
        return False, "Username is required."

    if not password:
        return False, "Password is required."

    if not full_name:
        return False, "Full name is required."

    users = load_users()
    owner = load_owner()

    if username == owner.get(
        "username",
        ""
    ):

        return False, (
            "This username belongs to the owner."
        )

    if username in users:

        return False, (
            "Username already exists."
        )

    user = User(
        username=username,
        password=hash_password(password),
        full_name=full_name
    )

    users[username] = user

    StorageManager.save_users(
        users
    )

    return True, (
        "Account created successfully."
    )


# ============================================================
# LOGIN PAGE
# ============================================================

def login_page():

    login_tab, register_tab = st.tabs(
        [
            "🔐 Login",
            "📝 Register"
        ]
    )

    with login_tab:

        st.subheader(
            "Login to Library System"
        )

        username = st.text_input(
            "Username",
            key="login_username"
        )

        password = st.text_input(
            "Password",
            type="password",
            key="login_password"
        )

        if st.button(
            "Login",
            use_container_width=True
        ):

            owner = login_owner(
                username,
                password
            )

            if owner:

                st.session_state.logged_in = True
                st.session_state.role = "owner"
                st.session_state.username = (
                    owner["username"]
                )
                st.session_state.full_name = (
                    owner["full_name"]
                )

                st.rerun()

            user = login_user(
                username,
                password
            )

            if user:

                st.session_state.logged_in = True
                st.session_state.role = "user"
                st.session_state.username = (
                    user.username
                )
                st.session_state.full_name = (
                    user.full_name
                )

                st.rerun()

            st.error(
                "Invalid username or password."
            )

        st.caption(
            "Use your registered account to login."
        )

    # --------------------------------------------------------
    # REGISTER
    # --------------------------------------------------------

    with register_tab:

        st.subheader(
            "Create New User Account"
        )

        full_name = st.text_input(
            "Full Name",
            key="register_name"
        )

        username = st.text_input(
            "Username",
            key="register_username"
        )

        password = st.text_input(
            "Password",
            type="password",
            key="register_password"
        )

        confirm = st.text_input(
            "Confirm Password",
            type="password",
            key="register_confirm"
        )

        if st.button(
            "Create Account",
            use_container_width=True
        ):

            if password != confirm:

                st.error(
                    "Passwords do not match."
                )

            else:

                success, message = (
                    register_user(
                        username,
                        password,
                        full_name
                    )
                )

                if success:
                    st.success(message)
                else:
                    st.error(message)


# ============================================================
# OWNER PROFILE
# ============================================================

def owner_profile_page():

    section_title(
        "👤 My Profile",
        "Edit your name, username and password."
    )

    owner = load_owner()

    with st.form(
        "owner_profile_form"
    ):

        full_name = st.text_input(
            "Full Name",
            value=owner.get(
                "full_name",
                ""
            )
        )

        username = st.text_input(
            "Username",
            value=owner.get(
                "username",
                ""
            )
        )

        st.markdown(
            "### 🔐 Change Password"
        )

        current_password = st.text_input(
            "Current Password",
            type="password"
        )

        new_password = st.text_input(
            "New Password",
            type="password"
        )

        confirm_password = st.text_input(
            "Confirm New Password",
            type="password"
        )

        submitted = st.form_submit_button(
            "💾 Save Changes"
        )

        if submitted:

            # -----------------------------------------------
            # Validate current password
            # -----------------------------------------------

            if not verify_password(
                current_password,
                owner.get(
                    "password",
                    ""
                )
            ):

                st.error(
                    "Current password is incorrect."
                )

                return

            if not full_name.strip():

                st.error(
                    "Full name cannot be empty."
                )

                return

            if not username.strip():

                st.error(
                    "Username cannot be empty."
                )

                return

            # -----------------------------------------------
            # Check username against users
            # -----------------------------------------------

            users = load_users()

            if (
                username.strip()
                != owner["username"]
                and username.strip()
                in users
            ):

                st.error(
                    "This username is already used by a user."
                )

                return

            # -----------------------------------------------
            # Password
            # -----------------------------------------------

            if new_password:

                if new_password != confirm_password:

                    st.error(
                        "New passwords do not match."
                    )

                    return

                final_password = hash_password(
                    new_password
                )

            else:

                final_password = owner["password"]

            # -----------------------------------------------
            # Save
            # -----------------------------------------------

            owner["full_name"] = (
                full_name.strip()
            )

            owner["username"] = (
                username.strip()
            )

            owner["password"] = (
                final_password
            )

            StorageManager.save_owner_profile(
                owner
            )

            st.session_state.username = (
                owner["username"]
            )

            st.session_state.full_name = (
                owner["full_name"]
            )

            st.success(
                "Profile updated successfully."
            )

            st.rerun()


# ============================================================
# USER PROFILE
# ============================================================

def user_profile_page():

    section_title(
        "👤 My Profile",
        "Edit your name, username and password."
    )

    users = load_users()

    current_username = (
        st.session_state.username
    )

    if current_username not in users:

        st.error(
            "User account not found."
        )

        return

    user = users[current_username]

    with st.form(
        "user_profile_form"
    ):

        full_name = st.text_input(
            "Full Name",
            value=user.full_name
        )

        new_username = st.text_input(
            "Username",
            value=user.username
        )

        st.markdown(
            "### 🔐 Change Password"
        )

        current_password = st.text_input(
            "Current Password",
            type="password"
        )

        new_password = st.text_input(
            "New Password",
            type="password"
        )

        confirm_password = st.text_input(
            "Confirm New Password",
            type="password"
        )

        submitted = st.form_submit_button(
            "💾 Save Changes"
        )

        if submitted:

            if not verify_password(
                current_password,
                user.password
            ):

                st.error(
                    "Current password is incorrect."
                )

                return

            new_username = (
                new_username.strip()
            )

            full_name = (
                full_name.strip()
            )

            if not new_username:

                st.error(
                    "Username cannot be empty."
                )

                return

            if not full_name:

                st.error(
                    "Full name cannot be empty."
                )

                return

            owner = load_owner()

            if (
                new_username
                != current_username
                and new_username
                == owner.get(
                    "username",
                    ""
                )
            ):

                st.error(
                    "This username belongs to the owner."
                )

                return

            if (
                new_username
                != current_username
                and new_username in users
            ):

                st.error(
                    "Username already exists."
                )

                return

            # -----------------------------------------------
            # Password
            # -----------------------------------------------

            if new_password:

                if new_password != confirm_password:

                    st.error(
                        "New passwords do not match."
                    )

                    return

                final_password = (
                    hash_password(
                        new_password
                    )
                )

            else:

                final_password = user.password

            # -----------------------------------------------
            # Remove old username
            # -----------------------------------------------

            if new_username != current_username:

                del users[
                    current_username
                ]

            updated_user = User(
                username=new_username,
                password=final_password,
                full_name=full_name
            )

            users[new_username] = (
                updated_user
            )

            StorageManager.save_users(
                users
            )

            st.session_state.username = (
                new_username
            )

            st.session_state.full_name = (
                full_name
            )

            st.success(
                "Profile updated successfully."
            )

            st.rerun()


# ============================================================
# BOOKS
# ============================================================

def all_books_page(df):

    section_title(
        "📚 All Books",
        "Books imported from the library transaction dataset."
    )

    books, records = load_library_data(
        df
    )

    if not books:

        st.info(
            "No books available."
        )

        return

    data = []

    for book in books.values():

        data.append({
            "Book ID": book.book_id,
            "Title": book.title,
            "Author": book.author,
            "Category": book.category,
            "Available Copies": book.available_copies
        })

    st.dataframe(
        pd.DataFrame(data),
        use_container_width=True,
        hide_index=True
    )


def add_book_page(df):

    section_title(
        "➕ Add Book"
    )

    books, records = load_library_data(
        df
    )

    with st.form(
        "add_book_form"
    ):

        book_id = st.text_input(
            "Book ID"
        )

        title = st.text_input(
            "Title"
        )

        author = st.text_input(
            "Author"
        )

        category = st.text_input(
            "Category"
        )

        copies = st.number_input(
            "Available Copies",
            min_value=0,
            step=1
        )

        submitted = st.form_submit_button(
            "Add Book"
        )

        if submitted:

            book_id = book_id.strip()

            if not book_id or not title.strip():

                st.error(
                    "Book ID and Title are required."
                )

                return

            if book_id in books:

                st.error(
                    "Book ID already exists."
                )

                return

            book = Book(
                book_id=book_id,
                title=title.strip(),
                author=author.strip() or "Unknown",
                category=category.strip() or "Unknown",
                available_copies=int(copies)
            )

            books[book_id] = book

            save_library_data(
                books,
                records
            )

            st.success(
                "Book added successfully."
            )

            st.rerun()


def update_book_page(df):

    section_title(
        "✏️ Update Book"
    )

    books, records = load_library_data(
        df
    )

    if not books:

        st.info(
            "No books available."
        )

        return

    book_id = st.selectbox(
        "Select Book",
        list(books.keys())
    )

    book = books[book_id]

    with st.form(
        "update_book_form"
    ):

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
            value=int(
                book.available_copies
            ),
            step=1
        )

        submitted = st.form_submit_button(
            "Update Book"
        )

        if submitted:

            book.title = (
                title.strip()
                or "Unknown"
            )

            book.author = (
                author.strip()
                or "Unknown"
            )

            book.category = (
                category.strip()
                or "Unknown"
            )

            book.available_copies = (
                int(copies)
            )

            save_library_data(
                books,
                records
            )

            st.success(
                "Book updated successfully."
            )

            st.rerun()


def remove_book_page(df):

    section_title(
        "🗑️ Remove Book"
    )

    books, records = load_library_data(
        df
    )

    if not books:

        st.info(
            "No books available."
        )

        return

    book_id = st.selectbox(
        "Select Book",
        list(books.keys())
    )

    book = books[book_id]

    st.warning(
        f"You are about to delete: {book.title}"
    )

    # --------------------------------------------------------
    # Check if currently borrowed
    # --------------------------------------------------------

    active_records = [
        r for r in records
        if r.book_id == book_id
    ]

    if active_records:

        st.error(
            "This book currently has active borrowing records. "
            "Return the book before deleting it."
        )

        return

    if st.button(
        "🗑️ Delete Book",
        type="primary"
    ):

        del books[book_id]

        save_library_data(
            books,
            records
        )

        st.success(
            "Book deleted successfully."
        )

        st.rerun()


# ============================================================
# SYNC BOOKS FROM CSV
# ============================================================

def sync_books_page(df):

    section_title(
        "🔄 Sync Books From CSV",
        "Import the books from library_transactions.csv into the library inventory."
    )

    if df.empty:

        st.warning(
            "Please upload library_transactions.csv first."
        )

        return

    books, records = load_library_data()

    st.write(
        f"Books currently in system: **{len(books)}**"
    )

    csv_books = create_books_from_csv(
        df
    )

    st.write(
        f"Unique books found in CSV: **{len(csv_books)}**"
    )

    st.warning(
        """
        Syncing will replace the current book inventory
        with the unique books found in the CSV.

        Existing borrowing records will be preserved.
        """
    )

    confirm = st.checkbox(
        "I understand that the current book inventory will be replaced."
    )

    if confirm:

        if st.button(
            "🔄 Sync Books Now",
            type="primary"
        ):

            if not csv_books:

                st.error(
                    "No valid books found in the CSV."
                )

                return

            StorageManager.save_data(
                csv_books,
                records
            )

            st.success(
                f"{len(csv_books)} books imported successfully."
            )

            st.rerun()


# ============================================================
# BORROWING RECORDS
# ============================================================

def borrowing_records_page(df):

    section_title(
        "📋 Borrowing Records"
    )

    books, records = load_library_data(
        df
    )

    if not records:

        st.info(
            "No borrowing records yet."
        )

        return

    data = []

    for record in records:

        row = record.to_dict()

        if record.book_id in books:

            row["Title"] = books[
                record.book_id
            ].title

        data.append(row)

    st.dataframe(
        pd.DataFrame(data),
        use_container_width=True,
        hide_index=True
    )


# ============================================================
# DATA QUALITY
# ============================================================

def data_quality_report(df):

    return pd.DataFrame({

        "Column": df.columns,

        "Data Type": [
            str(df[col].dtype)
            for col in df.columns
        ],

        "Missing Values": [
            int(df[col].isna().sum())
            for col in df.columns
        ],

        "Missing %": [
            round(
                df[col].isna().mean() * 100,
                2
            )
            for col in df.columns
        ],

        "Unique Values": [
            int(
                df[col].nunique(
                    dropna=True
                )
            )
            for col in df.columns
        ]
    })


def invalid_transaction_ids(df):

    if "Transaction_ID" not in df.columns:

        return pd.DataFrame()

    pattern = r"^TRX-\d+$"

    mask = ~df[
        "Transaction_ID"
    ].astype("string").str.match(
        pattern,
        na=False
    )

    return df.loc[mask].copy()


def data_quality_page(
    df,
    source
):

    section_title(
        "🔎 Data Quality Assessment"
    )

    st.info(
        f"Data Source: {source}"
    )

    if df.empty:

        st.warning(
            "No dataset loaded."
        )

        return

    c1, c2, c3, c4 = st.columns(4)

    c1.metric(
        "Rows",
        len(df)
    )

    c2.metric(
        "Columns",
        len(df.columns)
    )

    c3.metric(
        "Duplicate Rows",
        int(df.duplicated().sum())
    )

    c4.metric(
        "Missing Cells",
        int(df.isna().sum().sum())
    )

    st.subheader(
        "Column Quality Report"
    )

    st.dataframe(
        data_quality_report(df),
        use_container_width=True,
        hide_index=True
    )

    st.subheader(
        "Duplicate Transaction IDs"
    )

    if "Transaction_ID" in df.columns:

        duplicates = df[
            df["Transaction_ID"]
            .duplicated(
                keep=False
            )
        ]

        if duplicates.empty:

            st.success(
                "No duplicate Transaction IDs found."
            )

        else:

            st.dataframe(
                duplicates,
                use_container_width=True,
                hide_index=True
            )

    st.subheader(
        "Invalid Transaction IDs"
    )

    invalid = invalid_transaction_ids(
        df
    )

    if invalid.empty:

        st.success(
            "No invalid Transaction IDs found."
        )

    else:

        st.dataframe(
            invalid,
            use_container_width=True,
            hide_index=True
        )


# ============================================================
# CLEANING
# ============================================================

def clean_transactions(df):

    clean = df.copy()

    clean = clean.drop_duplicates()

    for col in clean.select_dtypes(
        include=["object"]
    ).columns:

        clean[col] = clean[col].apply(
            normalize_text
        )

    for col in [
        "Category",
        "Author",
        "Member_Type"
    ]:

        if col in clean.columns:

            clean[col] = clean[
                col
            ].fillna(
                "Unknown"
            )

    if "Fine_Amount" in clean.columns:

        clean["Fine_Amount"] = pd.to_numeric(
            clean["Fine_Amount"],
            errors="coerce"
        )

        clean["Fine_Amount"] = (
            clean["Fine_Amount"]
            .fillna(0)
        )

        clean.loc[
            clean["Fine_Amount"] < 0,
            "Fine_Amount"
        ] = 0

    for col in [
        "Borrow_Date",
        "Due_Date",
        "Return_Date"
    ]:

        if col in clean.columns:

            clean[col] = pd.to_datetime(
                clean[col],
                errors="coerce"
            )

    if "Status" in clean.columns:

        clean["Status"] = (
            clean["Status"]
            .fillna("Unknown")
        )

    return clean


def data_cleaning_page(df):

    section_title(
        "🧹 Data Cleaning"
    )

    if df.empty:

        st.warning(
            "No dataset loaded."
        )

        return

    cleaned = clean_transactions(
        df
    )

    summary = pd.DataFrame({

        "Metric": [
            "Original Rows",
            "Cleaned Rows",
            "Removed Rows",
            "Original Missing Cells",
            "Cleaned Missing Cells"
        ],

        "Value": [
            len(df),
            len(cleaned),
            len(df) - len(cleaned),
            int(
                df.isna().sum().sum()
            ),
            int(
                cleaned.isna().sum().sum()
            )
        ]
    })

    st.dataframe(
        summary,
        use_container_width=True,
        hide_index=True
    )

    st.subheader(
        "Cleaning Decisions"
    )

    decisions = pd.DataFrame({

        "Problem": [
            "Duplicate rows",
            "Missing Category",
            "Missing Author",
            "Missing Member Type",
            "Invalid/negative fines",
            "Incorrect dates"
        ],

        "Solution": [
            "Remove exact duplicates",
            "Replace with Unknown",
            "Replace with Unknown",
            "Replace with Unknown",
            "Replace invalid values with 0",
            "Convert invalid dates to NaT"
        ]
    })

    st.dataframe(
        decisions,
        use_container_width=True,
        hide_index=True
    )

    st.subheader(
        "Cleaned Dataset"
    )

    st.dataframe(
        cleaned,
        use_container_width=True,
        hide_index=True
    )

    dataframe_download(
        cleaned,
        "cleaned_library_transactions.csv"
    )


# ============================================================
# FEATURE ENGINEERING
# ============================================================

def engineer_features(df):

    data = df.copy()

    if "Borrow_Date" in data.columns:

        data["Borrow_Year"] = (
            data["Borrow_Date"].dt.year
        )

        data["Borrow_Month"] = (
            data["Borrow_Date"].dt.month
        )

        data["Borrow_Month_Name"] = (
            data["Borrow_Date"]
            .dt.month_name()
        )

        data["Borrow_Day"] = (
            data["Borrow_Date"].dt.day
        )

        data["Borrow_Day_Name"] = (
            data["Borrow_Date"]
            .dt.day_name()
        )

        data["Borrow_Quarter"] = (
            data["Borrow_Date"].dt.quarter
        )

    if "Due_Date" in data.columns:

        data["Due_Year"] = (
            data["Due_Date"].dt.year
        )

    if (
        "Borrow_Date" in data.columns
        and "Return_Date" in data.columns
    ):

        data["Borrow_Duration_Days"] = (
            data["Return_Date"]
            - data["Borrow_Date"]
        ).dt.days

    if (
        "Due_Date" in data.columns
        and "Return_Date" in data.columns
    ):

        data["Days_Late"] = (
            data["Return_Date"]
            - data["Due_Date"]
        ).dt.days

        data["Days_Late"] = (
            data["Days_Late"]
            .fillna(0)
        )

    if "Status" in data.columns:

        status = (
            data["Status"]
            .astype("string")
            .str.lower()
        )

        data["Return_Status"] = np.select(
            [
                status.str.contains(
                    "borrow",
                    na=False
                ),
                status.str.contains(
                    "late",
                    na=False
                ),
                status.str.contains(
                    "on time",
                    na=False
                )
            ],
            [
                "Currently Borrowed",
                "Late",
                "On Time"
            ],
            default="Unknown"
        )

    if "Fine_Amount" in data.columns:

        data["Fine_Category"] = pd.cut(
            data["Fine_Amount"],
            bins=[
                -0.01,
                0,
                10,
                30,
                np.inf
            ],
            labels=[
                "No Fine",
                "Low",
                "Medium",
                "High"
            ]
        )

    return data


def feature_engineering_page(df):

    section_title(
        "⚙️ Feature Engineering"
    )

    if df.empty:
        return

    featured = engineer_features(
        clean_transactions(df)
    )

    original = set(df.columns)

    features = [
        col
        for col in featured.columns
        if col not in original
    ]

    st.dataframe(
        pd.DataFrame({
            "Feature": features
        }),
        use_container_width=True,
        hide_index=True
    )

    st.dataframe(
        featured,
        use_container_width=True,
        hide_index=True
    )


# ============================================================
# NUMPY
# ============================================================

def numpy_analysis(df):

    section_title(
        "🔢 NumPy Analysis"
    )

    if df.empty:
        return

    numeric = df.select_dtypes(
        include=np.number
    )

    if numeric.empty:

        st.info(
            "No numeric columns available."
        )

        return

    arr = numeric.to_numpy()

    st.write(
        "Array shape:",
        arr.shape
    )

    st.write(
        "First 10 rows:"
    )

    st.write(
        arr[:10]
    )

    st.subheader(
        "Indexing"
    )

    if len(arr) > 0:

        st.write(
            arr[0]
        )

    st.subheader(
        "Slicing"
    )

    st.write(
        arr[
            :5,
            :min(
                3,
                arr.shape[1]
            )
        ]
    )

    st.subheader(
        "Boolean Masking"
    )

    if "Fine_Amount" in df.columns:

        fine = pd.to_numeric(
            df["Fine_Amount"],
            errors="coerce"
        ).fillna(0).to_numpy()

        st.write(
            "Transactions with fines:",
            int(
                (fine > 0).sum()
            )
        )

    st.subheader(
        "Vectorization"
    )

    if "Fine_Amount" in df.columns:

        fine = pd.to_numeric(
            df["Fine_Amount"],
            errors="coerce"
        ).fillna(0).to_numpy()

        st.write(
            fine * 1.10
        )


# ============================================================
# PANDAS
# ============================================================

def pandas_analysis(df):

    section_title(
        "🐼 Pandas Analysis"
    )

    if df.empty:
        return

    clean = clean_transactions(
        df
    )

    if "Fine_Amount" in clean.columns:

        st.subheader(
            "Filtering"
        )

        filtered = clean[
            clean["Fine_Amount"] > 0
        ]

        st.dataframe(
            filtered,
            use_container_width=True,
            hide_index=True
        )

        st.subheader(
            "Sorting"
        )

        sorted_df = clean.sort_values(
            "Fine_Amount",
            ascending=False
        )

        st.dataframe(
            sorted_df.head(20),
            use_container_width=True,
            hide_index=True
        )

    if (
        "Category" in clean.columns
        and "Fine_Amount" in clean.columns
    ):

        st.subheader(
            "GroupBy & Aggregation"
        )

        grouped = (
            clean
            .groupby(
                "Category",
                dropna=False
            )
            .agg(
                Transactions=(
                    "Transaction_ID",
                    "count"
                ),
                Average_Fine=(
                    "Fine_Amount",
                    "mean"
                ),
                Total_Fine=(
                    "Fine_Amount",
                    "sum"
                )
            )
            .sort_values(
                "Total_Fine",
                ascending=False
            )
        )

        st.dataframe(
            grouped,
            use_container_width=True
        )

    if (
        "Member_Type" in clean.columns
        and "Category" in clean.columns
        and "Fine_Amount" in clean.columns
    ):

        st.subheader(
            "Pivot Table"
        )

        pivot = pd.pivot_table(
            clean,
            index="Member_Type",
            columns="Category",
            values="Fine_Amount",
            aggfunc="mean",
            fill_value=0
        )

        st.dataframe(
            pivot,
            use_container_width=True
        )


# ============================================================
# POLARS
# ============================================================

def polars_analysis(df):

    section_title(
        "⚡ Polars Analysis"
    )

    if not POLARS_AVAILABLE:

        st.error(
            "Polars is not installed."
        )

        return

    if df.empty:
        return

    clean = clean_transactions(
        df
    )

    polars_df = clean.copy()

    for col in polars_df.columns:

        if pd.api.types.is_datetime64_any_dtype(
            polars_df[col]
        ):

            polars_df[col] = (
                polars_df[col]
                .astype(str)
            )

    pl_df = pl.from_pandas(
        polars_df
    )

    st.write(
        pl_df.head(10)
    )

    selected = [
        col
        for col in [
            "Transaction_ID",
            "Book_ID",
            "Category",
            "Member_Type",
            "Fine_Amount"
        ]
        if col in pl_df.columns
    ]

    if selected:

        st.subheader(
            "Select"
        )

        st.write(
            pl_df
            .select(selected)
            .head(10)
        )

    if "Fine_Amount" in pl_df.columns:

        st.subheader(
            "Filter"
        )

        st.write(
            pl_df.filter(
                pl.col(
                    "Fine_Amount"
                ) > 0
            ).head(10)
        )

    if (
        "Category" in pl_df.columns
        and "Fine_Amount" in pl_df.columns
    ):

        st.subheader(
            "Aggregation"
        )

        result = (
            pl_df
            .group_by("Category")
            .agg([
                pl.len().alias(
                    "Transactions"
                ),
                pl.col(
                    "Fine_Amount"
                ).mean().alias(
                    "Average_Fine"
                ),
                pl.col(
                    "Fine_Amount"
                ).sum().alias(
                    "Total_Fine"
                )
            ])
            .sort(
                "Total_Fine",
                descending=True
            )
        )

        st.write(
            result
        )


# ============================================================
# EDA
# ============================================================

def eda_page(df):

    section_title(
        "📊 Exploratory Data Analysis"
    )

    if df.empty:
        return

    clean = clean_transactions(
        df
    )

    st.subheader(
        "1️⃣ Univariate Analysis"
    )

    col1, col2 = st.columns(2)

    with col1:

        if "Member_Type" in clean.columns:

            fig, ax = plt.subplots(
                figsize=(8, 5)
            )

            sns.countplot(
                data=clean,
                x="Member_Type",
                ax=ax
            )

            ax.set_title(
                "Transactions by Member Type"
            )

            ax.set_xlabel(
                "Member Type"
            )

            ax.set_ylabel(
                "Number of Transactions"
            )

            plt.xticks(
                rotation=30
            )

            st.pyplot(fig)

    with col2:

        if "Fine_Amount" in clean.columns:

            fig, ax = plt.subplots(
                figsize=(8, 5)
            )

            ax.hist(
                clean["Fine_Amount"],
                bins=10
            )

            ax.set_title(
                "Distribution of Fine Amount"
            )

            ax.set_xlabel(
                "Fine Amount"
            )

            ax.set_ylabel(
                "Number of Transactions"
            )

            st.pyplot(fig)

    st.subheader(
        "2️⃣ Bivariate Analysis"
    )

    if (
        "Category" in clean.columns
        and "Fine_Amount" in clean.columns
    ):

        category_fines = (
            clean
            .groupby(
                "Category"
            )["Fine_Amount"]
            .mean()
            .sort_values(
                ascending=False
            )
        )

        fig, ax = plt.subplots(
            figsize=(10, 5)
        )

        category_fines.plot(
            kind="bar",
            ax=ax
        )

        ax.set_title(
            "Average Fine by Category"
        )

        ax.set_xlabel(
            "Category"
        )

        ax.set_ylabel(
            "Average Fine"
        )

        plt.xticks(
            rotation=45
        )

        st.pyplot(fig)

    st.subheader(
        "3️⃣ Multivariate Analysis"
    )

    if (
        "Member_Type" in clean.columns
        and "Category" in clean.columns
        and "Fine_Amount" in clean.columns
    ):

        pivot = pd.pivot_table(
            clean,
            index="Member_Type",
            columns="Category",
            values="Fine_Amount",
            aggfunc="mean",
            fill_value=0
        )

        fig, ax = plt.subplots(
            figsize=(12, 6)
        )

        sns.heatmap(
            pivot,
            annot=True,
            fmt=".1f",
            ax=ax
        )

        ax.set_title(
            "Average Fine by Member Type and Category"
        )

        st.pyplot(fig)


# ============================================================
# STATISTICS
# ============================================================

def statistical_page(df):

    section_title(
        "📈 Statistical Analysis"
    )

    if df.empty:
        return

    clean = clean_transactions(
        df
    )

    numeric = clean.select_dtypes(
        include=np.number
    )

    if not numeric.empty:

        st.subheader(
            "Descriptive Statistics"
        )

        st.dataframe(
            numeric.describe().T,
            use_container_width=True
        )

    if len(numeric.columns) >= 2:

        st.subheader(
            "Correlation Matrix"
        )

        corr = numeric.corr()

        fig, ax = plt.subplots(
            figsize=(10, 6)
        )

        sns.heatmap(
            corr,
            annot=True,
            fmt=".2f",
            ax=ax
        )

        ax.set_title(
            "Correlation Matrix"
        )

        st.pyplot(fig)

    if (
        "Member_Type" in clean.columns
        and "Fine_Amount" in clean.columns
    ):

        st.subheader(
            "Group Comparison"
        )

        comparison = (
            clean
            .groupby(
                "Member_Type"
            )["Fine_Amount"]
            .agg([
                "count",
                "mean",
                "median",
                "std"
            ])
        )

        st.dataframe(
            comparison,
            use_container_width=True
        )


# ============================================================
# PLOTLY
# ============================================================

def plotly_dashboard(df):

    section_title(
        "📊 Interactive Plotly Dashboard"
    )

    if not PLOTLY_AVAILABLE:

        st.error(
            "Plotly is not installed."
        )

        return

    if df.empty:
        return

    clean = clean_transactions(
        df
    )

    c1, c2, c3, c4 = st.columns(4)

    c1.metric(
        "Transactions",
        len(clean)
    )

    total_fines = (
        clean["Fine_Amount"].sum()
        if "Fine_Amount" in clean.columns
        else 0
    )

    c2.metric(
        "Total Fines",
        f"{total_fines:.2f}"
    )

    late = 0

    if "Status" in clean.columns:

        late = clean[
            clean["Status"]
            .astype("string")
            .str.contains(
                "late",
                case=False,
                na=False
            )
        ].shape[0]

    c3.metric(
        "Late Transactions",
        late
    )

    categories = (
        clean["Category"].nunique()
        if "Category" in clean.columns
        else 0
    )

    c4.metric(
        "Categories",
        categories
    )

    if "Category" in clean.columns:

        counts = (
            clean["Category"]
            .value_counts()
            .reset_index()
        )

        counts.columns = [
            "Category",
            "Transactions"
        ]

        fig = px.bar(
            counts,
            x="Category",
            y="Transactions",
            title="Transactions by Category"
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )

    if "Member_Type" in clean.columns:

        counts = (
            clean["Member_Type"]
            .value_counts()
            .reset_index()
        )

        counts.columns = [
            "Member_Type",
            "Transactions"
        ]

        fig = px.pie(
            counts,
            names="Member_Type",
            values="Transactions",
            title="Transactions by Member Type"
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )

    if (
        "Category" in clean.columns
        and "Fine_Amount" in clean.columns
    ):

        fig = px.box(
            clean,
            x="Category",
            y="Fine_Amount",
            title="Fine Amount Distribution by Category"
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )


# ============================================================
# INSIGHTS
# ============================================================

def insights_page(df):

    section_title(
        "💡 Data Storytelling"
    )

    if df.empty:
        return

    clean = clean_transactions(
        df
    )

    if "Category" in clean.columns:

        category = (
            clean["Category"]
            .value_counts()
        )

        if not category.empty:

            st.write(
                f"📌 Most frequent category: **{category.idxmax()}**"
            )

    if "Member_Type" in clean.columns:

        members = (
            clean["Member_Type"]
            .value_counts()
        )

        if not members.empty:

            st.write(
                f"📌 Most frequent member type: **{members.idxmax()}**"
            )

    if "Fine_Amount" in clean.columns:

        st.write(
            f"💰 Total fines: **{clean['Fine_Amount'].sum():.2f}**"
        )

        st.write(
            f"📊 Average fine: **{clean['Fine_Amount'].mean():.2f}**"
        )

    st.subheader(
        "🎯 Recommendations"
    )

    st.markdown(
        """
        1. Monitor categories with high transaction volume.
        2. Investigate high fine values.
        3. Use transaction trends when planning book purchases.
        4. Continue checking missing and invalid data.
        5. Monitor borrowing activity over time.
        """
    )


# ============================================================
# EXPORT
# ============================================================

def export_page(df):

    section_title(
        "📤 Export Data"
    )

    if df.empty:

        st.warning(
            "No dataset loaded."
        )

        return

    clean = clean_transactions(
        df
    )

    featured = engineer_features(
        clean
    )

    dataframe_download(
        clean,
        "library_transactions_cleaned.csv"
    )

    dataframe_download(
        featured,
        "library_transactions_featured.csv"
    )

    dataframe_download(
        df,
        "library_transactions_original.csv"
    )


# ============================================================
# USER BOOK PAGES
# ============================================================

def available_books_page(df):

    section_title(
        "📚 Available Books"
    )

    books, records = load_library_data(
        df
    )

    available = [
        book.to_dict()
        for book in books.values()
        if book.available_copies > 0
    ]

    if not available:

        st.info(
            "No books are currently available."
        )

        return

    st.dataframe(
        pd.DataFrame(available),
        use_container_width=True,
        hide_index=True
    )


def search_books_page(df):

    section_title(
        "🔍 Search Books"
    )

    books, records = load_library_data(
        df
    )

    query = st.text_input(
        "Search by title, author, category or Book ID"
    )

    if not query:
        return

    query = query.lower()

    results = []

    for book in books.values():

        if (
            query in book.title.lower()
            or query in book.author.lower()
            or query in book.category.lower()
            or query in book.book_id.lower()
        ):

            results.append(
                book.to_dict()
            )

    if results:

        st.dataframe(
            pd.DataFrame(results),
            use_container_width=True,
            hide_index=True
        )

    else:

        st.warning(
            "No matching books found."
        )


def borrow_book_page(df):

    section_title(
        "📖 Borrow Book"
    )

    books, records = load_library_data(
        df
    )

    available = [
        book
        for book in books.values()
        if book.available_copies > 0
    ]

    if not available:

        st.info(
            "No books are currently available."
        )

        return

    options = {
        f"{book.book_id} - {book.title}":
        book.book_id
        for book in available
    }

    selected = st.selectbox(
        "Select Book",
        list(options.keys())
    )

    book_id = options[selected]

    if st.button(
        "📖 Borrow Book",
        use_container_width=True
    ):

        book = books[book_id]

        # -----------------------------------------------
        # Make sure the user doesn't already have it
        # -----------------------------------------------

        already_borrowed = any(
            record.username
            == st.session_state.username
            and record.book_id
            == book_id
            for record in records
        )

        if already_borrowed:

            st.warning(
                "You already borrowed this book."
            )

            return

        book.available_copies -= 1

        record_id = (
            f"R{len(records) + 1}"
        )

        record = BorrowRecord(
            record_id=record_id,
            book_id=book_id,
            borrower_name=(
                st.session_state.full_name
            ),
            username=(
                st.session_state.username
            ),
            borrow_date=str(
                date.today()
            )
        )

        records.append(
            record
        )

        save_library_data(
            books,
            records
        )

        st.success(
            f"You borrowed '{book.title}' successfully."
        )

        st.rerun()


def return_book_page(df):

    section_title(
        "↩️ Return Book"
    )

    books, records = load_library_data(
        df
    )

    username = (
        st.session_state.username
    )

    my_records = [
        record
        for record in records
        if record.username == username
    ]

    if not my_records:

        st.info(
            "You do not have any borrowed books."
        )

        return

    options = {
        f"{record.book_id} - "
        f"{books[record.book_id].title if record.book_id in books else 'Unknown'}":
        record
        for record in my_records
    }

    selected = st.selectbox(
        "Select Borrowed Book",
        list(options.keys())
    )

    record = options[selected]

    if st.button(
        "↩️ Return Book",
        use_container_width=True
    ):

        if record.book_id in books:

            books[
                record.book_id
            ].available_copies += 1

        records.remove(
            record
        )

        save_library_data(
            books,
            records
        )

        st.success(
            "Book returned successfully."
        )

        st.rerun()


def my_borrowed_books_page(df):

    section_title(
        "📖 My Borrowed Books"
    )

    books, records = load_library_data(
        df
    )

    username = (
        st.session_state.username
    )

    my_records = [
        record
        for record in records
        if record.username == username
    ]

    if not my_records:

        st.info(
            "You have no borrowed books."
        )

        return

    data = []

    for record in my_records:

        row = record.to_dict()

        row["Title"] = "Unknown"
        row["Author"] = "Unknown"

        if record.book_id in books:

            row["Title"] = books[
                record.book_id
            ].title

            row["Author"] = books[
                record.book_id
            ].author

        data.append(row)

    st.dataframe(
        pd.DataFrame(data),
        use_container_width=True,
        hide_index=True
    )


# ============================================================
# USER INSIGHTS
# ============================================================

def user_insights_page(df):

    section_title(
        "📊 Library Insights"
    )

    if df.empty:

        st.warning(
            "Please upload the transaction dataset."
        )

        return

    clean = clean_transactions(
        df
    )

    c1, c2, c3 = st.columns(3)

    c1.metric(
        "Transactions",
        len(clean)
    )

    c2.metric(
        "Average Fine",
        f"{clean['Fine_Amount'].mean():.2f}"
        if "Fine_Amount" in clean.columns
        else "0"
    )

    c3.metric(
        "Categories",
        clean["Category"].nunique()
        if "Category" in clean.columns
        else 0
    )

    if (
        PLOTLY_AVAILABLE
        and "Category" in clean.columns
        and "Fine_Amount" in clean.columns
    ):

        category = (
            clean
            .groupby(
                "Category"
            )["Fine_Amount"]
            .mean()
            .sort_values(
                ascending=False
            )
            .reset_index()
        )

        fig = px.bar(
            category,
            x="Category",
            y="Fine_Amount",
            title="Average Fine by Category"
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )


# ============================================================
# SIDEBAR
# ============================================================

def sidebar(
    df,
    source
):

    st.sidebar.markdown(
        "## 📚 Library System"
    )

    st.sidebar.success(
        f"👤 {st.session_state.full_name}"
    )

    st.sidebar.write(
        f"Role: **{st.session_state.role.title()}**"
    )

    st.sidebar.divider()

    st.sidebar.caption(
        "DATA SOURCE"
    )

    st.sidebar.info(
        source
    )

    st.sidebar.divider()

    if st.sidebar.button(
        "🚪 Logout",
        use_container_width=True
    ):

        st.session_state.logged_in = False
        st.session_state.role = None
        st.session_state.username = None
        st.session_state.full_name = None

        st.rerun()


# ============================================================
# OWNER APP
# ============================================================

def owner_app(
    df,
    source
):

    sidebar(
        df,
        source
    )

    pages = {

        "🏠 Dashboard":
            "dashboard",

        "📚 All Books":
            "all_books",

        "🔄 Sync Books From CSV":
            "sync",

        "➕ Add Book":
            "add_book",

        "✏️ Update Book":
            "update_book",

        "🗑️ Remove Book":
            "remove_book",

        "📋 Borrowing Records":
            "records",

        "👤 My Profile":
            "profile",

        "🔎 Data Quality":
            "quality",

        "🧹 Data Cleaning":
            "cleaning",

        "⚙️ Feature Engineering":
            "features",

        "🔢 NumPy":
            "numpy",

        "🐼 Pandas":
            "pandas",

        "⚡ Polars":
            "polars",

        "📊 EDA":
            "eda",

        "📈 Statistical Analysis":
            "statistics",

        "📊 Plotly Dashboard":
            "plotly",

        "💡 Insights":
            "insights",

        "📤 Export":
            "export"
    }

    page_name = st.sidebar.radio(
        "Navigation",
        list(pages.keys())
    )

    page = pages[page_name]

    # --------------------------------------------------------
    # Dashboard
    # --------------------------------------------------------

    if page == "dashboard":

        section_title(
            "🏠 Owner Dashboard",
            "Library Management System"
        )

        books, records = (
            load_library_data(df)
        )

        total_books = len(books)

        available_copies = sum(
            book.available_copies
            for book in books.values()
        )

        c1, c2, c3 = st.columns(3)

        c1.metric(
            "Books",
            total_books
        )

        c2.metric(
            "Available Copies",
            available_copies
        )

        c3.metric(
            "Borrowing Records",
            len(records)
        )

        if not df.empty:

            st.subheader(
                "Dataset Overview"
            )

            c1, c2, c3 = st.columns(3)

            c1.metric(
                "Transactions",
                len(df)
            )

            c2.metric(
                "Missing Cells",
                int(
                    df.isna().sum().sum()
                )
            )

            c3.metric(
                "Duplicate Rows",
                int(
                    df.duplicated().sum()
                )
            )

    elif page == "all_books":

        all_books_page(df)

    elif page == "sync":

        sync_books_page(df)

    elif page == "add_book":

        add_book_page(df)

    elif page == "update_book":

        update_book_page(df)

    elif page == "remove_book":

        remove_book_page(df)

    elif page == "records":

        borrowing_records_page(df)

    elif page == "profile":

        owner_profile_page()

    elif page == "quality":

        data_quality_page(
            df,
            source
        )

    elif page == "cleaning":

        data_cleaning_page(df)

    elif page == "features":

        feature_engineering_page(df)

    elif page == "numpy":

        numpy_analysis(df)

    elif page == "pandas":

        pandas_analysis(df)

    elif page == "polars":

        polars_analysis(df)

    elif page == "eda":

        eda_page(df)

    elif page == "statistics":

        statistical_page(df)

    elif page == "plotly":

        plotly_dashboard(df)

    elif page == "insights":

        insights_page(df)

    elif page == "export":

        export_page(df)


# ============================================================
# USER APP
# ============================================================

def user_app(
    df,
    source
):

    sidebar(
        df,
        source
    )

    pages = {

        "🏠 Home":
            "home",

        "📚 Available Books":
            "available",

        "🔍 Search Books":
            "search",

        "📖 Borrow Book":
            "borrow",

        "↩️ Return Book":
            "return",

        "📖 My Borrowed Books":
            "my_books",

        "📊 Library Insights":
            "insights",

        "👤 My Profile":
            "profile"
    }

    page_name = st.sidebar.radio(
        "Navigation",
        list(pages.keys())
    )

    page = pages[page_name]

    # --------------------------------------------------------
    # HOME
    # --------------------------------------------------------

    if page == "home":

        section_title(
            f"Welcome, {st.session_state.full_name} 👋"
        )

        books, records = (
            load_library_data(df)
        )

        available = sum(
            book.available_copies
            for book in books.values()
        )

        my_records = [
            record
            for record in records
            if record.username
            == st.session_state.username
        ]

        c1, c2, c3 = st.columns(3)

        c1.metric(
            "Total Books",
            len(books)
        )

        c2.metric(
            "Available Copies",
            available
        )

        c3.metric(
            "My Borrowed Books",
            len(my_records)
        )

        if (
            not df.empty
            and PLOTLY_AVAILABLE
            and "Category" in df.columns
        ):

            clean = clean_transactions(
                df
            )

            category = (
                clean["Category"]
                .value_counts()
                .reset_index()
            )

            category.columns = [
                "Category",
                "Transactions"
            ]

            fig = px.bar(
                category,
                x="Category",
                y="Transactions",
                title="Transactions by Category"
            )

            st.plotly_chart(
                fig,
                use_container_width=True
            )

    elif page == "available":

        available_books_page(df)

    elif page == "search":

        search_books_page(df)

    elif page == "borrow":

        borrow_book_page(df)

    elif page == "return":

        return_book_page(df)

    elif page == "my_books":

        my_borrowed_books_page(df)

    elif page == "insights":

        user_insights_page(df)

    elif page == "profile":

        user_profile_page()


# ============================================================
# MAIN
# ============================================================

def main():

    st.markdown(
        """
        <div class="title-box">

            <h1>
                📚 Library Management System
            </h1>

            <p>
                Module 3 — Data Wrangling,
                EDA & Visualization
            </p>

        </div>
        """,
        unsafe_allow_html=True
    )

    # ========================================================
    # CSV UPLOAD
    # ========================================================

    st.markdown(
        "### 📂 Library Transactions Dataset"
    )

    uploaded_file = st.file_uploader(
        "Upload library_transactions.csv",
        type=["csv"],
        help="Upload the CSV dataset used by Module 3."
    )

    df, source = read_transactions(
        uploaded_file
    )

    if not df.empty:

        df = standardize_columns(
            df
        )

        st.success(
            f"Dataset loaded successfully — "
            f"{len(df)} transactions."
        )

        st.caption(
            f"Shape: {df.shape[0]} rows × "
            f"{df.shape[1]} columns"
        )

    else:

        st.warning(
            "Please upload library_transactions.csv."
        )

    st.divider()

    # ========================================================
    # AUTH
    # ========================================================

    if not st.session_state.logged_in:

        login_page()

        return

    # ========================================================
    # APPLICATION
    # ========================================================

    if st.session_state.role == "owner":

        owner_app(
            df,
            source
        )

    elif st.session_state.role == "user":

        user_app(
            df,
            source
        )


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":

    main()
