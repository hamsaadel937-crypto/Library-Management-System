# 📚 Library Management System

A Python-based Library Management System designed to automate library operations and provide a simple, reliable, and user-friendly experience for managing books, users, borrowing transactions, data analysis, and visualizations.

The project combines **Python programming, Streamlit, data analysis, data cleaning, statistical analysis, and visualization** in one integrated application.

---

## 📌 Project Overview

The Library Management System is a modular Python application that helps manage library books and borrowing operations through an interactive Streamlit interface.

The system supports two main roles:

- 👨‍💼 **Library Owner**
- 👤 **Regular User**

The Owner has administrative access to manage the library inventory and analyze library data, while Regular Users can register, search for books, borrow available books, return books, and manage their own profiles.

The project also uses a real library transaction dataset (`library_transactions.csv`) for data cleaning, analysis, visualization, and generating the initial library book inventory.

---

# ✨ Main Features

## 👨‍💼 Library Owner

The Library Owner has administrative access to the system.

The Owner can:

- ➕ Add new books
- ✏️ Update book information
- ❌ Delete books
- 🔍 Search books
- 📚 View all books
- ✅ View available books
- 📋 View borrowing records
- 🔄 Synchronize books from the CSV dataset
- 📊 Analyze library transaction data
- 📈 Create data visualizations
- 📤 Export books to CSV
- 👤 Manage Owner profile
- 🔐 Change username and password
- 💾 Manage persistent library data

---

## 👤 Regular User

Regular users can create accounts and use the library services.

Users can:

- 📝 Register a new account
- 🔐 Login securely
- 👤 Manage their profile
- ✏️ Edit full name and username
- 🔑 Change their password
- 🔍 Search books by ID
- 🔍 Search books by title
- 🔍 Search books by author
- 📚 View available books
- 📥 Borrow books
- 📤 Return borrowed books
- 📋 View their own borrowing records

Users do not have permission to modify the library inventory.

---

# 🔐 Authentication & Profile Management

The system provides separate authentication for the Library Owner and Regular Users.

### Owner

The Owner can:

- Login using username and password
- Update full name
- Update username
- Change password
- Manage library inventory
- Access analysis and visualization features

### User

Regular users can:

- Create an account
- Login using username and password
- Update their personal information
- Change their password
- Manage their own borrowing activities

Passwords are not displayed as plain text in the application.

---

# 📚 Book Management

The system provides complete CRUD operations for library books.

### Create

The Owner can add a new book with:

- Book ID
- Title
- Author
- Category
- Number of available copies

### Read

The system allows users and the Owner to:

- View all books
- View available books
- Search by Book ID
- Search by Title
- Search by Author

### Update

The Owner can modify existing book information.

### Delete

The Owner can remove books from the library inventory while maintaining data consistency with active borrowing records.

---

# 🔄 CSV Dataset Integration

The project uses:

`library_transactions.csv`

as the main dataset for library transaction analysis.

The dataset contains information such as:

- Transaction ID
- Book ID
- Book Title
- Category
- Author
- Member ID
- Member Type
- Borrow Date
- Due Date
- Return Date
- Status
- Fine Amount

The application cleans and standardizes the dataset before performing analysis.

Unique books are extracted from the transaction dataset and can be synchronized with the library inventory.

This allows the CSV dataset to serve as the initial source of books available in the system.

---

# 🧹 Data Cleaning & Data Quality

The application performs several data cleaning operations, including:

- Standardizing column names
- Removing duplicate records
- Handling missing values
- Converting date columns to datetime format
- Cleaning text fields
- Handling invalid numeric values
- Detecting duplicate transaction IDs
- Handling missing categories and authors
- Validating transaction information
- Preparing clean data for analysis

A dedicated **Data Quality** section is included to help identify problems in the original dataset.

---

# 📊 Exploratory Data Analysis

The system provides Exploratory Data Analysis (EDA) for the library transaction dataset.

Analysis includes:

- Transaction distribution
- Book popularity
- Category distribution
- Member type distribution
- Borrowing trends
- Return status analysis
- Fine amount analysis
- Missing values
- Duplicate records
- Outlier detection

The application provides both numerical summaries and visual insights.

---

# 📈 Data Visualization

The system supports several visualization techniques.

### Available Visualizations

- 📊 Bar Charts
- 📉 Histograms
- 📦 Box Plots
- 🔵 Scatter Plots
- 📈 Line Charts
- 🔥 Correlation Heatmaps
- 📊 Category Distribution Charts
- 📚 Book and Transaction Analysis Charts

These visualizations help identify patterns and trends in library activity.

---

# 📐 Statistical Analysis

The project includes several statistical analysis techniques.

### Descriptive Statistics

- Mean
- Median
- Mode
- Range
- Variance
- Standard Deviation
- Quartiles
- Interquartile Range (IQR)

### Distribution Analysis

- Skewness
- Outlier Detection

### Probability & Sampling

- Probability calculations
- Expected Value
- Sampling
- Confidence Intervals

### Statistical Testing

- Hypothesis Testing
- One-Way ANOVA

### Linear Algebra

The project also demonstrates basic linear algebra operations using NumPy.

---

# 🔎 Search System

Users can search for books using:

### Book ID

Search for a specific book using its unique ID.

### Title

Search for books using part or all of the title.

### Author

Search for books written by a specific author.

The search results are displayed through the Streamlit interface.

---

# 📥 Borrowing System

When a user borrows a book:

1. The system checks whether the book exists.
2. The system checks available copies.
3. A borrowing record is created.
4. The available copies are decreased.
5. The transaction is saved to persistent storage.

Each borrowing record is associated with the user's account.

---

# 📤 Return System

Users can return books they previously borrowed.

When a book is returned:

1. The system verifies the borrowing record.
2. The borrowing record is removed/updated.
3. The available book count is increased.
4. The updated data is saved.

This keeps the library inventory synchronized with current borrowing activity.

---

# 💾 Data Persistence

The application uses local files for persistent storage.

### JSON Files

- `books.json`
- `borrowed_books.json`
- `users.json`
- `owner_profile.json`

### CSV Files

- `library_transactions.csv`
- `books.csv`

### Logging

The application also maintains:

- `library.log`

for recording important application events and errors.

---

# 🏗️ Project Structure

```text
Library-Management-System/
│
├── app.py
├── main.py
├── models.py
├── storage.py
├── library_service.py
│
├── library_transactions.csv
├── books.csv
├── books.json
├── borrowed_books.json
├── users.json
├── owner_profile.json
├── library.log
│
└── README.md
🧩 Main Python Modules
app.py

The main Streamlit application.

It handles:

User interface
Authentication
Owner dashboard
User dashboard
Book management
Borrowing and returning
Data analysis
Visualization
Statistical analysis
Profile management
CSV integration
models.py

Contains the main data models and custom exceptions.

Includes:

Book
User
BorrowRecord
Pydantic validation schemas
Custom library exceptions
storage.py

Responsible for persistent data storage.

It handles:

Loading data
Saving data
JSON storage
User storage
Owner profile storage
CSV export
Password hashing and verification
Logging
library_service.py

Contains the library business logic, including operations related to:

Books
Borrowing
Returning
Searching
Inventory management
main.py

Provides the main Python entry point for the project.

🛠️ Technologies Used
Programming Language
🐍 Python
Web Application
Streamlit
Data Analysis
Pandas
NumPy
Data Visualization
Matplotlib
Seaborn
Plotly
Statistics
SciPy
Data Validation
Pydantic
Data Storage
JSON
CSV
Python Concepts
Dataclasses
Functions
Object-Oriented Programming
Exception Handling
File Handling
Modular Programming
Authentication
Data Validation
🧠 Programming & Data Science Concepts

This project demonstrates several programming and Data Science concepts:

Object-Oriented Programming
Dataclasses
Pydantic Models
Exception Handling
File Handling
JSON Persistence
CSV Processing
Data Cleaning
Data Wrangling
Exploratory Data Analysis
Statistical Analysis
Data Visualization
NumPy Arrays
Pandas DataFrames
Probability
Sampling
Hypothesis Testing
ANOVA
Linear Algebra
CRUD Operations
Authentication
Role-Based Access
Password Hashing
Logging
🚀 Installation
1. Clone the Repository
git clone https://github.com/hamsaadel937-crypto/Library-Management-System.git

Move into the project directory:

cd Library-Management-System
2. Install Required Libraries

Install the required Python packages:

pip install streamlit pandas numpy matplotlib seaborn plotly scipy pydantic
▶️ Run the Application

Start the Streamlit application using:

streamlit run app.py

The application will open in your browser.

🔑 User Flow
Owner Flow
Owner Login
     ↓
Owner Dashboard
     ↓
Manage Books
     ↓
Add / Update / Delete / Search
     ↓
Data Analysis
     ↓
Visualization
     ↓
Statistical Analysis
     ↓
Export Data
User Flow
Register
   ↓
Login
   ↓
User Dashboard
   ↓
Search / View Books
   ↓
Borrow Book
   ↓
View Borrowed Books
   ↓
Return Book
📊 Data Analysis Workflow

The data analysis pipeline follows these steps:

Raw CSV Dataset
       ↓
Column Standardization
       ↓
Data Cleaning
       ↓
Missing Value Handling
       ↓
Duplicate Detection
       ↓
Data Validation
       ↓
Feature Engineering
       ↓
Exploratory Data Analysis
       ↓
Statistical Analysis
       ↓
Visualization
       ↓
Insights & Reports
🔄 Library Inventory Workflow

The library inventory can be initialized from the transaction dataset.

library_transactions.csv
          ↓
     Read Dataset
          ↓
   Clean & Standardize
          ↓
 Extract Unique Books
          ↓
   Create Book Records
          ↓
      books.json
          ↓
 Library Management System

This makes the transaction dataset useful not only for analysis but also for creating the initial library book inventory.

🛡️ Error Handling

The application includes custom exceptions for common library operations, such as:

BookNotFoundError
DuplicateBookError
InsufficientCopiesError
UnauthorizedError
UserNotFoundError
DuplicateUserError
BorrowRecordNotFoundError

These exceptions help the application handle invalid operations safely.

📌 Project Highlights

Some of the main strengths of this project are:

Modular Python architecture
Interactive Streamlit interface
Role-based access
CRUD book management
User registration and authentication
Borrowing and returning system
CSV dataset integration
Data cleaning and quality analysis
Exploratory Data Analysis
Statistical analysis
Data visualization
Persistent JSON storage
CSV export
Logging
Password protection and hashing
Exception handling
👩‍💻 Team
Hamsa Adel
Radwa Mohamed
Baraah Abdelmoneam
👨‍🏫 Instructor

Ahmed Heary

🏛️ Organization

Arabian Academy

🎓 Project Purpose

This project was developed as a Python Final Project and combines software development with Data Science concepts.

It demonstrates how Python can be used to build an interactive management system while also applying:

Data Wrangling
Exploratory Data Analysis
Statistics
Visualization
Data Validation
File Management
Object-Oriented Programming
