# -*- coding: utf-8 -*-
"""
Created on Fri Feb 27 11:19:47 2026

@author: aengstrom
"""
import pyodbc
import pandas as pd
def query_av_rtemp(start_date: pd.Timestamp, end_date: pd.Timestamp, site: str) -> pd.Series:
    # Validate inputs
    if not all(isinstance(d, pd.Timestamp) for d in [start_date, end_date]):
        raise TypeError("start_date and end_date must be pandas Timestamps")
    if start_date >= end_date:
        raise ValueError("start_date must be earlier than end_date")

    #Convert datetime to explicitly match SQL DATETIME
    start_date_str = start_date.strftime('%Y-%m-%d %H:%M:%S')
    end_date_str = end_date.strftime('%Y-%m-%d %H:%M:%S')
    
    sql_drivers = [d for d in pyodbc.drivers() if "SQL Server" in d]
    if not sql_drivers:
        raise RuntimeError("No SQL Server ODBC driver found on this machine.")
    driver = sql_drivers[0]


    query=f"""SELECT 
        Date,
        FinalValue as Temperature
        FROM AVData.Reporting.ReadingAverageDataFull
        
        
        
        
        WHERE SiteAbbreviation = '{site}'
        AND Date >= '{start_date_str}'
        AND Date <= '{end_date_str}'
        AND [IntervalName] =  '001m'

        AND ParameterName = 'RTEMP'
        AND ParameterEnabled = 1
        ORDER BY Date"""
        
    with pyodbc.connect(
        f'DRIVER={{{driver}}};'
        'SERVER=168.178.3.149;'
        'DATABASE=AVData;'
        'timeout=10;ENCRYPT=yes;Trusted_Connection=yes;TrustServerCertificate=yes;'
    ) as cnxn:
        df = pd.read_sql_query(query, cnxn).set_index('Date')
        
    
    return df['Temperature'] 
