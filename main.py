
from datetime import datetime, timedelta
import email.mime.multipart
import email.mime.text
import smtplib
import requests

import os

# Configuration loaded from environment variables
WEB_APP_URL = os.getenv("WEB_APP_URL", "https://script.google.com/macros/s/YOUR_DEPLOYMENT_ID/exec")
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SENDER_EMAIL = os.getenv("SENDER_EMAIL", "your_email@gmail.com")
SENDER_PASSWORD = os.getenv("SENDER_PASSWORD", "your_app_password")


def send_email(to_email, subject, body):
  try:
    msg = email.mime.multipart.MIMEMultipart()
    msg["From"] = SENDER_EMAIL
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.attach(email.mime.text.MIMEText(body, "plain"))

    server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
    server.starttls()
    server.login(SENDER_EMAIL, SENDER_PASSWORD)
    server.sendmail(SENDER_EMAIL, to_email, msg.as_string())
    server.quit()
    print(f"✅ Email alert sent to {to_email}")
  except Exception as e:
    print(f"❌ Email error: {e}")


def run_automation():
  print("Fetching data from Google Sheet...")
  res = requests.post(WEB_APP_URL, json={"action": "getTasks"}).json()

  tracking_data = res["tracking"]
  master_data = res["master"]

  print(
      f"📊 Fetched {len(tracking_data)-1} tracking rows and"
      f" {len(master_data)-1} master rows."
  )

  # Convert master sheet rows to dictionary
  master_lookup = {}
  for row in master_data[1:]:
    if row and row[0]:
      master_lookup[row[0]] = {
          "name": row[1] if len(row) > 1 else "",
          "frequency": int(row[3]) if len(row) > 3 and row[3] else 1,
          "manager": row[5] if len(row) > 5 else "",
          "leadership": row[6] if len(row) > 6 else "",
      }

  today = datetime.now().date()
  print(f"📅 Current Date (Today): {today}")

  # Check each row in Task_Tracking
  for idx, row in enumerate(tracking_data[1:], start=2):
    if not row or len(row) < 5 or not row[0]:
      continue

    log_id, task_id, assigned_email, due_date_val, status = (
        row[0],
        row[1],
        row[2],
        str(row[3])[:10],
        row[4],
    )
    manager_alert = str(row[6]).upper() == "TRUE" if len(row) > 6 else False
    leadership_esc = str(row[7]).upper() == "TRUE" if len(row) > 7 else False
    next_cycle_created = str(row[8]).upper() == "TRUE" if len(row) > 8 else False

    print(
        f"🔍 Checking Row {idx}: Task={task_id}, Due={due_date_val},"
        f" Status={status}"
    )

    try:
      due_date = datetime.strptime(due_date_val, "%Y-%m-%d").date()
    except ValueError:
      print(f"⚠️ Could not parse date: {due_date_val}")
      continue

    info = master_lookup.get(task_id, {})
    task_name = info.get("name", task_id)
    frequency = info.get("frequency", 1)
    manager_email = info.get("manager", "")
    leadership_email = info.get("leadership", "")

    # 1. Recurring Cycle Rollover
    if status == "Completed" and not next_cycle_created:
      next_due = due_date + timedelta(days=frequency)
      new_log_id = f"{task_id}_{next_due.strftime('%Y%m%d')}"
      new_row = [
          new_log_id,
          task_id,
          assigned_email,
          next_due.strftime("%Y-%m-%d"),
          "Pending",
          "",
          False,
          False,
          False,
      ]

      requests.post(
          WEB_APP_URL, json={"action": "appendRow", "rowValues": new_row}
      )
      requests.post(
          WEB_APP_URL,
          json={
              "action": "updateRow",
              "rowIndex": idx,
              "colIndex": 9,
              "value": "TRUE",
          },
      )
      print(f"🔄 Rollover created for {task_id} due on {next_due}")

    # 2. Overdue Manager Alert
    elif status == "Pending" and today > due_date:
      print(
          f"🚨 Task {task_id} is overdue! Due: {due_date}, Today: {today},"
          f" Alert Sent: {manager_alert}"
      )
      if not manager_alert and manager_email:
        subject = f"[Overdue Task] {task_name}"
        body = (
            f"Hello Manager,\n\nTask '{task_name}' assigned to"
            f" {assigned_email} was due on {due_date_val} and is still"
            " Pending."
        )
        send_email(manager_email, subject, body)
        requests.post(
            WEB_APP_URL,
            json={
                "action": "updateRow",
                "rowIndex": idx,
                "colIndex": 7,
                "value": "TRUE",
            },
        )

      # 3. Leadership Escalation
      if (today - due_date).days >= 2 and not leadership_esc:
        if leadership_email:
          subject = f"[ESCALATION] Unresolved Task: {task_name}"
          body = (
              f"Dear Leadership,\n\nTask '{task_name}' assigned to"
              f" {assigned_email} has been pending for over 2 days past due date"
              f" ({due_date_val})."
          )
          send_email(leadership_email, subject, body)
          requests.post(
              WEB_APP_URL,
              json={
                  "action": "updateRow",
                  "rowIndex": idx,
                  "colIndex": 8,
                  "value": "TRUE",
              },
          )


if __name__ == "__main__":
  run_automation()
