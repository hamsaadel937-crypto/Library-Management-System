import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy import stats
from datetime import datetime
from pathlib import Path
import hashlib

try:
    import seaborn as sns
    SEABORN_AVAILABLE = True
except ImportError:
    SEABORN_AVAILABLE = False

try:
    import polars as pl
    POLARS_AVAILABLE = True
except ImportError:
    POLARS_AVAILABLE = False

try:
    import plotly.express as px
    import plotly.graph_objects as go
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False

from library_service import LibraryManager
from storage import (
    StorageManager,
    hash_password,
    verify_password
)
from models import (
    Book,
    User,
    LibraryError,
    DuplicateBookError,
    BookNotFoundError
)


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="Library Management System",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
.block-container {
    padding-top: 1.5rem;
}

[data-testid="stMetricValue"] {
    font-size: 1.7rem;
}

.stButton > button {
    width: 100%;
}

div[data-testid="stMetric"] {
    border: 1px solid rgba(128,128,128,.25);
    padding: 10px;
    border-radius: 10px;
}
</style>
""", unsafe_allow_html=True)


# ============================================================
# PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent
DEFAULT_CSV = BASE_DIR / "library_transactions.csv"


# ============================================================
# SESSION STATE
# ============================================================

defaults = {
    "logged_in": False,
    "role": None,
    "username": None,
    "full_name": None,
    "analysis_df": None,
    "clean_df": None,
    "data_loaded": False,
    "csv_source": str(DEFAULT_CSV)
}

for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value


# ============================================================
# BASIC HELPERS
# ============================================================

def title(text, subtitle=None):
    st.title(text)
    if subtitle:
        st.caption(subtitle)


def books_to_dataframe(books):
    rows = []

    for book in books:
        rows.append({
            "Book ID": book.book_id,
            "Title": book.title,
            "Author": book.author,
            "Category": book.category,
            "Available Copies": book.available_copies
        })

    return pd.DataFrame(rows)


def records_to_dataframe(records):
    rows = []

    for record in records:
        rows.append({
            "Record ID": record.record_id,
            "Book ID": record.book_id,
            "Borrower": record.borrower_name,
            "Username": record.username,
            "Borrow Date": record.borrow_date
        })

    return pd.DataFrame(rows)


def safe_first(series):
    values = (
        series.dropna()
        .astype(str)
        .str.strip()
    )

    values = values[values != ""]

    if len(values) == 0:
        return "Unknown"

    return values.iloc[0]


# ============================================================
# DATA LOADING
# ============================================================

@st.cache_data(show_spinner=False)
def read_csv_file(path):
    return pd.read_csv(path)


def standardize_columns(df):
    df = df.copy()

    new_columns = []

    for col in df.columns:
        col = str(col).strip()
        col = col.replace("**", "")
        col = col.replace(" ", "_")
        col = col.replace("-", "_")
        col = col.replace("/", "_")
        new_columns.append(col)

    df.columns = new_columns

    return df


def load_dataset():
    path = Path(st.session_state.csv_source)

    if not path.exists():
        return pd.DataFrame()

    try:
        df = read_csv_file(str(path))
        return standardize_columns(df)
    except Exception as e:
        st.error(f"Could not load dataset: {e}")
        return pd.DataFrame()


# ============================================================
# DATA QUALITY
# ============================================================

def data_quality_report(df):
    report = []

    for col in df.columns:
        report.append({
            "Column": col,
            "Data Type": str(df[col].dtype),
            "Missing Values": int(df[col].isna().sum()),
            "Missing %": round(
                df[col].isna().mean() * 100,
                2
            ),
            "Unique Values": int(df[col].nunique(dropna=True))
        })

    return pd.DataFrame(report)


def duplicate_transaction_ids(df):
    if "Transaction_ID" not in df.columns:
        return pd.DataFrame()

    duplicated = df[
        df["Transaction_ID"].duplicated(
            keep=False
        )
    ].copy()

    return duplicated.sort_values(
        "Transaction_ID"
    )


def invalid_values_report(df):
    problems = []

    if "Fine_Amount" in df.columns:
        fine = pd.to_numeric(
            df["Fine_Amount"],
            errors="coerce"
        )

        negative_count = int(
            (fine < 0).sum()
        )

        problems.append({
            "Check": "Negative Fine Amount",
            "Count": negative_count
        })

    if "Borrow_Date" in df.columns:
        borrow_dates = pd.to_datetime(
            df["Borrow_Date"],
            errors="coerce"
        )

        problems.append({
            "Check": "Invalid Borrow Dates",
            "Count": int(borrow_dates.isna().sum())
        })

    if "Due_Date" in df.columns:
        due_dates = pd.to_datetime(
            df["Due_Date"],
            errors="coerce"
        )

        problems.append({
            "Check": "Invalid Due Dates",
            "Count": int(due_dates.isna().sum())
        })

    if "Return_Date" in df.columns:
        return_dates = pd.to_datetime(
            df["Return_Date"],
            errors="coerce"
        )

        problems.append({
            "Check": "Invalid Return Dates",
            "Count": int(return_dates.isna().sum())
        })

    if "Book_ID" in df.columns:
        problems.append({
            "Check": "Missing Book IDs",
            "Count": int(df["Book_ID"].isna().sum())
        })

    return pd.DataFrame(problems)


def inconsistent_categories(df):
    if "Category" not in df.columns:
        return pd.DataFrame()

    result = (
        df["Category"]
        .fillna("Missing")
        .astype(str)
        .str.strip()
        .value_counts()
        .reset_index()
    )

    result.columns = [
        "Category",
        "Count"
    ]

    return result


# ============================================================
# DATA CLEANING
# ============================================================

def clean_transactions(df):
    clean = df.copy()

    # Remove exact duplicate rows
    clean = clean.drop_duplicates()

    # Strip text
    text_columns = [
        "Transaction_ID",
        "Book_ID",
        "Book_Title",
        "Category",
        "Author",
        "Member_ID",
        "Member_Type",
        "Status"
    ]

    for col in text_columns:
        if col in clean.columns:
            clean[col] = (
                clean[col]
                .astype("string")
                .str.strip()
            )

    # Replace formatting artifacts
    for col in [
        "Book_Title",
        "Category",
        "Author",
        "Member_Type",
        "Status"
    ]:
        if col in clean.columns:
            clean[col] = (
                clean[col]
                .astype("string")
                .str.replace(
                    r"\s+",
                    " ",
                    regex=True
                )
                .str.strip()
            )

    # Missing categorical information
    for col in [
        "Book_Title",
        "Category",
        "Author",
        "Member_Type",
        "Status"
    ]:
        if col in clean.columns:
            clean[col] = clean[col].fillna("Unknown")

    # Numeric Fine
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

    # Dates
    date_columns = [
        "Borrow_Date",
        "Due_Date",
        "Return_Date"
    ]

    for col in date_columns:
        if col in clean.columns:
            clean[col] = pd.to_datetime(
                clean[col],
                errors="coerce"
            )

    # Standardize status
    if "Status" in clean.columns:
        clean["Status"] = (
            clean["Status"]
            .astype(str)
            .str.strip()
            .str.title()
        )

    # Feature Engineering
    if "Borrow_Date" in clean.columns:
        clean["Borrow_Year"] = (
            clean["Borrow_Date"].dt.year
        )

        clean["Borrow_Month"] = (
            clean["Borrow_Date"].dt.month
        )

        clean["Borrow_Month_Name"] = (
            clean["Borrow_Date"]
            .dt.strftime("%B")
        )

        clean["Borrow_Day"] = (
            clean["Borrow_Date"].dt.day
        )

        clean["Borrow_Day_Name"] = (
            clean["Borrow_Date"]
            .dt.strftime("%A")
        )

    if (
        "Borrow_Date" in clean.columns
        and "Return_Date" in clean.columns
    ):
        clean["Borrow_Duration_Days"] = (
            clean["Return_Date"]
            - clean["Borrow_Date"]
        ).dt.days

        clean["Borrow_Duration_Days"] = (
            clean["Borrow_Duration_Days"]
            .clip(lower=0)
        )

    if (
        "Borrow_Date" in clean.columns
        and "Due_Date" in clean.columns
    ):
        clean["Due_Duration_Days"] = (
            clean["Due_Date"]
            - clean["Borrow_Date"]
        ).dt.days

    if "Fine_Amount" in clean.columns:
        clean["Fine_Group"] = pd.cut(
            clean["Fine_Amount"],
            bins=[
                -0.01,
                0,
                10,
                50,
                np.inf
            ],
            labels=[
                "No Fine",
                "Low",
                "Medium",
                "High"
            ]
        )

    return clean


# ============================================================
# OUTLIERS
# ============================================================

def iqr_outlier_info(series):
    values = pd.to_numeric(
        series,
        errors="coerce"
    ).dropna()

    if values.empty:
        return None

    q1 = values.quantile(0.25)
    q3 = values.quantile(0.75)
    iqr = q3 - q1

    lower = q1 - 1.5 * iqr
    upper = q3 + 1.5 * iqr

    mask = (
        (values < lower)
        | (values > upper)
    )

    return {
        "Q1": q1,
        "Q3": q3,
        "IQR": iqr,
        "Lower Bound": lower,
        "Upper Bound": upper,
        "Outlier Count": int(mask.sum()),
        "Total Values": int(len(values))
    }


# ============================================================
# CSV -> BOOK INVENTORY
# ============================================================

def create_books_from_dataset(df):
    if df.empty:
        return {}

    required = [
        "Book_ID",
        "Book_Title"
    ]

    for col in required:
        if col not in df.columns:
            return {}

    work = df.copy()

    work["Book_ID"] = (
        work["Book_ID"]
        .astype(str)
        .str.strip()
    )

    work = work[
        (work["Book_ID"] != "")
        & (work["Book_ID"].str.lower() != "nan")
    ]

    grouped = (
        work.groupby("Book_ID", sort=False)
        .agg({
            "Book_Title": safe_first,
            "Author": (
                safe_first
                if "Author" in work.columns
                else lambda x: "Unknown"
            ),
            "Category": (
                safe_first
                if "Category" in work.columns
                else lambda x: "Unknown"
            )
        })
        .reset_index()
    )

    books = {}

    for _, row in grouped.iterrows():

        book_id = str(
            row["Book_ID"]
        ).strip()

        title_value = str(
            row["Book_Title"]
        ).strip()

        author_value = str(
            row.get("Author", "Unknown")
        ).strip()

        category_value = str(
            row.get("Category", "Unknown")
        ).strip()

        if not title_value or title_value.lower() == "nan":
            title_value = "Unknown"

        if not author_value or author_value.lower() == "nan":
            author_value = "Unknown"

        if not category_value or category_value.lower() == "nan":
            category_value = "Unknown"

        books[book_id] = Book(
            book_id=book_id,
            title=title_value,
            author=author_value,
            category=category_value,
            available_copies=1
        )

    return books


def sync_books_from_csv(df, overwrite=True):
    books, records = StorageManager.load_data()

    new_books = create_books_from_dataset(df)

    if not new_books:
        return 0

    if not overwrite and books:
        return len(books)

    StorageManager.save_data(
        new_books,
        records
    )

    return len(new_books)


# ============================================================
# AUTO LOAD DATA
# ============================================================

df_raw = load_dataset()

if not df_raw.empty:

    if not st.session_state.data_loaded:
        st.session_state.analysis_df = df_raw
        st.session_state.clean_df = clean_transactions(
            df_raw
        )
        st.session_state.data_loaded = True

    books_now, records_now = (
        StorageManager.load_data()
    )

    # Automatically create inventory from ALL unique books
    # only when inventory is empty.
    if not books_now:
        generated_books = create_books_from_dataset(
            df_raw
        )

        if generated_books:
            StorageManager.save_data(
                generated_books,
                records_now
            )


# ============================================================
# LOGIN
# ============================================================

if not st.session_state.logged_in:

    st.title("📚 Library Management System")
    st.subheader(
        "Library Management + Module 3 Data Analysis"
    )

    login_tab, register_tab = st.tabs(
        ["🔐 Login", "📝 Register"]
    )

    with login_tab:

        account_type = st.radio(
            "Account Type",
            ["👨‍💼 Owner", "👤 User"],
            horizontal=True
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
            "🔐 Login",
            use_container_width=True
        ):

            try:

                manager = LibraryManager()

                if account_type == "👨‍💼 Owner":

                    owner = manager.login_owner(
                        username,
                        password
                    )

                    st.session_state.logged_in = True
                    st.session_state.role = "owner"
                    st.session_state.username = owner["username"]
                    st.session_state.full_name = owner["full_name"]

                else:

                    user = manager.login_user(
                        username,
                        password
                    )

                    st.session_state.logged_in = True
                    st.session_state.role = "user"
                    st.session_state.username = user.username
                    st.session_state.full_name = user.full_name

                st.rerun()

            except Exception as e:
                st.error(str(e))

    with register_tab:

        st.subheader("📝 Create User Account")

        reg_username = st.text_input(
            "Username",
            key="register_username"
        )

        reg_full_name = st.text_input(
            "Full Name",
            key="register_full_name"
        )

        reg_password = st.text_input(
            "Password",
            type="password",
            key="register_password"
        )

        reg_confirm = st.text_input(
            "Confirm Password",
            type="password",
            key="register_confirm"
        )

        if st.button(
            "Create Account",
            use_container_width=True
        ):

            if reg_password != reg_confirm:
                st.error("Passwords do not match.")

            else:

                try:

                    manager = LibraryManager()

                    manager.register_user(
                        reg_username,
                        reg_password,
                        reg_full_name
                    )

                    st.success(
                        "Account created successfully."
                    )

                except Exception as e:
                    st.error(str(e))

    st.stop()


# ============================================================
# LOAD MANAGER
# ============================================================

manager = LibraryManager()

books = manager.get_all_books()
records = manager.records

books_df = books_to_dataframe(books)

if df_raw.empty:
    clean_df = pd.DataFrame()
else:
    clean_df = clean_transactions(df_raw)

st.session_state.clean_df = clean_df


# ============================================================
# SIDEBAR
# ============================================================

st.sidebar.title("📚 Library System")

st.sidebar.success(
    f"Welcome, {st.session_state.full_name}"
)

st.sidebar.caption(
    f"Role: {st.session_state.role.title()}"
)

st.sidebar.markdown("---")


if st.session_state.role == "owner":

    menu = [
        "🏠 Dashboard",
        "📚 All Books",
        "➕ Add Book",
        "✏️ Update Book",
        "🗑️ Remove Book",
        "🔄 Sync Books from CSV",
        "📋 Borrowing Records",
        "👤 My Profile",
        "🧹 Data Quality",
        "🧽 Data Cleaning",
        "🔧 Feature Engineering",
        "🔢 NumPy Analysis",
        "🐼 Pandas Wrangling",
        "⚡ Polars Analysis",
        "🔎 EDA",
        "📐 Statistical Analysis",
        "📊 Visualizations",
        "📈 Interactive Dashboard",
        "💡 Insights & Recommendations",
        "🏁 Final Conclusion",
        "📁 Export CSV"
    ]

else:

    menu = [
        "🏠 Home",
        "📚 Available Books",
        "🔎 Search Book",
        "📤 Borrow Book",
        "📥 Return Book",
        "📋 My Borrowed Books",
        "👤 My Profile"
    ]


choice = st.sidebar.selectbox(
    "Navigation",
    menu
)


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
# USER HOME
# ============================================================

if (
    st.session_state.role == "user"
    and choice == "🏠 Home"
):

    title(
        "🏠 Welcome to the Library",
        "Search, borrow and return books."
    )

    total_books = len(books)
    available = len(
        manager.get_available_books()
    )
    borrowed = len(
        manager.get_user_borrowed_books(
            st.session_state.username
        )
    )

    c1, c2, c3 = st.columns(3)

    c1.metric(
        "📚 Total Books",
        total_books
    )

    c2.metric(
        "✅ Available Books",
        available
    )

    c3.metric(
        "📤 My Borrowed Books",
        borrowed
    )

    if not books_df.empty:
        st.dataframe(
            books_df,
            use_container_width=True,
            hide_index=True
        )


# ============================================================
# AVAILABLE BOOKS
# ============================================================

elif (
    st.session_state.role == "user"
    and choice == "📚 Available Books"
):

    title(
        "📚 Available Books",
        "Books with at least one available copy."
    )

    available_books = manager.get_available_books()

    if available_books:
        st.dataframe(
            books_to_dataframe(available_books),
            use_container_width=True,
            hide_index=True
        )
    else:
        st.warning("No books are currently available.")


# ============================================================
# SEARCH
# ============================================================

elif choice == "🔎 Search Book":

    title(
        "🔎 Search Books",
        "Search by Book ID, title, author or category."
    )

    query = st.text_input(
        "Enter search text"
    )

    if query:

        results = manager.search_books(query)

        if results:

            st.dataframe(
                books_to_dataframe(results),
                use_container_width=True,
                hide_index=True
            )

        else:
            st.warning("No books found.")


# ============================================================
# OWNER DASHBOARD
# ============================================================

elif (
    st.session_state.role == "owner"
    and choice == "🏠 Dashboard"
):

    title(
        "👨‍💼 Owner Dashboard",
        "Library inventory and Module 3 overview."
    )

    total_titles = len(books)

    total_available = sum(
        book.available_copies
        for book in books
    )

    available_titles = sum(
        book.available_copies > 0
        for book in books
    )

    active_borrowing = len(records)

    c1, c2, c3, c4 = st.columns(4)

    c1.metric(
        "📚 Book Titles",
        total_titles
    )

    c2.metric(
        "📦 Available Copies",
        total_available
    )

    c3.metric(
        "✅ Available Titles",
        available_titles
    )

    c4.metric(
        "📤 Active Borrowings",
        active_borrowing
    )

    st.markdown("---")

    if not books_df.empty:

        st.subheader("📚 Current Inventory")

        st.dataframe(
            books_df,
            use_container_width=True,
            hide_index=True
        )

    if not clean_df.empty:

        st.subheader(
            "📊 Dataset Overview"
        )

        d1, d2, d3, d4 = st.columns(4)

        d1.metric(
            "Transactions",
            len(clean_df)
        )

        d2.metric(
            "Unique Books",
            clean_df["Book_ID"].nunique()
            if "Book_ID" in clean_df.columns
            else 0
        )

        d3.metric(
            "Unique Members",
            clean_df["Member_ID"].nunique()
            if "Member_ID" in clean_df.columns
            else 0
        )

        d4.metric(
            "Total Fines",
            round(
                clean_df["Fine_Amount"].sum(),
                2
            )
            if "Fine_Amount" in clean_df.columns
            else 0
        )


# ============================================================
# ALL BOOKS
# ============================================================

elif (
    st.session_state.role == "owner"
    and choice == "📚 All Books"
):

    title(
        "📚 All Books",
        f"{len(books)} unique books in the inventory."
    )

    if not books_df.empty:
        st.dataframe(
            books_df,
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("No books found.")


# ============================================================
# ADD BOOK
# ============================================================

elif (
    st.session_state.role == "owner"
    and choice == "➕ Add Book"
):

    title("➕ Add New Book")

    c1, c2 = st.columns(2)

    with c1:

        book_id = st.text_input(
            "Book ID"
        )

        book_title = st.text_input(
            "Title"
        )

        author = st.text_input(
            "Author"
        )

    with c2:

        category = st.text_input(
            "Category"
        )

        copies = st.number_input(
            "Available Copies",
            min_value=0,
            value=1,
            step=1
        )

    if st.button(
        "➕ Add Book"
    ):

        try:

            manager.add_book(
                book_id,
                book_title,
                author,
                category,
                copies
            )

            st.success(
                "Book added successfully."
            )

            st.rerun()

        except Exception as e:
            st.error(str(e))


# ============================================================
# UPDATE BOOK
# ============================================================

elif (
    st.session_state.role == "owner"
    and choice == "✏️ Update Book"
):

    title("✏️ Update Book")

    if books:

        selected_id = st.selectbox(
            "Select Book",
            [book.book_id for book in books]
        )

        selected_book = manager.search_by_id(
            selected_id
        )

        c1, c2 = st.columns(2)

        with c1:

            new_title = st.text_input(
                "Title",
                value=selected_book.title
            )

            new_author = st.text_input(
                "Author",
                value=selected_book.author
            )

        with c2:

            new_category = st.text_input(
                "Category",
                value=selected_book.category
            )

            new_copies = st.number_input(
                "Available Copies",
                min_value=0,
                value=int(
                    selected_book.available_copies
                )
            )

        if st.button(
            "💾 Save Changes"
        ):

            try:

                manager.update_book(
                    selected_id,
                    new_title,
                    new_author,
                    new_category,
                    new_copies
                )

                st.success(
                    "Book updated successfully."
                )

                st.rerun()

            except Exception as e:
                st.error(str(e))

    else:
        st.info("No books available.")


# ============================================================
# REMOVE BOOK
# ============================================================

elif (
    st.session_state.role == "owner"
    and choice == "🗑️ Remove Book"
):

    title("🗑️ Remove Book")

    if books:

        selected_id = st.selectbox(
            "Select Book",
            [book.book_id for book in books]
        )

        selected = manager.search_by_id(
            selected_id
        )

        st.warning(
            f"You are removing: {selected.title}"
        )

        if st.button(
            "🗑️ Delete Book"
        ):

            try:

                manager.remove_book(
                    selected_id
                )

                st.success(
                    "Book removed successfully."
                )

                st.rerun()

            except Exception as e:
                st.error(str(e))

    else:
        st.info("No books available.")


# ============================================================
# SYNC BOOKS
# ============================================================

elif (
    st.session_state.role == "owner"
    and choice == "🔄 Sync Books from CSV"
):

    title(
        "🔄 Sync Books from CSV",
        "Rebuild the library inventory from unique Book IDs in the dataset."
    )

    if clean_df.empty:

        st.error(
            "Dataset could not be loaded."
        )

    else:

        unique_count = (
            clean_df["Book_ID"].nunique()
            if "Book_ID" in clean_df.columns
            else 0
        )

        st.metric(
            "Unique Books in Dataset",
            unique_count
        )

        st.warning(
            "Sync will rebuild the current book inventory from the CSV."
        )

        if st.button(
            "🔄 Sync Entire Inventory"
        ):

            count = sync_books_from_csv(
                clean_df,
                overwrite=True
            )

            st.success(
                f"{count} unique books imported successfully."
            )

            st.rerun()


# ============================================================
# BORROWING RECORDS
# ============================================================

elif (
    st.session_state.role == "owner"
    and choice == "📋 Borrowing Records"
):

    title(
        "📋 Active Borrowing Records"
    )

    if records:

        records_df = records_to_dataframe(
            records
        )

        st.dataframe(
            records_df,
            use_container_width=True,
            hide_index=True
        )

    else:
        st.info(
            "No active borrowing records."
        )


# ============================================================
# USER BORROW
# ============================================================

elif (
    st.session_state.role == "user"
    and choice == "📤 Borrow Book"
):

    title(
        "📤 Borrow Book",
        "Borrow one available copy."
    )

    available_books = manager.get_available_books()

    if not available_books:

        st.warning(
            "No books are currently available."
        )

    else:

        selected_id = st.selectbox(
            "Select Book",
            [
                book.book_id
                for book in available_books
            ]
        )

        selected = manager.search_by_id(
            selected_id
        )

        st.write(
            f"**Title:** {selected.title}"
        )

        st.write(
            f"**Author:** {selected.author}"
        )

        st.write(
            f"**Category:** {selected.category}"
        )

        st.write(
            f"**Available Copies:** "
            f"{selected.available_copies}"
        )

        if st.button(
            "📤 Borrow This Book"
        ):

            try:

                manager.borrow_book(
                    selected_id,
                    st.session_state.full_name,
                    st.session_state.username
                )

                st.success(
                    "Book borrowed successfully."
                )

                st.rerun()

            except Exception as e:
                st.error(str(e))


# ============================================================
# USER RETURN
# ============================================================

elif (
    st.session_state.role == "user"
    and choice == "📥 Return Book"
):

    title(
        "📥 Return Book"
    )

    borrowed = manager.get_user_borrowed_books(
        st.session_state.username
    )

    if not borrowed:

        st.info(
            "You have no active borrowed books."
        )

    else:

        selected_record = st.selectbox(
            "Select borrowed book",
            [
                record.record_id
                for record in borrowed
            ]
        )

        record = next(
            r for r in borrowed
            if r.record_id == selected_record
        )

        book = (
            manager.books.get(
                record.book_id
            )
        )

        if book:
            st.write(
                f"**Book:** {book.title}"
            )

        if st.button(
            "📥 Return Book"
        ):

            try:

                manager.return_book(
                    record.book_id,
                    username=st.session_state.username
                )

                st.success(
                    "Book returned successfully."
                )

                st.rerun()

            except Exception as e:
                st.error(str(e))


# ============================================================
# USER BORROWED
# ============================================================

elif (
    st.session_state.role == "user"
    and choice == "📋 My Borrowed Books"
):

    title(
        "📋 My Borrowed Books"
    )

    borrowed = manager.get_user_borrowed_books(
        st.session_state.username
    )

    if borrowed:

        rows = []

        for record in borrowed:

            book = manager.books.get(
                record.book_id
            )

            rows.append({
                "Record ID": record.record_id,
                "Book ID": record.book_id,
                "Title": (
                    book.title
                    if book else "Unknown"
                ),
                "Author": (
                    book.author
                    if book else "Unknown"
                ),
                "Borrow Date": record.borrow_date
            })

        st.dataframe(
            pd.DataFrame(rows),
            use_container_width=True,
            hide_index=True
        )

    else:
        st.info(
            "You have no active borrowed books."
        )


# ============================================================
# PROFILE - OWNER
# ============================================================

elif (
    st.session_state.role == "owner"
    and choice == "👤 My Profile"
):

    title(
        "👤 Owner Profile",
        "Update your personal information and password."
    )

    owner = StorageManager.load_owner_profile()

    with st.form("owner_profile_form"):

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

        st.markdown("### 🔐 Change Password")

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

        save = st.form_submit_button(
            "💾 Save Profile"
        )

    if save:

        if not verify_password(
            current_password,
            owner.get("password", "")
        ):
            st.error(
                "Current password is incorrect."
            )

        elif not username.strip():
            st.error(
                "Username cannot be empty."
            )

        elif not full_name.strip():
            st.error(
                "Full name cannot be empty."
            )

        elif (
            new_password
            and new_password != confirm_password
        ):
            st.error(
                "New passwords do not match."
            )

        elif (
            new_password
            and len(new_password) < 6
        ):
            st.error(
                "New password must contain at least 6 characters."
            )

        else:

            users = StorageManager.load_users()

            collision = any(
                u.lower() == username.strip().lower()
                and u.lower()
                != owner.get("username", "").lower()
                for u in users.keys()
            )

            if collision:

                st.error(
                    "This username is already used by a user."
                )

            else:

                owner["username"] = username.strip()
                owner["full_name"] = full_name.strip()

                if new_password:
                    owner["password"] = hash_password(
                        new_password
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
# PROFILE - USER
# ============================================================

elif (
    st.session_state.role == "user"
    and choice == "👤 My Profile"
):

    title(
        "👤 My Profile",
        "Update your name, username and password."
    )

    users = StorageManager.load_users()

    current_username = (
        st.session_state.username
    )

    user = users.get(
        current_username
    )

    if user is None:

        st.error(
            "User profile not found."
        )

    else:

        with st.form("user_profile_form"):

            full_name = st.text_input(
                "Full Name",
                value=user.full_name
            )

            username = st.text_input(
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

            save = st.form_submit_button(
                "💾 Save Profile"
            )

        if save:

            if not verify_password(
                current_password,
                user.password
            ):

                st.error(
                    "Current password is incorrect."
                )

            elif not username.strip():

                st.error(
                    "Username cannot be empty."
                )

            elif not full_name.strip():

                st.error(
                    "Full name cannot be empty."
                )

            elif (
                new_password
                and new_password != confirm_password
            ):

                st.error(
                    "New passwords do not match."
                )

            elif (
                new_password
                and len(new_password) < 6
            ):

                st.error(
                    "New password must contain at least 6 characters."
                )

            else:

                owner = (
                    StorageManager.load_owner_profile()
                )

                owner_username = (
                    owner.get(
                        "username",
                        ""
                    ).lower()
                )

                if (
                    username.strip().lower()
                    == owner_username
                ):

                    st.error(
                        "This username belongs to the owner."
                    )

                else:

                    collision = any(
                        u.lower()
                        == username.strip().lower()
                        and u != current_username
                        for u in users.keys()
                    )

                    if collision:

                        st.error(
                            "Username already exists."
                        )

                    else:

                        final_password = (
                            hash_password(
                                new_password
                            )
                            if new_password
                            else user.password
                        )

                        updated_user = User(
                            username=username.strip(),
                            password=final_password,
                            full_name=full_name.strip()
                        )

                        if (
                            username.strip()
                            != current_username
                        ):

                            del users[
                                current_username
                            ]

                            for record in manager.records:

                                if (
                                    record.username
                                    == current_username
                                ):
                                    record.username = (
                                        username.strip()
                                    )

                        users[
                            username.strip()
                        ] = updated_user

                        StorageManager.save_users(
                            users
                        )

                        StorageManager.save_data(
                            manager.books,
                            manager.records
                        )

                        st.session_state.username = (
                            username.strip()
                        )

                        st.session_state.full_name = (
                            full_name.strip()
                        )

                        st.success(
                            "Profile updated successfully."
                        )

                        st.rerun()


# ============================================================
# DATA QUALITY
# ============================================================

elif (
    st.session_state.role == "owner"
    and choice == "🧹 Data Quality"
):

    title(
        "🧹 Data Quality Assessment",
        "Inspect the raw dataset before cleaning."
    )

    if df_raw.empty:

        st.error("Dataset not found.")

    else:

        c1, c2, c3, c4 = st.columns(4)

        c1.metric(
            "Rows",
            len(df_raw)
        )

        c2.metric(
            "Columns",
            len(df_raw.columns)
        )

        c3.metric(
            "Duplicate Rows",
            int(df_raw.duplicated().sum())
        )

        c4.metric(
            "Missing Cells",
            int(df_raw.isna().sum().sum())
        )

        st.subheader(
            "Column Quality Report"
        )

        st.dataframe(
            data_quality_report(df_raw),
            use_container_width=True,
            hide_index=True
        )

        st.subheader(
            "Duplicate Transaction IDs"
        )

        duplicate_ids = duplicate_transaction_ids(
            df_raw
        )

        if duplicate_ids.empty:
            st.success(
                "No duplicate Transaction IDs found."
            )
        else:
            st.dataframe(
                duplicate_ids,
                use_container_width=True,
                hide_index=True
            )

        st.subheader(
            "Invalid Values"
        )

        invalid_df = invalid_values_report(
            df_raw
        )

        if not invalid_df.empty:
            st.dataframe(
                invalid_df,
                use_container_width=True,
                hide_index=True
            )

        st.subheader(
            "Category Distribution / Consistency"
        )

        category_df = inconsistent_categories(
            df_raw
        )

        if not category_df.empty:
            st.dataframe(
                category_df,
                use_container_width=True,
                hide_index=True
            )


# ============================================================
# DATA CLEANING
# ============================================================

elif (
    st.session_state.role == "owner"
    and choice == "🧽 Data Cleaning"
):

    title(
        "🧽 Data Cleaning",
        "Cleaned dataset used for all Module 3 analysis."
    )

    if clean_df.empty:

        st.error("Dataset not found.")

    else:

        c1, c2, c3, c4 = st.columns(4)

        c1.metric(
            "Raw Rows",
            len(df_raw)
        )

        c2.metric(
            "Clean Rows",
            len(clean_df)
        )

        c3.metric(
            "Rows Removed",
            len(df_raw) - len(clean_df)
        )

        c4.metric(
            "Remaining Missing Cells",
            int(clean_df.isna().sum().sum())
        )

        st.subheader(
            "Cleaning Operations"
        )

        st.markdown("""
        - Exact duplicate rows are removed.
        - Text fields are stripped and standardized.
        - Missing categorical values are represented as `Unknown`.
        - Numeric fine values are converted to numeric.
        - Invalid negative fines are replaced with `0`.
        - Date fields are converted to datetime.
        - Status values are standardized.
        - New analytical features are created from dates and numerical values.
        """)

        st.subheader(
            "Cleaned Dataset"
        )

        st.dataframe(
            clean_df,
            use_container_width=True,
            hide_index=True
        )

        csv_clean = clean_df.to_csv(
            index=False
        ).encode("utf-8")

        st.download_button(
            "⬇️ Download Cleaned Dataset",
            csv_clean,
            "cleaned_library_transactions.csv",
            "text/csv"
        )


# ============================================================
# FEATURE ENGINEERING
# ============================================================

elif (
    st.session_state.role == "owner"
    and choice == "🔧 Feature Engineering"
):

    title(
        "🔧 Feature Engineering & Transformation"
    )

    if clean_df.empty:

        st.error("Dataset not found.")

    else:

        engineered_columns = [
            col
            for col in [
                "Borrow_Year",
                "Borrow_Month",
                "Borrow_Month_Name",
                "Borrow_Day",
                "Borrow_Day_Name",
                "Borrow_Duration_Days",
                "Due_Duration_Days",
                "Fine_Group"
            ]
            if col in clean_df.columns
        ]

        st.write(
            "Created features:"
        )

        st.write(
            engineered_columns
        )

        if engineered_columns:

            st.dataframe(
                clean_df[
                    engineered_columns
                ].head(20),
                use_container_width=True,
                hide_index=True
            )


# ============================================================
# NUMPY ANALYSIS
# ============================================================

elif (
    st.session_state.role == "owner"
    and choice == "🔢 NumPy Analysis"
):

    title(
        "🔢 NumPy Analysis",
        "Arrays, indexing, slicing, masking, vectorization and statistics."
    )

    if clean_df.empty:

        st.error("Dataset not found.")

    elif "Fine_Amount" not in clean_df.columns:

        st.warning(
            "Fine_Amount is not available."
        )

    else:

        values = (
            clean_df["Fine_Amount"]
            .to_numpy(dtype=float)
        )

        st.subheader(
            "1. NumPy Array"
        )

        st.code(
            "fine_array = clean_df['Fine_Amount'].to_numpy()"
        )

        st.write(
            values[:20]
        )

        st.subheader(
            "2. Indexing"
        )

        st.write(
            "First value:",
            values[0] if len(values) else "N/A"
        )

        st.subheader(
            "3. Slicing"
        )

        st.write(
            values[:10]
        )

        st.subheader(
            "4. Boolean Masking"
        )

        high_fines = values[
            values > values.mean()
        ]

        st.write(
            high_fines[:20]
        )

        st.subheader(
            "5. Vectorization"
        )

        doubled = values * 2

        st.write(
            doubled[:20]
        )

        st.subheader(
            "6. NumPy Statistics"
        )

        c1, c2, c3, c4 = st.columns(4)

        c1.metric(
            "Mean",
            round(np.mean(values), 2)
        )

        c2.metric(
            "Median",
            round(np.median(values), 2)
        )

        c3.metric(
            "Std",
            round(np.std(values), 2)
        )

        c4.metric(
            "Max",
            round(np.max(values), 2)
        )


# ============================================================
# PANDAS WRANGLING
# ============================================================

elif (
    st.session_state.role == "owner"
    and choice == "🐼 Pandas Wrangling"
):

    title(
        "🐼 Pandas Data Wrangling"
    )

    if clean_df.empty:

        st.error("Dataset not found.")

    else:

        tabs = st.tabs([
            "Filtering",
            "Sorting",
            "GroupBy",
            "Aggregation",
            "Merge / Join",
            "Pivot Table",
            "Reshaping"
        ])

        with tabs[0]:

            st.subheader("Filtering")

            if "Fine_Amount" in clean_df.columns:

                filtered = clean_df[
                    clean_df["Fine_Amount"] > 0
                ]

                st.dataframe(
                    filtered.head(50),
                    use_container_width=True,
                    hide_index=True
                )

        with tabs[1]:

            st.subheader("Sorting")

            if "Fine_Amount" in clean_df.columns:

                sorted_df = clean_df.sort_values(
                    "Fine_Amount",
                    ascending=False
                )

                st.dataframe(
                    sorted_df.head(20),
                    use_container_width=True,
                    hide_index=True
                )

        with tabs[2]:

            st.subheader("GroupBy")

            if "Category" in clean_df.columns:

                grouped = (
                    clean_df
                    .groupby("Category")
                    .size()
                    .reset_index(
                        name="Transactions"
                    )
                    .sort_values(
                        "Transactions",
                        ascending=False
                    )
                )

                st.dataframe(
                    grouped,
                    use_container_width=True,
                    hide_index=True
                )

        with tabs[3]:

            st.subheader("Aggregation")

            if (
                "Category" in clean_df.columns
                and "Fine_Amount" in clean_df.columns
            ):

                aggregation = (
                    clean_df
                    .groupby("Category")
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
                    .reset_index()
                )

                st.dataframe(
                    aggregation,
                    use_container_width=True,
                    hide_index=True
                )

        with tabs[4]:

            st.subheader("Merge / Join")

            if (
                "Book_ID" in clean_df.columns
                and "Book_Title" in clean_df.columns
            ):

                books_table = (
                    clean_df[
                        [
                            "Book_ID",
                            "Book_Title",
                            "Author",
                            "Category"
                        ]
                    ]
                    .drop_duplicates("Book_ID")
                )

                transactions_table = clean_df[
                    [
                        "Transaction_ID",
                        "Book_ID",
                        "Member_ID",
                        "Status",
                        "Fine_Amount"
                    ]
                ]

                merged = pd.merge(
                    transactions_table,
                    books_table,
                    on="Book_ID",
                    how="left"
                )

                st.dataframe(
                    merged.head(50),
                    use_container_width=True,
                    hide_index=True
                )

        with tabs[5]:

            st.subheader("Pivot Table")

            if (
                "Category" in clean_df.columns
                and "Member_Type" in clean_df.columns
            ):

                pivot = pd.pivot_table(
                    clean_df,
                    index="Category",
                    columns="Member_Type",
                    values="Transaction_ID",
                    aggfunc="count",
                    fill_value=0
                )

                st.dataframe(
                    pivot,
                    use_container_width=True
                )

        with tabs[6]:

            st.subheader("Reshaping")

            if (
                "Category" in clean_df.columns
                and "Member_Type" in clean_df.columns
            ):

                reshaped = (
                    clean_df
                    .groupby(
                        [
                            "Category",
                            "Member_Type"
                        ]
                    )
                    .size()
                    .reset_index(
                        name="Transactions"
                    )
                )

                st.dataframe(
                    reshaped,
                    use_container_width=True,
                    hide_index=True
                )


# ============================================================
# POLARS
# ============================================================

elif (
    st.session_state.role == "owner"
    and choice == "⚡ Polars Analysis"
):

    title(
        "⚡ Polars Analysis",
        "Selected data-wrangling operations using Polars."
    )

    if not POLARS_AVAILABLE:

        st.error(
            "Polars is not installed. Run: pip install polars"
        )

    elif clean_df.empty:

        st.error("Dataset not found.")

    else:

        polars_df = pl.from_pandas(
            clean_df
        )

        st.subheader(
            "Polars DataFrame"
        )

        st.dataframe(
            polars_df.head(20).to_pandas(),
            use_container_width=True,
            hide_index=True
        )

        st.subheader(
            "Select Columns"
        )

        selected_columns = [
            col
            for col in [
                "Book_ID",
                "Book_Title",
                "Category",
                "Fine_Amount"
            ]
            if col in polars_df.columns
        ]

        if selected_columns:

            selected = polars_df.select(
                selected_columns
            )

            st.dataframe(
                selected.head(20).to_pandas(),
                use_container_width=True,
                hide_index=True
            )

        st.subheader(
            "Filtering"
        )

        if "Fine_Amount" in polars_df.columns:

            filtered = polars_df.filter(
                pl.col("Fine_Amount") > 0
            )

            st.dataframe(
                filtered.head(20).to_pandas(),
                use_container_width=True,
                hide_index=True
            )

        st.subheader(
            "Aggregation"
        )

        if (
            "Category" in polars_df.columns
            and "Fine_Amount" in polars_df.columns
        ):

            aggregation = (
                polars_df
                .group_by("Category")
                .agg([
                    pl.len().alias("Transactions"),
                    pl.col("Fine_Amount")
                    .mean()
                    .alias("Average_Fine"),
                    pl.col("Fine_Amount")
                    .sum()
                    .alias("Total_Fine")
                ])
                .sort(
                    "Transactions",
                    descending=True
                )
            )

            st.dataframe(
                aggregation.to_pandas(),
                use_container_width=True,
                hide_index=True
            )

        st.subheader(
            "Lazy API"
        )

        lazy_result = (
            polars_df
            .lazy()
            .filter(
                pl.col("Fine_Amount") >= 0
            )
            .group_by("Category")
            .agg(
                pl.col("Fine_Amount")
                .mean()
                .alias("Average_Fine")
            )
            .collect()
        )

        st.dataframe(
            lazy_result.to_pandas(),
            use_container_width=True,
            hide_index=True
        )

        st.subheader(
            "Pandas vs Polars"
        )

        comparison = pd.DataFrame({
            "Task": [
                "DataFrame",
                "Select",
                "Filter",
                "GroupBy",
                "Aggregation",
                "Lazy API"
            ],
            "Pandas": [
                "DataFrame",
                "df[[columns]]",
                "df[condition]",
                "groupby()",
                "agg()",
                "Not native"
            ],
            "Polars": [
                "DataFrame",
                "select()",
                "filter()",
                "group_by()",
                "agg()",
                "lazy().collect()"
            ]
        })

        st.dataframe(
            comparison,
            use_container_width=True,
            hide_index=True
        )


# ============================================================
# EDA
# ============================================================

elif (
    st.session_state.role == "owner"
    and choice == "🔎 EDA"
):

    title(
        "🔎 Exploratory Data Analysis",
        "Univariate, Bivariate and Multivariate analysis."
    )

    if clean_df.empty:

        st.error("Dataset not found.")

    else:

        eda_tabs = st.tabs([
            "Univariate",
            "Bivariate",
            "Multivariate"
        ])

        with eda_tabs[0]:

            st.subheader(
                "Univariate Analysis"
            )

            if "Fine_Amount" in clean_df.columns:

                st.write(
                    clean_df[
                        "Fine_Amount"
                    ].describe()
                )

                fig, ax = plt.subplots()

                ax.hist(
                    clean_df[
                        "Fine_Amount"
                    ],
                    bins=15
                )

                ax.set_title(
                    "Fine Amount Distribution"
                )

                ax.set_xlabel(
                    "Fine Amount"
                )

                ax.set_ylabel(
                    "Frequency"
                )

                st.pyplot(fig)

                st.info(
                    "This visualization shows the distribution of fine amounts."
                )

        with eda_tabs[1]:

            st.subheader(
                "Bivariate Analysis"
            )

            if (
                "Borrow_Duration_Days"
                in clean_df.columns
                and "Fine_Amount"
                in clean_df.columns
            ):

                temp = clean_df[
                    [
                        "Borrow_Duration_Days",
                        "Fine_Amount"
                    ]
                ].dropna()

                fig, ax = plt.subplots()

                ax.scatter(
                    temp[
                        "Borrow_Duration_Days"
                    ],
                    temp[
                        "Fine_Amount"
                    ],
                    alpha=0.6
                )

                ax.set_title(
                    "Borrow Duration vs Fine Amount"
                )

                ax.set_xlabel(
                    "Borrow Duration (Days)"
                )

                ax.set_ylabel(
                    "Fine Amount"
                )

                st.pyplot(fig)

                correlation = temp.corr().iloc[0, 1]

                st.info(
                    f"Correlation between borrowing duration and fine amount: "
                    f"{correlation:.3f}"
                )

        with eda_tabs[2]:

            st.subheader(
                "Multivariate Analysis"
            )

            required = [
                "Category",
                "Member_Type",
                "Fine_Amount"
            ]

            if all(
                col in clean_df.columns
                for col in required
            ):

                multi = (
                    clean_df
                    .groupby(
                        [
                            "Category",
                            "Member_Type"
                        ]
                    )[
                        "Fine_Amount"
                    ]
                    .mean()
                    .reset_index()
                )

                st.dataframe(
                    multi,
                    use_container_width=True,
                    hide_index=True
                )

                if PLOTLY_AVAILABLE:

                    fig = px.bar(
                        multi,
                        x="Category",
                        y="Fine_Amount",
                        color="Member_Type",
                        barmode="group",
                        title=(
                            "Average Fine by Category "
                            "and Member Type"
                        )
                    )

                    st.plotly_chart(
                        fig,
                        use_container_width=True
                    )


# ============================================================
# STATISTICAL ANALYSIS
# ============================================================

elif (
    st.session_state.role == "owner"
    and choice == "📐 Statistical Analysis"
):

    title(
        "📐 Statistical Exploration"
    )

    if clean_df.empty:

        st.error("Dataset not found.")

    else:

        if "Fine_Amount" in clean_df.columns:

            values = (
                pd.to_numeric(
                    clean_df["Fine_Amount"],
                    errors="coerce"
                )
                .dropna()
                .to_numpy()
            )

            st.subheader(
                "Descriptive Statistics"
            )

            c1, c2, c3, c4 = st.columns(4)

            c1.metric(
                "Mean",
                round(np.mean(values), 2)
            )

            c2.metric(
                "Median",
                round(np.median(values), 2)
            )

            c3.metric(
                "Variance",
                round(np.var(values), 2)
            )

            c4.metric(
                "Std",
                round(np.std(values), 2)
            )

            st.write(
                "Mode:",
                (
                    stats.mode(
                        values,
                        keepdims=True
                    ).mode[0]
                    if len(values)
                    else "N/A"
                )
            )

            st.write(
                "Range:",
                round(
                    np.max(values)
                    - np.min(values),
                    2
                )
            )

            st.write(
                "Skewness:",
                round(
                    stats.skew(values),
                    3
                )
            )

            st.subheader(
                "Quartiles & IQR"
            )

            q1 = np.percentile(
                values,
                25
            )

            q2 = np.percentile(
                values,
                50
            )

            q3 = np.percentile(
                values,
                75
            )

            iqr = q3 - q1

            st.dataframe(
                pd.DataFrame({
                    "Statistic": [
                        "Q1",
                        "Median",
                        "Q3",
                        "IQR"
                    ],
                    "Value": [
                        q1,
                        q2,
                        q3,
                        iqr
                    ]
                }),
                use_container_width=True,
                hide_index=True
            )

            st.subheader(
                "Outlier Detection - IQR"
            )

            info = iqr_outlier_info(
                clean_df["Fine_Amount"]
            )

            if info:

                st.write(
                    f"Lower Bound: {info['Lower Bound']:.2f}"
                )

                st.write(
                    f"Upper Bound: {info['Upper Bound']:.2f}"
                )

                st.write(
                    f"Potential Outliers: {info['Outlier Count']}"
                )

            st.subheader(
                "Probability"
            )

            positive_fines = np.sum(
                values > 0
            )

            probability = (
                positive_fines / len(values)
                if len(values)
                else 0
            )

            st.metric(
                "P(Fine > 0)",
                round(probability, 4)
            )

            st.subheader(
                "Expected Value"
            )

            st.write(
                round(
                    np.mean(values),
                    2
                )
            )

            st.subheader(
                "Sampling"
            )

            sample_size = min(
                30,
                len(values)
            )

            if sample_size > 0:

                sample = np.random.default_rng(
                    42
                ).choice(
                    values,
                    size=sample_size,
                    replace=False
                )

                st.write(
                    f"Random sample size: {sample_size}"
                )

                st.write(
                    sample
                )

            st.subheader(
                "95% Confidence Interval"
            )

            if len(values) > 1:

                mean = np.mean(values)
                sem = stats.sem(values)

                ci = stats.t.interval(
                    0.95,
                    len(values) - 1,
                    loc=mean,
                    scale=sem
                )

                st.write(
                    f"95% CI: "
                    f"({ci[0]:.2f}, {ci[1]:.2f})"
                )

        # Correlation
        numeric_columns = clean_df.select_dtypes(
            include=np.number
        ).columns.tolist()

        if len(numeric_columns) >= 2:

            st.subheader(
                "Correlation Matrix"
            )

            corr = clean_df[
                numeric_columns
            ].corr()

            st.dataframe(
                corr,
                use_container_width=True
            )

        # Hypothesis Test
        st.subheader(
            "Hypothesis Testing"
        )

        if "Fine_Amount" in clean_df.columns:

            values = (
                clean_df["Fine_Amount"]
                .dropna()
                .to_numpy()
            )

            if len(values) > 1:

                test_value = 0

                t_stat, p_value = stats.ttest_1samp(
                    values,
                    test_value
                )

                st.write(
                    f"One-sample t-test against mean = 0"
                )

                st.write(
                    f"t-statistic = {t_stat:.4f}"
                )

                st.write(
                    f"p-value = {p_value:.6f}"
                )

                if p_value < 0.05:

                    st.success(
                        "The result is statistically significant at α = 0.05."
                    )

                else:

                    st.info(
                        "The result is not statistically significant at α = 0.05."
                    )

        # ANOVA
        if (
            "Category" in clean_df.columns
            and "Fine_Amount" in clean_df.columns
        ):

            st.subheader(
                "One-Way ANOVA"
            )

            groups = []

            for _, group in clean_df.groupby(
                "Category"
            ):

                values = (
                    pd.to_numeric(
                        group["Fine_Amount"],
                        errors="coerce"
                    )
                    .dropna()
                    .to_numpy()
                )

                if len(values) >= 2:
                    groups.append(values)

            if len(groups) >= 2:

                f_stat, p_value = stats.f_oneway(
                    *groups
                )

                st.write(
                    f"F-statistic = {f_stat:.4f}"
                )

                st.write(
                    f"p-value = {p_value:.6f}"
                )

                if p_value < 0.05:

                    st.success(
                        "There is a statistically significant difference "
                        "between at least two category means."
                    )

                else:

                    st.info(
                        "No statistically significant difference was detected "
                        "between the category means."
                    )

        # Linear Algebra
        st.subheader(
            "Linear Algebra with NumPy"
        )

        matrix = np.array([
            [1, 2],
            [3, 4]
        ])

        vector = np.array([
            [5],
            [6]
        ])

        st.write(
            "Matrix:"
        )

        st.write(matrix)

        st.write(
            "Matrix × Vector:"
        )

        st.write(
            matrix @ vector
        )


# ============================================================
# VISUALIZATIONS
# ============================================================

elif (
    st.session_state.role == "owner"
    and choice == "📊 Visualizations"
):

    title(
        "📊 Data Visualization",
        "Charts selected according to analytical questions."
    )

    if clean_df.empty:

        st.error("Dataset not found.")

    else:

        chart = st.selectbox(
            "Choose Visualization",
            [
                "Bar Chart - Transactions by Category",
                "Histogram - Fine Amount",
                "Line Chart - Monthly Transactions",
                "Box Plot - Fine Amount",
                "Scatter Plot - Borrow Duration vs Fine",
                "Heatmap - Correlation"
            ]
        )

        # BAR
        if chart.startswith("Bar"):

            if "Category" in clean_df.columns:

                data = (
                    clean_df["Category"]
                    .value_counts()
                    .sort_values(
                        ascending=False
                    )
                )

                fig, ax = plt.subplots()

                ax.bar(
                    data.index,
                    data.values
                )

                ax.set_title(
                    "Transactions by Category"
                )

                ax.set_xlabel(
                    "Category"
                )

                ax.set_ylabel(
                    "Number of Transactions"
                )

                plt.xticks(
                    rotation=45,
                    ha="right"
                )

                st.pyplot(fig)

                st.info(
                    "Purpose: compare borrowing activity across book categories."
                )

        # HISTOGRAM
        elif chart.startswith("Histogram"):

            if "Fine_Amount" in clean_df.columns:

                fig, ax = plt.subplots()

                ax.hist(
                    clean_df[
                        "Fine_Amount"
                    ].dropna(),
                    bins=15
                )

                ax.set_title(
                    "Fine Amount Distribution"
                )

                ax.set_xlabel(
                    "Fine Amount"
                )

                ax.set_ylabel(
                    "Frequency"
                )

                st.pyplot(fig)

                st.info(
                    "Purpose: understand the distribution of fine amounts."
                )

        # LINE
        elif chart.startswith("Line"):

            if (
                "Borrow_Date" in clean_df.columns
            ):

                monthly = (
                    clean_df
                    .dropna(
                        subset=[
                            "Borrow_Date"
                        ]
                    )
                    .set_index(
                        "Borrow_Date"
                    )
                    .resample("ME")
                    .size()
                    .reset_index(
                        name="Transactions"
                    )
                )

                fig, ax = plt.subplots()

                ax.plot(
                    monthly[
                        "Borrow_Date"
                    ],
                    monthly[
                        "Transactions"
                    ],
                    marker="o"
                )

                ax.set_title(
                    "Monthly Borrowing Transactions"
                )

                ax.set_xlabel(
                    "Month"
                )

                ax.set_ylabel(
                    "Transactions"
                )

                plt.xticks(
                    rotation=45
                )

                st.pyplot(fig)

                st.info(
                    "Purpose: identify borrowing trends over time."
                )

        # BOX
        elif chart.startswith("Box"):

            if "Fine_Amount" in clean_df.columns:

                values = (
                    clean_df[
                        "Fine_Amount"
                    ]
                    .dropna()
                )

                fig, ax = plt.subplots()

                ax.boxplot(
                    values,
                    vert=True
                )

                ax.set_title(
                    "Box Plot of Fine Amount"
                )

                ax.set_ylabel(
                    "Fine Amount"
                )

                st.pyplot(fig)

                info = iqr_outlier_info(
                    values
                )

                if info:

                    st.info(
                        f"IQR = {info['IQR']:.2f} | "
                        f"Potential outliers = "
                        f"{info['Outlier Count']}"
                    )

        # SCATTER
        elif chart.startswith("Scatter"):

            if (
                "Borrow_Duration_Days"
                in clean_df.columns
                and "Fine_Amount"
                in clean_df.columns
            ):

                data = clean_df[
                    [
                        "Borrow_Duration_Days",
                        "Fine_Amount"
                    ]
                ].dropna()

                fig, ax = plt.subplots()

                ax.scatter(
                    data[
                        "Borrow_Duration_Days"
                    ],
                    data[
                        "Fine_Amount"
                    ],
                    alpha=0.6
                )

                ax.set_title(
                    "Borrow Duration vs Fine Amount"
                )

                ax.set_xlabel(
                    "Borrow Duration (Days)"
                )

                ax.set_ylabel(
                    "Fine Amount"
                )

                st.pyplot(fig)

                st.info(
                    "Purpose: investigate the relationship between "
                    "borrowing duration and fines."
                )

        # HEATMAP
        elif chart.startswith("Heatmap"):

            numeric = clean_df.select_dtypes(
                include=np.number
            )

            if numeric.shape[1] >= 2:

                corr = numeric.corr()

                if SEABORN_AVAILABLE:

                    fig, ax = plt.subplots(
                        figsize=(9, 6)
                    )

                    sns.heatmap(
                        corr,
                        annot=True,
                        fmt=".2f",
                        ax=ax
                    )

                    ax.set_title(
                        "Correlation Heatmap"
                    )

                    st.pyplot(fig)

                else:

                    st.dataframe(
                        corr,
                        use_container_width=True
                    )


# ============================================================
# PLOTLY DASHBOARD
# ============================================================

elif (
    st.session_state.role == "owner"
    and choice == "📈 Interactive Dashboard"
):

    title(
        "📈 Interactive Library Analytics Dashboard",
        "Interactive Plotly dashboard."
    )

    if not PLOTLY_AVAILABLE:

        st.error(
            "Plotly is not installed. Run: pip install plotly"
        )

    elif clean_df.empty:

        st.error("Dataset not found.")

    else:

        dashboard_df = clean_df.copy()

        # Filters
        c1, c2 = st.columns(2)

        if "Category" in dashboard_df.columns:

            categories = sorted(
                dashboard_df[
                    "Category"
                ]
                .dropna()
                .astype(str)
                .unique()
                .tolist()
            )

            with c1:

                selected_categories = st.multiselect(
                    "Category",
                    categories,
                    default=categories
                )

        else:

            selected_categories = []

        if "Member_Type" in dashboard_df.columns:

            member_types = sorted(
                dashboard_df[
                    "Member_Type"
                ]
                .dropna()
                .astype(str)
                .unique()
                .tolist()
            )

            with c2:

                selected_members = st.multiselect(
                    "Member Type",
                    member_types,
                    default=member_types
                )

        else:

            selected_members = []

        if selected_categories:

            dashboard_df = dashboard_df[
                dashboard_df["Category"]
                .astype(str)
                .isin(
                    selected_categories
                )
            ]

        if selected_members:

            dashboard_df = dashboard_df[
                dashboard_df["Member_Type"]
                .astype(str)
                .isin(
                    selected_members
                )
            ]

        total_transactions = len(
            dashboard_df
        )

        unique_books = (
            dashboard_df["Book_ID"].nunique()
            if "Book_ID" in dashboard_df.columns
            else 0
        )

        unique_members = (
            dashboard_df["Member_ID"].nunique()
            if "Member_ID" in dashboard_df.columns
            else 0
        )

        total_fines = (
            dashboard_df["Fine_Amount"].sum()
            if "Fine_Amount" in dashboard_df.columns
            else 0
        )

        m1, m2, m3, m4 = st.columns(4)

        m1.metric(
            "Transactions",
            total_transactions
        )

        m2.metric(
            "Unique Books",
            unique_books
        )

        m3.metric(
            "Unique Members",
            unique_members
        )

        m4.metric(
            "Total Fines",
            round(total_fines, 2)
        )

        # Monthly line
        if "Borrow_Date" in dashboard_df.columns:

            monthly = (
                dashboard_df
                .dropna(
                    subset=[
                        "Borrow_Date"
                    ]
                )
                .set_index(
                    "Borrow_Date"
                )
                .resample("ME")
                .size()
                .reset_index(
                    name="Transactions"
                )
            )

            fig = px.line(
                monthly,
                x="Borrow_Date",
                y="Transactions",
                markers=True,
                title="Monthly Borrowing Transactions"
            )

            st.plotly_chart(
                fig,
                use_container_width=True
            )

        c1, c2 = st.columns(2)

        if (
            "Category" in dashboard_df.columns
        ):

            category_counts = (
                dashboard_df[
                    "Category"
                ]
                .value_counts()
                .reset_index()
            )

            category_counts.columns = [
                "Category",
                "Transactions"
            ]

            fig = px.bar(
                category_counts,
                x="Category",
                y="Transactions",
                title="Transactions by Category"
            )

            with c1:
                st.plotly_chart(
                    fig,
                    use_container_width=True
                )

        if (
            "Member_Type"
            in dashboard_df.columns
        ):

            member_counts = (
                dashboard_df[
                    "Member_Type"
                ]
                .value_counts()
                .reset_index()
            )

            member_counts.columns = [
                "Member Type",
                "Transactions"
            ]

            fig = px.pie(
                member_counts,
                names="Member Type",
                values="Transactions",
                title="Member Type Distribution"
            )

            with c2:
                st.plotly_chart(
                    fig,
                    use_container_width=True
                )

        if (
            "Category" in dashboard_df.columns
            and "Fine_Amount"
            in dashboard_df.columns
        ):

            category_fines = (
                dashboard_df
                .groupby("Category")[
                    "Fine_Amount"
                ]
                .mean()
                .reset_index()
            )

            fig = px.bar(
                category_fines,
                x="Category",
                y="Fine_Amount",
                title="Average Fine by Category"
            )

            st.plotly_chart(
                fig,
                use_container_width=True
            )


# ============================================================
# INSIGHTS
# ============================================================

elif (
    st.session_state.role == "owner"
    and choice == "💡 Insights & Recommendations"
):

    title(
        "💡 Data Storytelling",
        "Data → Finding → Insight → Recommendation"
    )

    if clean_df.empty:

        st.error("Dataset not found.")

    else:

        st.subheader(
            "📌 Key Findings"
        )

        findings = []

        if "Category" in clean_df.columns:

            top_category = (
                clean_df[
                    "Category"
                ]
                .value_counts()
                .idxmax()
            )

            top_category_count = (
                clean_df[
                    "Category"
                ]
                .value_counts()
                .max()
            )

            findings.append(
                f"**Most active category:** "
                f"{top_category} "
                f"with {top_category_count} transactions."
            )

        if "Book_Title" in clean_df.columns:

            top_book = (
                clean_df[
                    "Book_Title"
                ]
                .value_counts()
                .idxmax()
            )

            top_book_count = (
                clean_df[
                    "Book_Title"
                ]
                .value_counts()
                .max()
            )

            findings.append(
                f"**Most borrowed title:** "
                f"{top_book} "
                f"with {top_book_count} transactions."
            )

        if "Member_Type" in clean_df.columns:

            top_member = (
                clean_df[
                    "Member_Type"
                ]
                .value_counts()
                .idxmax()
            )

            findings.append(
                f"**Most active member type:** "
                f"{top_member}."
            )

        if "Fine_Amount" in clean_df.columns:

            average_fine = (
                clean_df[
                    "Fine_Amount"
                ].mean()
            )

            total_fine = (
                clean_df[
                    "Fine_Amount"
                ].sum()
            )

            findings.append(
                f"**Average fine:** "
                f"{average_fine:.2f}."
            )

            findings.append(
                f"**Total recorded fines:** "
                f"{total_fine:.2f}."
            )

        for item in findings:
            st.markdown(
                f"- {item}"
            )

        st.markdown("---")

        st.subheader(
            "💡 Insights"
        )

        if "Category" in clean_df.columns:

            top_category = (
                clean_df[
                    "Category"
                ]
                .value_counts()
                .idxmax()
            )

            st.write(
                f"The high transaction volume for "
                f"**{top_category}** indicates stronger "
                f"library activity around this category."
            )

        if "Fine_Amount" in clean_df.columns:

            st.write(
                "Fine amounts can be used to identify "
                "borrowing behavior that may require "
                "better return-date awareness."
            )

        st.subheader(
            "🎯 Recommendations"
        )

        st.markdown("""
        - Increase availability of frequently borrowed books.
        - Monitor categories with consistently high demand.
        - Review books associated with repeated fines.
        - Improve reminders for due dates.
        - Use monthly borrowing trends to support inventory planning.
        - Continue monitoring data quality before future analysis.
        """)


# ============================================================
# FINAL CONCLUSION
# ============================================================

elif (
    st.session_state.role == "owner"
    and choice == "🏁 Final Conclusion"
):

    title(
        "🏁 Final Conclusion",
        "Module 3 final analytical summary."
    )

    if clean_df.empty:

        st.error("Dataset not found.")

    else:

        st.subheader(
            "📌 Key Findings"
        )

        if "Category" in clean_df.columns:

            category = (
                clean_df["Category"]
                .value_counts()
                .idxmax()
            )

            count = (
                clean_df["Category"]
                .value_counts()
                .max()
            )

            st.write(
                f"- The category with the highest "
                f"transaction activity is **{category}** "
                f"with **{count} transactions**."
            )

        if "Book_Title" in clean_df.columns:

            book = (
                clean_df["Book_Title"]
                .value_counts()
                .idxmax()
            )

            st.write(
                f"- The most frequently borrowed book "
                f"is **{book}**."
            )

        if "Fine_Amount" in clean_df.columns:

            st.write(
                f"- The average fine amount is "
                f"**{clean_df['Fine_Amount'].mean():.2f}**."
            )

            outlier_info = iqr_outlier_info(
                clean_df["Fine_Amount"]
            )

            if outlier_info:

                st.write(
                    f"- IQR analysis identified "
                    f"**{outlier_info['Outlier Count']}** "
                    f"potential fine outliers."
                )

        st.subheader(
            "🧹 Data Quality"
        )

        st.write(
            f"- The original dataset contains "
            f"**{len(df_raw)} rows**."
        )

        st.write(
            f"- Exact duplicate rows found: "
            f"**{int(df_raw.duplicated().sum())}**."
        )

        st.write(
            f"- Remaining missing cells after cleaning: "
            f"**{int(clean_df.isna().sum().sum())}**."
        )

        st.subheader(
            "📊 Analysis Performed"
        )

        st.markdown("""
        - Data Quality Assessment
        - Data Cleaning
        - Outlier Detection using IQR
        - Feature Engineering
        - NumPy Analysis
        - Pandas Data Wrangling
        - Polars Analysis and Lazy API
        - Univariate Analysis
        - Bivariate Analysis
        - Multivariate Analysis
        - Descriptive Statistics
        - Correlation
        - Probability
        - Sampling
        - Confidence Interval
        - Hypothesis Testing
        - One-Way ANOVA
        - Linear Algebra
        - Matplotlib Visualizations
        - Seaborn Heatmap
        - Plotly Interactive Dashboard
        """)

        st.subheader(
            "🎯 Recommendations"
        )

        st.markdown("""
        1. Increase availability of high-demand books.
        2. Monitor categories with high borrowing activity.
        3. Monitor books associated with repeated fines.
        4. Use monthly borrowing trends for inventory planning.
        5. Continue cleaning and validating new transaction data.
        """)


# ============================================================
# EXPORT
# ============================================================

elif (
    st.session_state.role == "owner"
    and choice == "📁 Export CSV"
):

    title(
        "📁 Export Library Data"
    )

    if books:

        export_data = books_to_dataframe(
            books
        )

        csv_data = export_data.to_csv(
            index=False
        ).encode("utf-8-sig")

        st.download_button(
            "⬇️ Download Books CSV",
            csv_data,
            "books.csv",
            "text/csv",
            use_container_width=True
        )

        st.dataframe(
            export_data,
            use_container_width=True,
            hide_index=True
        )

    else:

        st.info(
            "No books available for export."
        )