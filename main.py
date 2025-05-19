import pandas as pd
import csv
from datetime import datetime, timedelta
import os
import matplotlib.pyplot as plt
import numpy as np
import random 
import requests
from dotenv import load_dotenv
import json


load_dotenv(dotenv_path='touch.env')
token = os.getenv("WISE_API_TOKEN")
headers = {"Authorization": f"Bearer {token}"}

# Get profile ID
response = requests.get("https://api.transferwise.com/v1/profiles", headers=headers)
try:
    profiles = response.json()
except json.JSONDecodeError:
    with open("wise_debug.log", "a") as log:
        log.write("Error decoding profiles response: " + response.text + "\n")
    print("❌ Failed to decode profiles response. Check wise_debug.log.")
    profiles = []

profile_id = next((p['id'] for p in profiles if p['type'] == 'personal'), None)

# Get borderless accounts
borderless_accounts = []
if profile_id:
    response = requests.get(f"https://api.transferwise.com/v1/borderless-accounts?profileId={profile_id}", headers=headers)
    try:
        borderless_accounts = response.json()
    except json.JSONDecodeError:
        with open("wise_debug.log", "a") as log:
            log.write("Error decoding borderless accounts response: " + response.text + "\n")
        print("❌ Failed to decode borderless accounts response. Check wise_debug.log.")

filename = 'transactions.csv'
if not os.path.exists(filename):
    df = pd.DataFrame(columns=["Date", "Type", "Amount", "Category"])
    df.to_csv(filename, index=False)

# === Extracting and saving transaction data from Wise ===
if isinstance(borderless_accounts, list) and borderless_accounts:
    account_id = borderless_accounts[0]['id']
    params = {
        "type": "ALL",
        "from": "2020-01-01T00:00:00Z",
        "to": "2025-12-31T23:59:59Z"
    }
    response = requests.get(
        f"https://api.transferwise.com/v1/borderless-accounts/{account_id}/transactions",
        headers=headers,
        params=params
    )
    try:
        transactions = response.json()
    except json.JSONDecodeError:
        with open("wise_debug.log", "a") as log:
            log.write("Error decoding transactions response: " + response.text + "\n")
        print("❌ Failed to decode transactions response. Check wise_debug.log.")
        transactions = []

    if isinstance(transactions, list):
        with open(filename, mode='a', newline='') as file:
            writer = csv.writer(file)
            for tx in transactions:
                if not isinstance(tx, dict):
                    continue
                date = tx.get('date', '')[:10]
                amount = tx.get('amount', {}).get('value', 0)
                tx_type = 'income' if amount > 0 else 'expense'
                description = tx.get('details', {}).get('description', '') or 'unknown'
                writer.writerow([date, tx_type, abs(amount), description])
        print('✅ Wise transactions have been saved to CSV.')
    else:
        with open("wise_debug.log", "a") as log:
            log.write("Unexpected transactions response format: " + str(transactions) + "\n")
        print("⚠️ Transactions response is not a list. Check wise_debug.log.")
else:
    print("⚠️ No borderless accounts found.")





def generate_random_data(rows = 100):
    CategoriesIncome = ['salary', 'freelance', 'scholarhsip', 'business', 'gift', 'rental income', 'stock divident']
    CategoriesExpense = ['grocery', 'charity', 'education', 'entertainment', 'rent', 'utilities', 'health care', 'taxes', 'transportation', 'self care']
    start_date = datetime(2020, 1, 1)
    end_date = datetime(2025, 12, 31)
    with open(filename, mode='a', newline='') as file:
        writer = csv.writer(file)
        for i in range(rows):
            delta = end_date - start_date
            random_days = random.randint(0, delta.days)
            date = (start_date + timedelta(days=random_days)).strftime('%Y-%m-%d')

            type_ = random.choice(['income', 'expense'])
            amount = round(random.uniform(1, 1000000), 2)

            if type_ == 'income':
                category = random.choice(CategoriesIncome)
            elif type_ == 'expense':
                category = random.choice(CategoriesExpense)

            writer.writerow([date, type_, amount, category])
        print('transactions are added!')
    


def add_transactions():
    saving_jar = 0
    add = input('Do you need to add transactions? ')
    if add.lower() == 'yes':
        date = datetime.now().strftime('%Y-%m-%d')
        t_type = input("Income or Expense? ").lower()
        if t_type not in ('income', 'expense'):
            raise ValueError("'type' has to be either 'income' or 'expense'")
        if t_type == 'income':
            amount = float(input('What is your income?'))
            category = input('What is the source? ')
            if category == 'salary':
                amount_for_saving = amount*0.25
                saving_jar = saving_jar + amount_for_saving
                amount = amount - amount_for_saving
        elif t_type == 'expense':
            amount = float(input('What is your expense? ')) 
            category = input('What is the category? ')
        if amount <= 0:
            raise ValueError("'amount' has to be a positive number")
        comment = input('Add notes (optional)')
        with open(filename, mode='a', newline='') as file:
            writer = csv.writer(file)
            writer.writerow([date, t_type, amount, category])
            print('transactions are added!')
    elif add.lower() == 'no':
        print('sure!')
    else:
        print('non-valid answer')
    return saving_jar


def load_data():
    try:
        df = pd.read_csv(filename)
        df['Date'] = pd.to_datetime(df['Date'])
        return df
    except FileNotFoundError:
        print(f"Error: {filename} not found. Please generate data first (Option 1).")
        return pd.DataFrame(columns=["Date", "Type", "Amount", "Category"])
    except Exception as e:
        print(f"Error loading data: {e}")
        return pd.DataFrame(columns=["Date", "Type", "Amount", "Category"])


def show_category_report(df):
    if df.empty:
        print("No data available to generate report.")
        return
    
    category_report = df.groupby(['Type', 'Category'])['Amount'].sum()
    print("\nReport by Category:")
    print(category_report)

    if not category_report.empty:

        income_data = category_report['income'] if 'income' in category_report.index.levels[0] else pd.Series()
        expense_data = category_report['expense'] if 'expense' in category_report.index.levels[0] else pd.Series()

        if not income_data.empty or not expense_data.empty:
            fig, axes = plt.subplots(1, 2, figsize=(14, 7))

            if not income_data.empty:
                axes[0].pie(income_data, labels=income_data.index, autopct='%1.1f%%', startangle=140)
                axes[0].set_title('Income Categories')

            if not expense_data.empty:
                axes[1].pie(expense_data, labels=expense_data.index, autopct='%1.1f%%', startangle=140)
                axes[1].set_title('Expense Categories')

            plt.tight_layout()
            plt.show()
        else:
            print("No data to plot.")


def show_top_expenses(df):
    if df.empty:
        print("No data available to show top expenses.")
        return
    expenses_df = df[df['Type'] == 'expense']
    top_expenses = expenses_df.sort_values(by='Amount', ascending=False).head(5)
    print("\nTop Expenses:")
    print(top_expenses[['Date', 'Category', 'Amount']])


def show_recent_data(df):
    today = pd.to_datetime(datetime.now().date())
    last_week_data = today - pd.Timedelta(days=7)
    last_month_data = today - pd.Timedelta(days=30)
    df_last_week = df[df['Date'] >= last_week_data]
    df_last_month = df[df['Date'] >= last_month_data]
    week_income = df_last_week[df_last_week['Type'] == 'income']['Amount'].to_numpy()
    week_expense = df_last_week[df_last_week['Type'] == 'expense']['Amount'].to_numpy()
    month_income = df_last_month[df_last_month['Type'] == 'income']['Amount'].to_numpy()
    month_expense = df_last_month[df_last_month['Type'] == 'expense']['Amount'].to_numpy()
    print(f"Last 7 days:\n   Income: {round(np.sum(week_income), 2)} | Expense: {round(np.sum(week_expense), 2)}")
    print(f"Last 30 days:\n   Income: {round(np.sum(month_income), 2)} | Expense: {round(np.sum(month_expense), 2)}")


def show_means(df):
    if df.empty:
        print("No data available to calculate means.")
        return
    mean_value_income = df[df['Type'] == 'income']['Amount'].mean() 
    print(f'your average income: {round(mean_value_income, 2)}')
    mean_value_expense = df[df['Type'] == 'expense']['Amount'].mean()
    print(f'your average expense: {round(mean_value_expense, 2)}')


def check_expense_limit(df, limit=1000000):
    current_month = datetime.now().month
    current_month_expenses_sum = df[
        (df['Type'] == 'expense') & (df['Date'].dt.month == current_month)]['Amount'].to_numpy()
    if np.sum(current_month_expenses_sum) >= limit:
        print('Warning: Your spending for this month is too high!')


def net_worth_of_year(df):
    current_year = datetime.now().year
    year_income = df[(df['Date'].dt.year == current_year) and (df['Type'] == 'income')]['Amount'].to_numpy()
    year_expense = df[(df['Date'].dt.year == current_year) and (df['Type'] == 'expense')]['Amount'].to_numpy()
    for i in range(0, 12):
        df[(df['Date'].dt.month == i) and (df['Type'] == 'income')]['Amount'].to_numpy()



print(f"https://api.transferwise.com/v1/borderless-accounts/{account_id}/transactions")


#generate_random_data(rows = 100)
df = load_data()
show_category_report(df)
show_top_expenses(df)
show_recent_data(df)
show_means(df)
check_expense_limit(df, limit=10000)
saving_jar = add_transactions()
print(f'your savings are: {saving_jar}')