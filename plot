import pandas as pd
import numpy as np
import polars as pl
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px

# Load Dataset
df = pd.read_csv('library_transactions.csv')
print("Dataset Shape:", df.shape)
df.head()
print("--- Missing Values ---")
print(df.isnull().sum())
print("\n--- Duplicated Rows ---")
print("Duplicates count:", df.duplicated().sum())
print("\n--- Data Types ---")
print(df.dtypes)
# Drop duplicates
df_clean = df.drop_duplicates().copy()

# Fill missing categories and authors with 'Unknown'
df_clean['Category'].fillna('Uncategorized', inplace=True)
df_clean['Author'].fillna('Unknown Author', inplace=True)

# Convert date columns to datetime
df_clean['Borrow_Date'] = pd.to_datetime(df_clean['Borrow_Date'])
df_clean['Due_Date'] = pd.to_datetime(df_clean['Due_Date'])
df_clean['Return_Date'] = pd.to_datetime(df_clean['Return_Date'])

print("Cleaned Data Shape:", df_clean.shape)
Q1 = df_clean['Fine_Amount'].quantile(0.25)
Q3 = df_clean['Fine_Amount'].quantile(0.75)
IQR = Q3 - Q1
upper_bound = Q3 + 1.5 * IQR

outliers = df_clean[df_clean['Fine_Amount'] > upper_bound]
print(f"Upper Bound for Fines: ${upper_bound:.2f}")
print(f"Number of Fine Outliers: {len(outliers)}")
# Duration kept
df_clean['Borrow_Duration'] = (df_clean['Return_Date'] - df_clean['Borrow_Date']).dt.days
# Days delayed beyond due date
df_clean['Delay_Days'] = (df_clean['Return_Date'] - df_clean['Due_Date']).dt.days.apply(lambda x: max(0, x) if pd.notnull(x) else 0)
df_clean['Is_Overdue'] = df_clean['Delay_Days'] > 0
df_clean[['Borrow_Date', 'Due_Date', 'Return_Date', 'Borrow_Duration', 'Delay_Days', 'Fine_Amount']].head()
fines_array = df_clean['Fine_Amount'].values
high_fines_mask = fines_array > 10.0

print("Total Fines Collected (NumPy):", np.sum(fines_array))
print("Average Fine per Transaction:", np.mean(fines_array))
print("Max Fine Observed:", np.max(fines_array))
print("High Fine Count (> $10):", np.sum(high_fines_mask))
# GroupBy Member Type
member_stats = df_clean.groupby('Member_Type').agg(
    Total_Borrows=('Transaction_ID', 'count'),
    Total_Fines=('Fine_Amount', 'sum'),
    Avg_Delay=('Delay_Days', 'mean')
).reset_index()

print(member_stats)

# Pivot Table: Fines by Category and Member Type
pivot_fines = df_clean.pivot_table(index='Category', columns='Member_Type', values='Fine_Amount', aggfunc='sum', fill_value=0)
pivot_fines
pl_df = pl.from_pandas(df_clean)

polars_summary = pl_df.group_by('Category').agg([
    pl.count('Transaction_ID').alias('Borrow_Count'),
    pl.mean('Fine_Amount').alias('Avg_Fine')
]).sort('Borrow_Count', descending=True)

print(polars_summary)
category_counts = df_clean['Category'].value_counts()
print("Top Categories:")
print(category_counts)
stats_df = df_clean[['Borrow_Duration', 'Delay_Days', 'Fine_Amount']].describe()
print(stats_df)

print("\n--- Correlation Matrix ---")
print(df_clean[['Borrow_Duration', 'Delay_Days', 'Fine_Amount']].corr())
fig, axes = plt.subplots(1, 2, figsize=(14, 5))

# Chart 1: Most Borrowed Categories
sns.countplot(data=df_clean, y='Category', order=df_clean['Category'].value_counts().index, ax=axes[0], palette='crest')
axes[0].set_title('Most Popular Book Categories')

# Chart 2: Fine Amount Distribution
sns.boxplot(data=df_clean, x='Member_Type', y='Fine_Amount', ax=axes[1], palette='Set2')
axes[1].set_title('Fine Amount Distribution by Member Type')

plt.tight_layout()
plt.show()
fig = px.histogram(df_clean, x='Category', color='Member_Type', barmode='group',
                   title='Interactive Breakdown of Borrowings by Category & Member Type',
                   labels={'Category': 'Book Category', 'count': 'Number of Borrows'})
fig.show()