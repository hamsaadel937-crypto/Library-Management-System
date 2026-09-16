# 📚 Library Management System

A complete Python-based Library Management System developed with Streamlit and extended into a full **Data Wrangling, EDA, Statistics, Visualization, and Interactive Dashboard project**.

The project progressed through:

```text
Module 1 → Build the Library Management System
Module 2 → Mathematics & Statistics
Module 3 → Data Wrangling, EDA & Visualization
🎯 Project Goal

The project transforms raw library transaction data into:

Raw Data
   ↓
Data Quality Assessment
   ↓
Data Cleaning
   ↓
Outlier Detection
   ↓
Feature Engineering
   ↓
NumPy Analysis
   ↓
Pandas Data Wrangling
   ↓
Polars Analysis
   ↓
EDA
   ↓
Statistical Exploration
   ↓
Visualization
   ↓
Interactive Plotly Dashboard
   ↓
Insights
   ↓
Recommendations
   ↓
Final Conclusion
📊 Dataset

The main dataset is:

library_transactions.csv

The dataset contains library transaction information including:

Transaction ID
Book ID
Book Title
Category
Author
Member ID
Member Type
Borrow Date
Due Date
Return Date
Status
Fine Amount

The dataset represents borrowing transactions, not one row per book.

Therefore:

Transactions ≠ Books

The library inventory is created using the unique Book_ID values from the dataset.

🧹 Module 3 - Data Quality Assessment

The project checks the raw dataset for:

Missing Values
Duplicate Rows
Duplicate Transaction IDs
Incorrect Data Types
Invalid Values
Inconsistent Categories
Invalid Dates
Numerical Problems
Potential Outliers

A dedicated Data Quality page displays the detected problems before cleaning.

🧽 Data Cleaning

The cleaning pipeline includes:

Removing exact duplicate rows
Standardizing column names
Removing unnecessary spaces
Standardizing text values
Handling missing categorical values
Converting dates to datetime
Converting Fine Amount to numeric
Handling invalid negative fines
Standardizing transaction status
Preparing the dataset for analysis

Missing categorical information is represented as:

Unknown

instead of inventing values.

📦 Outlier Detection

The project uses the IQR method.

IQR = Q3 - Q1

Lower Bound = Q1 - 1.5 × IQR

Upper Bound = Q3 + 1.5 × IQR

Potential outliers are identified and visualized using Box Plots.

The project does not randomly remove outliers.

🔧 Feature Engineering

New analytical features are created from the original data:

Borrow Year
Borrow Month
Borrow Month Name
Borrow Day
Borrow Day Name
Borrow Duration
Due Duration
Fine Group

These features make time-based and behavioral analysis easier.

🔢 NumPy Analysis

NumPy is used for:

NumPy Arrays
Indexing
Slicing
Boolean Masking
Vectorization
Mean
Median
Standard Deviation
Variance
Percentiles
Matrix Operations
Linear Algebra
🐼 Pandas Data Wrangling

The project demonstrates:

Filtering
Sorting
GroupBy
Aggregation
Merge
Join
Pivot Tables
Reshaping

Example:

df.groupby("Category")["Fine_Amount"].mean()

The results are interpreted instead of simply displayed.

⚡ Polars Analysis

Polars is used for selected data-wrangling operations:

Polars DataFrames
Selecting columns
Filtering
Grouping
Aggregation
Lazy API

The project also provides a comparison between:

Pandas
vs
Polars
🔎 Exploratory Data Analysis

EDA is divided into three levels.

Univariate Analysis

Analysis of one variable, such as:

Fine Amount
Transaction Status
Category
Member Type
Bivariate Analysis

Relationships between two variables, such as:

Borrow Duration vs Fine Amount
Category vs Fine Amount
Multivariate Analysis

Analysis involving multiple variables, such as:

Category
Member Type
Fine Amount
📐 Statistical Analysis

The project includes:

Mean
Median
Mode
Range
Variance
Standard Deviation
Quartiles
IQR
Skewness
Correlation
Probability
Expected Value
Sampling
Confidence Intervals
Hypothesis Testing
One-Way ANOVA
Linear Algebra

Statistical results are interpreted in the application.

📊 Data Visualization

The project includes:

Bar Chart

Used to compare transaction activity between categories.

Histogram

Used to understand the distribution of Fine Amount.

Line Chart

Used to analyze monthly borrowing trends.

Box Plot

Used to understand numerical distributions and detect potential outliers.

Scatter Plot

Used to investigate relationships between Borrow Duration and Fine Amount.

Correlation Heatmap

Used to visualize relationships between numerical variables.

📈 Interactive Plotly Dashboard

The project includes an interactive dashboard containing:

Total Transactions
Unique Books
Unique Members
Total Fines
Monthly Borrowing Trends
Transactions by Category
Member Type Distribution
Average Fine by Category

The dashboard supports interactive filters and Plotly interactions.

💡 Data Storytelling

The analysis follows:

Data
 ↓
Finding
 ↓
Insight
 ↓
Recommendation

The project identifies:

High-demand categories
Frequently borrowed books
Active member types
Fine patterns
Monthly borrowing patterns
Data quality problems
Potential outliers

Based on these findings, recommendations are generated for library inventory and management.

👨‍💼 Owner Features

The Library Owner can:

Add Books
Update Books
Remove Books
Search Books
View All Books
View Borrowing Records
Synchronize Books from CSV
Export Books
Access Data Quality
Access Data Cleaning
Access EDA
Access Statistics
Access Visualizations
Access Interactive Dashboard
View Insights
View Final Conclusion
Edit Owner Profile

Owner Profile allows updating:

Full Name
Username
Password
👤 User Features

Regular Users can:

Register
Login
Search Books
View Available Books
Borrow Books
Return Books
View Borrowed Books
Edit their profile

User Profile allows updating:

Full Name
Username
Password

Passwords are entered through password-protected fields and stored using hashing.

📚 Library Inventory

The library inventory is generated from unique books in:

library_transactions.csv

The system uses:

Book_ID
Book_Title
Author
Category

to create unique library books.

For example:

500 Transactions
       ↓
Unique Book IDs
       ↓
Library Inventory

Repeated transactions for the same Book ID do not create duplicate books.

📥 Borrowing System

When a user borrows a book:

The system checks that the book exists.
The system checks available copies.
A borrowing record is created.
Available copies decrease.
Data is saved.
📤 Returning System

When a user returns a book:

The system identifies the active borrowing record.
The borrowing record is removed.
Available copies increase.
Updated data is saved.
🔐 Authentication

The project provides role-based authentication:

Owner
  ↓
Administrative Features

User
  ↓
Library Services

Passwords are not displayed as plain text.

Passwords are stored using SHA-256 hashing.

💾 Data Persistence

The project uses JSON files for persistent application data:

books.json
borrowed_books.json
users.json
owner_profile.json

Additional files include:

library_transactions.csv
books.csv
library.log
🧩 Project Structure
Library-Management-System/
│
├── app.py
├── main.py
├── models.py
├── storage.py
├── library_service.py
│
├── library_transactions.csv
├── books.json
├── borrowed_books.json
├── users.json
├── owner_profile.json
├── books.csv
├── library.log
├── requirements.txt
└── README.md
🛠️ Technologies Used
Python
Streamlit
Pandas
NumPy
Polars
Matplotlib
Seaborn
Plotly
SciPy
Pydantic
JSON
CSV
Logging
🧠 Main Concepts

The project demonstrates:

Object-Oriented Programming
Modular Programming
Dataclasses
Pydantic Validation
Exception Handling
File Handling
Authentication
Role-Based Access
Password Hashing
CRUD Operations
Data Cleaning
Data Wrangling
Outlier Detection
Feature Engineering
NumPy
Pandas
Polars
EDA
Statistics
Probability
Sampling
Hypothesis Testing
ANOVA
Visualization
Interactive Dashboards
Data Storytelling
🚀 Installation

Clone the repository:

git clone https://github.com/hamsaadel937-crypto/Library-Management-System.git

Open the project:

cd Library-Management-System

Install requirements:

pip install -r requirements.txt

Run:

streamlit run app.py
🔑 Default Owner Account
Username: library
Password: lib123456

The password is not displayed inside the application interface.

🎯 Final Project Pipeline
Existing Library Management System
            ↓
       Data Collection
            ↓
   Data Quality Assessment
            ↓
       Data Cleaning
            ↓
    Outlier Detection
            ↓
    Feature Engineering
            ↓
       NumPy Analysis
            ↓
    Pandas Wrangling
            ↓
      Polars Analysis
            ↓
            EDA
       ↙      ↓      ↘
Univariate  Bivariate  Multivariate
            ↓
 Statistical Exploration
            ↓
      Visualization
            ↓
 Interactive Plotly Dashboard
            ↓
      Data Storytelling
            ↓
   Insights & Recommendations
            ↓
       Final Conclusion
👩‍💻 Team
Hamsa Adel
Radwa Mohamed
Baraah Abdelmoneam
👨‍🏫 Instructor

Ahmed Heary

🏛️ Organization

Arabian Academy

📄 Purpose

This project was developed as an educational final project demonstrating the progression from a traditional Python Library Management System into a complete real-world Data Analysis project.
