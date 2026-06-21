import pandas as pd
import smtplib
import os

# ---- Load today's and yesterday's data ----
try:
    df_new = pd.read_csv("books_catalog.csv")
    df_old = pd.read_csv("yesterday_catalog.csv")
except FileNotFoundError as e:
    print(f"Missing file: {e}")
    print("Make sure both books_catalog.csv and yesterday_catalog.csv exist.")
    exit()

# ---- Clean the price columns: remove £ and convert to float ----
df_new['Price'] = df_new['Price'].str.replace('£', '', regex=False).astype(float)
df_old['Price'] = df_old['Price'].str.replace('£', '', regex=False).astype(float)

# ---- Merge on Title to compare prices ----
merged = pd.merge(df_new, df_old, on='Title', suffixes=('_today', '_yesterday'))

# ---- Find books where price dropped ----
merged['price_drop'] = merged['Price_yesterday'] - merged['Price_today']
drops = merged[merged['price_drop'] > 0]

# ---- Report results ----
if drops.empty:
    print("No price drops detected.")
else:
    print(f"Found {len(drops)} price drop(s):")
    for _, row in drops.iterrows():
        print(f"  {row['Title']}: £{row['Price_yesterday']:.2f} -> £{row['Price_today']:.2f} (down £{row['price_drop']:.2f})")

    # ---- Build email alert (optional, works when GMAIL_APP_PASSWORD is set) ----
    app_password = os.environ.get("GMAIL_APP_PASSWORD")
    if app_password:
        sender = "meshsami321@gmail.com"
        receiver = "meshsami321@gmail.com"
        subject = "Price Drop Alert"
        body = f"Found {len(drops)} price drop(s):\n\n"
        for _, row in drops.iterrows():
            body += f"{row['Title']}: £{row['Price_yesterday']:.2f} -> £{row['Price_today']:.2f}\n"
        message = f"Subject: {subject}\n\n{body}"

        try:
            server = smtplib.SMTP("smtp.gmail.com", 587)
            server.starttls()
            server.login(sender, app_password)
            server.sendmail(sender, receiver, message)
            server.quit()
            print("\nEmail alert sent.")
        except Exception as e:
            print(f"\nEmail failed: {e}")
    else:
        print("\n(GMAIL_APP_PASSWORD not set – skipping email)")