# Security Policy

## Reporting a vulnerability

Please do not report security vulnerabilities through public GitHub issues.

If you find a vulnerability, contact the maintainer privately. Include enough detail to reproduce the issue, but do not include real Aliyun AccessKeys, private keys, or production certificate material.

## Credential handling

- Store the credentials INI file outside the repository.
- Use `chmod 600` for the credentials file.
- Prefer least-privilege Aliyun RAM users or roles.
- Rotate any credential that may have been exposed.
