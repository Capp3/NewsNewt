# Security Policy

## Supported Versions

We actively support security updates for the following versions:

| Version | Supported          |
| ------- | ------------------ |
| 0.1.x   | :white_check_mark: |

## Reporting a Vulnerability

If you discover a security vulnerability in NewsNewt, please report it responsibly:

1. **Do not** open a public GitHub issue
2. Email security concerns to: [security contact email]
3. Include:
   - Description of the vulnerability
   - Steps to reproduce
   - Potential impact
   - Suggested fix (if any)

We will acknowledge receipt within 48 hours and provide an update on the status within 7 days.

## Security Considerations

NewsNewt is designed to run in a **private Docker network** and should not be exposed to the public internet. Key security considerations:

- The service accepts URLs and makes HTTP requests to archive services
- No authentication is required at the service level (relies on network isolation)
- All outgoing requests target archive services and archived snapshot URLs
- Input validation is performed on all URLs
- Timeout limits prevent resource exhaustion

## Disclosure Process

1. Report received and acknowledged
2. Vulnerability confirmed and assessed
3. Fix developed and tested
4. Security update released
5. Public disclosure (if appropriate)

We appreciate your help in keeping NewsNewt secure.

