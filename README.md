# Serverless Functions Collection

A curated collection of Python-based AWS Lambda functions designed to solve real-world cloud automation and DevOps problems.

Each folder in this repository contains a self-contained function with its own logic, intended to be deployed to the AWS Serverless environment.

## Function Library

### 1. S3 to Slack Notifier (The "Serverless Drop-Box")
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

## How to Use

1.  **Clone the repo:**
    ```bash
    git clone [https://github.com/shakeelsaga/Serverless-Functions-Collection.git](https://github.com/shakeelsaga/Serverless-Functions-Collection.git)
    ```
2.  **Select a function:** Navigate to the specific folder.
3.  **Deploy:** Copy the code into the AWS Lambda Console (Python 3.x runtime).
4.  **Configure:** Set the required Environment Variables (documented in the code comments).

## Tech Stack
* **Runtime:** Python 3.9+
* **AWS SDK:** Boto3 (Core integration)
* **Libraries:** `urllib` (Standard library for lightweight HTTP requests)

## Contributing
I am actively adding new automation patterns to this repository. If you have a suggestion for a useful Lambda function, feel free to open an issue or pull request!

## License
MIT License