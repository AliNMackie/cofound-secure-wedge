# Contributing to IR35 Platform

Thank you for your interest in contributing to the IR35 Compliance & Prevention Platform. This document outlines the standards and workflows required to maintain our "10/10 production quality".

## Workflow

1. **Create Branch**: Create a new branch for your task.
   ```bash
   git checkout -b feature/your-feature-name
   ```
2. **Make Changes**: Implement your changes, adhering to the coding standards and security requirements.
3. **Run Validation**: Run the necessary validation commands locally before committing.
4. **Create PR**: Push your branch and create a Pull Request.

## Validation

### Terraform
Ensure all Terraform code is formatted and valid.
```bash
terraform fmt -check && terraform validate
```

### Python
Run all tests and ensure there are no hardcoded secrets.
```bash
# Run tests (adjust command as needed based on setup)
pytest

# Check for hardcoded secrets (example using trufflehog or detect-secrets if available, otherwise manual review)
# Do not commit if you suspect secrets are in the code.
```

## Security Checklist

- [ ] **No Credentials in Code**: Ensure no API keys, passwords, or service account keys are hardcoded.
- [ ] **Secrets Management**: All secrets must be stored in Google Secret Manager and accessed via environment variables or the Secret Manager API.
- [ ] **IAM**: Adhere to the Principle of Least Privilege for all IAM roles and permissions.

## PR Review Requirements

- A clear description of the changes.
- Reference to the issue or task being addressed.
- Confirmation that all validation checks passed.
- Screenshot of frontend changes (if applicable).
