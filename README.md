# Allo Innoware - Automated Operations & SLA Management System

An automated operations management prototype built to track recurring tasks, enforce SLAs, automate manager alerts, and handle leadership escalations using Python, Google Sheets, and Linux automation.

## 🚀 System Architecture & Features
1. **Recurring Cycle & Rollover Logic:** Automatically calculates next due dates (Daily, 7, 15, or 30 days) and rolls over tasks upon completion without manual friction.
2. **Single-Point Employee Interface:** Team members manage and update status/Ticket IDs from a single operating view.
3. **Automated SLA Tracking & Email Alerts:** Python script integrated with Gmail SMTP and Google Apps Script Web App API to dispatch same-day overdue warnings to managers.
4. **Escalation Protocol:** Automatically escalates unresolved tasks to leadership after configured SLA thresholds.
5. **Idempotency:** State tracking prevents duplicate emails and redundant loops during multiple daily cron runs.

## 🛠️ Tech Stack
* **Language:** Python 3 (`requests`, `smtplib`)
* **Database / Interface:** Google Sheets & Google Apps Script (REST API Web App)
* **OS & Automation:** Linux Mint (`cron` job scheduled daily at 09:00 AM)
