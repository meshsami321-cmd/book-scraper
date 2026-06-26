import pandas as pd
import smtplib
import os
import json
from email.mime.text import MIMEText

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

    # ---- Load subscriber list ----
    try:
        with open("subscribers.json", "r") as f:
            subscribers = json.load(f)
    except FileNotFoundError:
        print("\nsubscribers.json not found – skipping email.")
        exit()

    if not subscribers:
        print("\nSubscriber list is empty – skipping email.")
        exit()

    # ---- Build email alert ----
    app_password = os.environ.get("GMAIL_APP_PASSWORD")
    if app_password:
        sender = "meshsami321@gmail.com"
        sender_name = "Samuel - Price Drop Alerts"
        subject = "Price Drop Alert – Your Books Just Got Cheaper"

        body = f"Found {len(drops)} price drop(s):\n\n"
        for _, row in drops.iterrows():
            body += f"{row['Title']}: £{row['Price_yesterday']:.2f} -> £{row['Price_today']:.2f}\n"

        msg = MIMEText(body, "plain", "utf-8")
        msg["Subject"] = subject
        msg["From"] = f"{sender_name} <{sender}>"
        msg["To"] = sender
        msg["Bcc"] = ", ".join(subscribers)

        try:
            server = smtplib.SMTP("smtp.gmail.com", 587)
            server.starttls()
            server.login(sender, app_password)
            server.sendmail(sender, [sender] + subscribers, msg.as_string())
            server.quit()
            print(f"\nEmail alert sent to {len(subscribers)} subscriber(s).")
        except Exception as e:
            print(f"\nEmail failed: {e}")
    else:
        print("\n(GMAIL_APP_PASSWORD not set – skipping email)")