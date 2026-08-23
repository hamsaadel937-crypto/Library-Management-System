# 📚 Library Management System

A Python-based Library Management System designed to simplify book organization, borrowing, returning, searching, and data management through an efficient, reliable, and user-friendly interface.

The system provides separate roles for the **Library Owner** and **Regular Users**, with different permissions and features for each role.

---

## 📖 Project Overview

The Library Management System is a Python application developed to automate common library operations and improve book management.

The system is divided into two main roles:

- 👨‍💼 **Library Owner**
- 👤 **Regular User**

The Library Owner is responsible for managing books and accessing administrative features, while regular users can search for books, borrow available books, return borrowed books, and view their borrowing records.

The project follows a modular programming approach by separating the application into multiple Python files, making the code organized, reusable, and easy to maintain.

---

## 👨‍💼 Owner System

The Library Owner has administrative access to the library system.

The Owner can:

- ➕ Add New Books
- ✏️ Update Book Information
- ❌ Remove Books
- 🔍 Search Books
- 📚 Display All Books
- ✅ Display Available Books
- 📋 View All Borrowed Books
- 📊 Perform Statistical Analysis
- 📈 View Data Visualizations
- 📄 Export Books to CSV
- 💾 Manage Library Data

---

## 👤 User System

Regular users can create their own accounts and use the library services.

Users can:

- 📝 Create a New Account
- 🔐 Login with Username and Password
- 👤 Use their Full Name
- 🔍 Search Books by ID
- 🔍 Search Books by Title
- 🔍 Search Books by Author
- 📚 Display Available Books
- 📥 Borrow Books
- 📤 Return Books
- 📋 View Their Borrowed Books

Each user has their own account and borrowing records.

---

## 🔐 Authentication & Permissions

The system provides authentication for both the Library Owner and Regular Users.

### 👨‍💼 Owner

The Owner has full administrative permissions, including:

- Book Management
- Inventory Management
- Borrowing Records
- Statistical Analysis
- Data Visualization
- CSV Export

### 👤 User

Regular users have access to:

- Book Search
- Available Books
- Borrowing
- Returning
- Their Own Borrowing Records

This role-based structure prevents regular users from modifying the library inventory.

---

## ✨ Features

### 📚 Book Management

- ➕ Add New Books
- ❌ Remove Books
- 🔍 Search Books by ID
- 🔍 Search Books by Title
- 🔍 Search Books by Author
- 📚 Display All Books
- ✅ Display Available Books

### 📥 Borrowing System

- 📥 Borrow Books
- 📤 Return Books
- 📋 Track Borrowing Records
- 👤 Associate Borrowing Records with Users

### 🔐 User Management

- 📝 User Registration
- 🔑 User Login
- 👤 Full Name
- 🔐 Username & Password
- 👨‍💼 Owner/User Role Separation

### 📊 Statistical Analysis

The system provides mathematical and statistical analysis of library data, including:

- Mean
- Median
- Mode
- Range
- Variance
- Standard Deviation
- Quartiles
- IQR
- Outlier Detection
- Skewness
- Probability
- Expected Value
- Sampling
- Confidence Interval
- Hypothesis Testing
- One-Way ANOVA
- Linear Algebra

### 📈 Data Visualization

The system supports multiple charts:

- 📊 Bar Chart
- 📉 Histogram
- 📦 Box Plot
- 🔵 Scatter Plot
- 📈 Line Chart

### 💾 Data Management

- JSON Data Storage
- CSV Export
- Automatic Data Saving
- Logging System
- Exception Handling

---

## 🛠️ Technologies Used

- Python
- Streamlit
- Pandas
- NumPy
- SciPy
- Matplotlib
- Pydantic
- Dataclasses
- JSON
- CSV
- Logging

---

## 🧠 Programming Concepts

This project demonstrates several Python and Data Science concepts:

- Object-Oriented Programming
- Dataclasses
- Pydantic Data Validation
- Exception Handling
- File Handling
- JSON Data Storage
- CSV Export
- Logging
- Modular Programming
- Functions
- `map()`
- `filter()`
- `reduce()`
- `zip()`
- NumPy Arrays
- Statistical Analysis
- Data Visualization
- Linear Algebra
- Probability
- Sampling
- Hypothesis Testing
- ANOVA

---

## 📂 Project Structure

```text
Library-Management-System/
│
├── app.py
├── main.py
├── models.py
├── storage.py
├── library_service.py
│
├── books.json
├── borrowed_books.json
├── users.json
├── books.csv
├── library.log
│
└── README.md
---

## 👩‍💻 Created By

- Hamsa Adel
- Radwa Mohamed
- Baraah Abdelmoneam

---

## 👨‍🏫 Instructor

Ahmed Heary

---

## 🏛️ Organization

Arabian Academy

---

## 📄 License

This project was developed for educational purposes as part of a Python Final Project.
