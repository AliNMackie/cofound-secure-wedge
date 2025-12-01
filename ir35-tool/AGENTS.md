# IR35 Platform - Agent Instructions

This document outlines the architecture, components, and development standards for the IR35 Compliance & Prevention Platform. All agents and developers must adhere to these guidelines to ensure a "10/10 production quality" system.

## Core Components

The platform consists of four core components:

1.  **RAG Indexer**
    -   Responsible for indexing and retrieving relevant documents for compliance assessments.
    -   Uses Python Cloud Functions.

2.  **Assessment API**
    -   Provides the interface for conducting IR35 assessments.
    -   Built with Python Cloud Functions and secured via API Gateway.

3.  **n8n Workflows**
    -   Handles automation and orchestration of business logic.
    -   Integrates various services and manages process flows.

4.  **Terraform Infrastructure**
    -   Defines the infrastructure as code (IaC) for the entire platform on Google Cloud Platform (GCP).
    -   Manages resources such as Cloud Functions, API Gateway, Secret Manager, and networking.

## Architecture Principles

*(Based on IR35_Platform_Playbook_v10.md)*

*   **Cloud-Native**: Leveraging GCP managed services (Cloud Functions, Run, Pub/Sub) for scalability and reduced operational overhead.
*   **Security-First**:
    *   **Secret Manager**: All sensitive configuration and credentials must be stored in Google Secret Manager. No secrets in code or environment variables.
    *   **IAM**: Strict adherence to Least Privilege principle. Service accounts should have only the permissions necessary for their function.
    *   **API Gateway**: All public endpoints must be exposed through API Gateway for authentication and rate limiting.
*   **Infrastructure as Code**: All infrastructure changes must be made via Terraform. Manual changes in the console are prohibited.
*   **Production Quality**: Code must be modular, tested, and documented.

## Development Conventions

### Terraform Patterns
*   Use modules for reusable components.
*   State files must be stored remotely (e.g., GCS bucket), not locally.
*   Run `terraform fmt` and `terraform validate` before committing.

### Python Standards
*   Follow PEP 8 style guidelines.
*   Ensure high test coverage (unit and integration tests).
*   Use type hinting where possible.
*   **Security**: Never hardcode secrets. Use the Google Cloud Secret Manager client library to access secrets at runtime.

### Security Requirements
*   Rotate keys and secrets regularly.
*   Validate all inputs at the API boundary.
*   Ensure encryption in transit and at rest.

## Deployment Plan

*(Reference: README.md)*

The deployment follows a structured 6-step plan:

1.  [Step 1 from README.md - Placeholder: Infrastructure Setup]
2.  [Step 2 from README.md - Placeholder: Core Services Deployment]
3.  [Step 3 from README.md - Placeholder: Integration Configuration]
4.  [Step 4 from README.md - Placeholder: Security Hardening]
5.  [Step 5 from README.md - Placeholder: Testing & Validation]
6.  [Step 6 from README.md - Placeholder: Go-Live]

*Note: Please refer to `README.md` and `IR35_Platform_Playbook_v10.md` for the detailed 6-step deployment plan and comprehensive architecture principles.*
