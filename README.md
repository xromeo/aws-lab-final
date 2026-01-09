
# Signed URL File Gateway (Serverless)

This project implements a secure, internal "File Gateway" service that allows users to upload and download files from an Amazon S3 bucket without exposing the bucket publicly. The system uses **temporary, cryptographically signed URLs** to control access, ensuring that every download is time-limited and secure.

## 🏗️ Architecture

The solution follows the **Serverless track**:
* **Amazon API Gateway (HTTP API):** Acts as the front door for the service.
* **AWS Lambda (Python):** Contains the logic to generate pre-signed URLs and handle the 307 redirect logic.
* **Amazon S3:** Private storage for uploaded files.
* **IAM Role:** Implements least-privilege access, allowing the Lambda function to perform `s3:PutObject` and `s3:GetObject` only.



---

## 🚀 Deployment via GitHub Actions (Forking Workflow)

This project is designed to be fully reproducible using Infrastructure as Code (AWS SAM). To deploy this to your own AWS account, follow these steps:

### 1. Fork this Repository
Click the **Fork** button at the top right of this page to create a copy of this repository in your own GitHub account.

### 2. Configure GitHub Secrets and Variables
Go to **Settings > Secrets and variables > Actions** in your forked repository and add the following:

* **Variables:**
  * `AWS_ACCOUNT_ID`: Your 12-digit AWS Account ID.

### 3. Configure OpenID connect in AWS
Use this documentation
https://docs.github.com/en/actions/how-tos/secure-your-work/security-harden-deployments/oidc-in-aws
The rol name should be `githubaws` 

### 4. Run the Pipeline
The deployment is automated via the `.github/workflows/deploy.yaml` file.
1. Push a change to the `main` branch or manually trigger the **Workflow Dispatch**.
2. GitHub Actions will execute `sam build` and `sam deploy`, creating the `file-gateway` stack in your account.

---

## 📋 API Documentation

### 1. Endpoint A: POST `/files`
**Goal:** Prepare a secure upload to S3.
* **Request Body:** `{"filename": "example.jpg", "contentType": "image/jpeg"}`
* **Response:** Returns a JSON containing the `objectKey` and a short-lived `uploadUrl` (15 minutes).

### 2. Endpoint B: GET `/files/{objectKey+}`
**Goal:** Securely download a file via an HTTP redirect.
* **Behavior:** The API generates a pre-signed download URL valid for 1 hour and returns an **HTTP 307 Temporary Redirect**.
* **Redirección Logic:** We use **307** to ensure the client maintains the GET method and to signify the temporary nature of the S3 access.

---

## 🧪 Testing with cURL

Once deployed, obtain the **ApiUrl** from the GitHub Actions output or the CloudFormation console.

CloudFormation outputs from deployed stack
-------------------------------------------------------------------------------------------------
Outputs                                                                                         
-------------------------------------------------------------------------------------------------
Key                 ApiUrl                                                                      
Description         URL base de tu API Gateway                                                  
Value               https://y4dty28461.execute-api.us-east-1.amazonaws.com                      

Key                 BucketName                                                                  
Description         Nombre del bucket creado                                                    
Value               file-gateway-319029039131-us-east-1                                         
-------------------------------------------------------------------------------------------------


### Step 1: Get the Upload URL
```bash
curl -X POST https://<API_ID>.execute-api.<REGION>[.amazonaws.com/files](https://.amazonaws.com/files) \
     -H "Content-Type: application/json" \
     -d '{"filename": "test_file.txt", "contentType": "text/plain"}'
```

### Step 2: Upload the File (PUT)
Copy the  `uploadUrl` from the previous step and run:

```bash
echo "Hello from File Gateway" > test_file.txt
curl -X PUT "<UPLOAD_URL_HERE>" \
     -H "Content-Type: text/plain" \
     --upload-file test_file.txt
```

### Step 3: Download via Redirect (GET)
Use the  `-L` flag to follow the 307 redirect automatically:

```bash
echo "Hello from File Gateway" > test_file.txt
curl -X PUT "<UPLOAD_URL_HERE>" \
     -H "Content-Type: text/plain" \
     --upload-file test_file.txt
```
