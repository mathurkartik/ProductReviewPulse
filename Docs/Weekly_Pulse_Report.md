# Groww — Weekly Review Pulse  |  2026-W16  [pulse-groww-2026-W16]

## Top Themes

1. **App Performance & Bugs** — Users are experiencing systematic lag, frequent app crashes, and login timeouts across various regions, particularly during peak market hours.
2. **Customer Support Friction** — There is increasing dissatisfaction with slow response times, automated bot loops, and non-resolution of complex queries regarding failed transactions.
3. **KYC & Onboarding Delays** — A significant cluster of new users are reporting being stuck in the "Verification Pending" state for over 5 days without any communication.

## Real User Quotes

*"The app keeps crashing when I try to execute an options trade. Lost money because the sell button was completely unresponsive during a volatile spike."* (Play Store, 1★)

*"Customer support is practically non-existent. I raised a ticket about a failed UPI deposit 4 days ago and only get automated replies."* (App Store, 2★)

*"I submitted my PAN and Aadhar last week. It still says verification in progress. My friends got verified on other apps in 10 minutes."* (Play Store, 1★)

*"Love the clean UI for mutual funds, but the recent update made the portfolio refresh rate extremely slow."* (App Store, 3★)

## Action Ideas

*   **Investigate Peak Load Servers**: Conduct a load-testing audit on the options trading execution module between 9:15 AM and 10:00 AM IST.
*   **Implement Live Agent Handoff**: Adjust the customer support chatbot logic to automatically route to a human agent if the user's query involves a "Failed Transaction" keyword.
*   **Automated KYC Status Emails**: Create an automated daily email/push notification for users stuck in the KYC funnel explaining exactly what manual check is causing the delay.

## What This Solves

| Audience | Value |
| :--- | :--- |
| **Engineering / DevOps** | Highlights critical latency issues during market hours, prioritizing server scaling. |
| **Customer Success** | Identifies the main driver of negative sentiment (bot loops) allowing for targeted workflow improvements. |
| **Product & Growth** | Pinpoints the exact friction point in the onboarding funnel that is causing drop-off for newly acquired users. |

---
