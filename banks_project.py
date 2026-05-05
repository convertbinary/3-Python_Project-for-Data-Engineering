# Code for ETL operations on Country-GDP data

# Importing the required libraries
from bs4 import BeautifulSoup
import requests
import pandas as pd
from datetime import datetime
import numpy as np
import sqlite3

url = 'https://web.archive.org/web/20230908091635/https://en.wikipedia.org/wiki/List_of_largest_banks'
df_columns = ['Rank', 'Bank Name', 'MC_USD_Billion']
exchange_rate_csv_path = 'exchange_rate.csv'
output_path = "df_transformed.csv"
sql_connection = sqlite3.connect('Banks.db')
table_name = 'Largest_banks'


def log_progress(message):
    ''' This function logs the mentioned message of a given stage of the
    code execution to a log file. Function returns nothing'''
    current_time = datetime.now()
    f_ct = current_time.strftime('%Y-%m-%d-%H:%M:%S')
    with open('log_file.txt', 'a') as log_file:
        log_file.write(f_ct + ':  ' + message + '\n')

def extract(url, table_attribs):
    ''' This function aims to extract the required
    information from the website and save it to a data frame. The
    function returns the data frame for further processing. '''
    data = requests.get(url).text
    soup = BeautifulSoup(data, 'html.parser')
    tables = soup.find_all('tbody')
    rows = tables[0].find_all('tr')
    df = pd.DataFrame(columns=table_attribs)
    for row in rows[1:]:
        col = row.find_all('td')
        if len(col) > 0:
            data_dict = {'Rank': col[0].text.strip(), 'Bank Name': col[1].text.strip(), 'MC_USD_Billion': col[2].text.strip()}
            df1 = pd.DataFrame(data_dict, index=[0])
            df = pd.concat([df, df1], ignore_index=True)
    return df

def transform(df, csv_path):
    ''' This function accesses the CSV file for exchange rate
	information, and adds three columns to the data frame, each
	containing the transformed version of Market Cap column to
	respective currencies'''
    exchange_rate_df = pd.read_csv(csv_path)
    exchange_dict = exchange_rate_df.set_index('Currency').to_dict()['Rate']
    # Ensure exchange_rate['GBP'] is always a float
    gbp_rate = float(exchange_dict['GBP'])
    eur_rate = float(exchange_dict['EUR'])
    inr_rate = float(exchange_dict['INR'])

    df['MC_GBP_Billion'] = [np.round(float(x) * gbp_rate, 2) for x in df['MC_USD_Billion']]
    df['MC_EUR_Billion'] = [np.round(float(x) * eur_rate, 2) for x in df['MC_USD_Billion']]
    df['MC_INR_Billion'] = [np.round(float(x) * inr_rate, 2) for x in df['MC_USD_Billion']]

    return df

def load_to_csv(df, output_path):
    ''' This function saves the final data frame as a CSV file in
	the provided path. Function returns nothing.'''
    with open(output_path, "w") as file:
        df.to_csv(file, index=False)

def load_to_db(df, sql_connection, table_name):
    ''' This function saves the final data frame to a database
	table with the provided name. Function returns nothing.'''
    df.to_sql(table_name, sql_connection, if_exists='replace', index=False)

def run_query(query_statement, sql_connection):
    ''' This function runs the query on the database table and
    prints the output on the terminal. Function returns nothing. '''
    result_df = pd.read_sql_query(query_statement, sql_connection)
    print(result_df)


''' Here, you define the required entities and call the relevant
functions in the correct order to complete the project. Note that this
portion is not inside any function.'''

log_progress('ETL process started.')

df = extract(url, df_columns)
print(df)
log_progress('Extract process completed.')


df_transformed = transform(df, exchange_rate_csv_path)
print(df_transformed)
log_progress('Transform process completed.')

load_to_csv(df_transformed, output_path)
log_progress('Load to CSV process completed.')

load_to_db(df_transformed, sql_connection, table_name)
log_progress('Load to DB process completed.')

run_query('SELECT * FROM Largest_banks;', sql_connection)
run_query('SELECT AVG(MC_GBP_Billion) FROM Largest_banks;', sql_connection)
run_query('SELECT `Bank Name` FROM Largest_banks LIMIT 5;', sql_connection)

log_progress('ETL process completed.')
