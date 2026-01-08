# Serverless Functions Collection

A curated collection of Python-based AWS Lambda functions focused on practical cloud automation, cost control, and operational safety.

This repository emphasizes event-driven design, least-privilege IAM usage, and defensive automation patterns commonly used in real-world DevOps environments.

## Engineering Focus

This repository focuses on:

- Designing small, single-responsibility Lambda functions  
- Using event-driven and scheduled automations where appropriate  
- Enforcing safety and cost controls through tagging and validation  
- Treating cloud resources as disposable and automatable by default  

Each function is intentionally scoped to solve one operational problem end-to-end.

## Function Library

### 1. S3 to Slack Notifier
**Type:** Observability & Notification
**Location:** [`S3-Slack-Notifier/lambda_function.py`](./S3-Slack-Notifier/lambda_function.py)

A secure, event-driven notification system that bridges AWS S3 and Slack. It instantly alerts a team channel whenever a new file is uploaded to a specific S3 bucket.

**Key Features:**
* **Event-Driven:** Triggered automatically by S3 `ObjectCreated` events.
* **Secure Sharing:** Generates a temporary **Presigned URL** (valid for 1 hour) so users can download private files without public bucket access.
* **Smart Decoding:** Automatically handles URL-encoded filenames (e.g., `Team+Photo.jpg` -> `Team Photo.jpg`) to prevent broken links.
* **Ops-Friendly:** Uses Environment Variables for webhook security and includes robust error handling for "test" events.

**Architecture:**
> User Uploads File -> S3 Bucket -> Lambda Trigger -> Generate Presigned URL -> Post to Slack Webhook

---

### 2. EBS Lifecycle Manager
**Type:** Cost Optimization & Disaster Recovery
**Location:** [`EBS-Lifecycle-Manager/lambda_function.py`](./EBS-Lifecycle-Manager/lambda_function.py)

A scheduled automation function designed to manage EC2 snapshot lifecycles with a strong emphasis on cost control and safe deletion.

This function reflects real-world backup automation patterns where retention policies, tagging discipline, and deletion safety are critical.

**Key Features:**
* **Smart Scheduling:** Triggered daily via Amazon EventBridge (Cron).
* **Cost Optimization:** Enforces a 7-day retention policy, automatically deleting old snapshots to save storage costs.
* **Intelligent Tagging:** Distinguishes between "Initial" (first-time) and "Incremental" backups in logs and tags.
* **Tag-Driven Scope:** Only targets volumes explicitly tagged `Backup: true`, ignoring temporary or non-critical storage.
* **Deletion Safety:** Operates only on snapshots it created itself, ensuring manual or externally-managed backups are never touched.

**Design Notes:**
- Uses tag-based scoping to strictly limit automation blast radius  
- Treats snapshot deletion as a privileged, carefully constrained operation  
- Separates scheduling (EventBridge) from execution (Lambda) for clarity  

**Architecture:**
> EventBridge (Schedule) -> Lambda -> EC2 API (Create/Delete Snapshot) -> Slack Notification

---

### 3. Security Group Auditor
**Type:** Compliance & Remediation
**Location:** [`Security-Group-Auditor/lambda_function.py`](./Security-Group-Auditor/lambda_function.py)

An auto-remediation function acting as a "Compliance Guardrail." It continuously scans network perimeters to detect and neutralize high-risk misconfigurations.

**Key Features:**
* **Vulnerability Detection:** Identifies Security Groups allowing SSH (Port 22) from the open internet (`0.0.0.0/0`).
* **Auto-Remediation:** Immediately revokes the non-compliant ingress rule without affecting other valid traffic (Surgical Revocation).
* **Incident Reporting:** Logs the violation and notifies the security operations channel via Slack.
* **Crash-Safe Logic:** Handles "All Traffic" rules and complex IP ranges without execution failures.

**Architecture:**
> EventBridge (Schedule) -> Lambda -> EC2 API (Describe/Revoke) -> Slack Notification

---

## Design Philosophy

- Prefer multiple small Lambdas over monolithic automation  
- Automate cost and security hygiene, not just provisioning  
- Fail safely and log clearly when assumptions are violated  
- Optimize for operational clarity over minimal code  

These functions are designed to be readable, auditable, and easy to extend.

---

## How to Use

1.  **Clone the repo:**
    ```bash
    git clone [https://github.com/shakeelsaga/Serverless-Functions-Collection.git](https://github.com/shakeelsaga/Serverless-Functions-Collection.git)
    ```
2.  **Select a function:** Navigate to the specific folder.
3.  **Deploy:** Copy the code into the AWS Lambda Console (Python 3.x runtime).
4.  **Configure:**
    * Set the required Environment Variables (e.g., `SLACK_WEBHOOK_URL`).
    * Attach the necessary IAM Permissions (e.g., `ec2:CreateSnapshot`, `ec2:RevokeSecurityGroupIngress`).

## Tech Stack
* **Runtime:** Python 3.9+
* **AWS SDK:** Boto3 (Core integration)
* **Services:** AWS Lambda, Amazon EventBridge, S3, EC2
* **Libraries:** `urllib` (Standard library for lightweight HTTP requests)

## Contributing
I am actively adding new automation patterns to this repository. If you have a suggestion for a useful Lambda function, feel free to open an issue or pull request!

## License
MIT License