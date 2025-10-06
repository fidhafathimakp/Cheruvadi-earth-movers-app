import streamlit as st
import psycopg2
import pandas as pd
import plotly.express as px
from datetime import datetime

# ---- Database connection settings ----
DB_HOST = "db.pbollegtlkcxdbylblna.supabase.co"
DB_PORT = "5432"
DB_NAME = "postgres"
DB_USER = "postgres"
DB_PASS = "5kdWkrxe9QXZOVNw"

def get_conn():
    return psycopg2.connect(host=DB_HOST, port=DB_PORT, dbname=DB_NAME, user=DB_USER, password=DB_PASS)

def setup_db():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS entries (
            id SERIAL PRIMARY KEY,
            date DATE,
            vehicle TEXT,
            starting_reading FLOAT,
            closing_reading FLOAT,
            breaker FLOAT,
            bucket FLOAT,
            diesel FLOAT,
            advance FLOAT,
            shifting_rate FLOAT,
            batta FLOAT,
            salary FLOAT,
            remark TEXT
        );
    """)
    conn.commit()
    cur.close()
    conn.close()

setup_db()

def add_entry(data):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO entries (date, vehicle, starting_reading, closing_reading, breaker, bucket, diesel, advance, shifting_rate, batta, salary, remark)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
    """, (
        data['date'], data['vehicle'], data['starting_reading'], data['closing_reading'], data['breaker'],
        data['bucket'], data['diesel'], data['advance'], data['shifting_rate'], data['batta'], data['salary'], data['remark']
    ))
    conn.commit()
    cur.close()
    conn.close()

def fetch_data(vehicle=None, start_date=None, end_date=None):
    conn = get_conn()
    cur = conn.cursor()
    query = "SELECT * FROM entries WHERE 1=1"
    params = []
    if vehicle:
        query += " AND vehicle=%s"
        params.append(vehicle)
    if start_date:
        query += " AND date>=%s"
        params.append(start_date)
    if end_date:
        query += " AND date<=%s"
        params.append(end_date)
    cur.execute(query, tuple(params))
    rows = cur.fetchall()
    columns = [desc[0] for desc in cur.description]
    cur.close()
    conn.close()
    return pd.DataFrame(rows, columns=columns) if rows else pd.DataFrame(columns=columns)

def delete_entry(row_id):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("DELETE FROM entries WHERE id=%s;", (row_id,))
    conn.commit()
    cur.close()
    conn.close()

st.title("Cheruvadi Earth Movers: Vehicle Work & Wage Dashboard")

# ------ Daily Entry Form ------
st.header("Daily Vehicle Entry")
form = st.form(key='entry_form')
with form:
    date = st.date_input("Date", value=datetime.today())
    vehicle = st.selectbox("Vehicle", ["JCB 1", "JCB 2", "Excavator 210", "Excavator 140", "Volvo 80"])
    starting_reading = st.number_input("Starting Reading", step=0.1)
    closing_reading = st.number_input("Closing Reading", step=0.1)
    breaker = st.number_input("Breaker Hours", step=0.1)
    bucket = st.number_input("Bucket Hours", step=0.1)
    diesel = st.number_input("Diesel (L)", step=0.1)
    advance = st.number_input("Advance (₹)", step=0.1)
    shifting_rate = st.number_input("Shifting Rate (₹)", step=0.1)
    batta = st.number_input("Batta (₹)", step=0.1)
    salary = st.number_input("Wages / Salary (₹)", step=0.1)
    remark = st.text_input("Remarks / Driver Name")
    submitted = st.form_submit_button("Add Entry")
    if submitted:
        add_entry({
            'date': date,
            'vehicle': vehicle,
            'starting_reading': starting_reading,
            'closing_reading': closing_reading,
            'breaker': breaker,
            'bucket': bucket,
            'diesel': diesel,
            'advance': advance,
            'shifting_rate': shifting_rate,
            'batta': batta,
            'salary': salary,
            'remark': remark
        })
        st.success("Daily entry added!")

# ------ Filtering ------
st.header("Reports and Analytics")
vehicles = ["All"] + ["JCB 1", "JCB 2", "Excavator 210", "Excavator 140", "Volvo 80"]
selected_vehicle = st.selectbox("Filter by Vehicle", vehicles)
if selected_vehicle == "All":
    selected_vehicle = None
date_range = st.date_input("Date Range", value=(datetime(2025,1,1), datetime.today()))
df = fetch_data(
    vehicle=selected_vehicle,
    start_date=date_range[0],
    end_date=date_range[1]
)

# ------ Dashboard & Charts ------
if not df.empty:
    st.dataframe(df)
    st.metric("Total Breaker Hours", df['breaker'].sum())
    st.metric("Total Bucket Hours", df['bucket'].sum())
    st.metric("Total Diesel (L)", df['diesel'].sum())
    st.metric("Total Salary (₹)", df['salary'].sum())
    st.metric("Expenses (₹)", df['batta'].sum() + df['shifting_rate'].sum() + df['advance'].sum())
    st.metric("Total Records", len(df))
    chart = px.bar(df, x='vehicle', y='breaker', title="Breaker Hours by Vehicle")
    st.plotly_chart(chart)
    chart2 = px.bar(df, x='vehicle', y='bucket', title="Bucket Hours by Vehicle")
    st.plotly_chart(chart2)
else:
    st.warning("No data for selected filters.")

# ------ Edit/Delete ------
st.header("Manage Records")
if not df.empty:
    row_id = st.number_input("ID to delete", min_value=int(df['id'].min()), max_value=int(df['id'].max()), step=1)
    if st.button("Delete Record"):
        delete_entry(row_id)
        st.success(f"Row {row_id} deleted. Refresh page to update.")
else:
    st.info("No records to manage yet.")

# ------ CSV Export ------
st.header("CSV Export")
if not df.empty:
    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button("Download CSV for Accounting", data=csv, file_name="vehicle_records.csv")
else:
    st.info("No data for CSV export.")

st.header("Summary Statistics")
if not df.empty:
    st.write(df.groupby('vehicle')[["breaker","bucket","diesel", "salary"]].sum())
else:
    st.info("No statistics yet.")
