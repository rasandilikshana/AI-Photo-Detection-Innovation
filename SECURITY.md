# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 1.0.x   | :white_check_mark: |
| < 1.0   | :x:                |

## Reporting a Vulnerability

**Please do not report security vulnerabilities through public GitHub issues.**

Instead, please report them via email to:
- **Email**: rasandilikshana@gmail.com
- **Subject**: [SECURITY] Brief description

### What to Include

1. **Description** of the vulnerability
2. **Steps to reproduce** the issue
3. **Potential impact** assessment
4. **Suggested fix** (if you have one)
5. **Your contact information**

### Response Timeline

- **Acknowledgment**: Within 48 hours
- **Initial assessment**: Within 7 days
- **Fix timeline**: Depends on severity
  - Critical: 24-72 hours
  - High: 1-2 weeks
  - Medium: 2-4 weeks
  - Low: Next release cycle

## Security Best Practices

### For Developers

1. **Never commit secrets**
   - Use `.env` files (gitignored)
   - Use environment variables
   - Never hardcode API keys, passwords, or tokens

2. **Input validation**
   - Always validate user input
   - Sanitize file uploads
   - Use parameterized queries

3. **Dependency management**
   - Keep dependencies updated
   - Run `pip list --outdated` regularly
   - Use `safety check` for vulnerability scanning

4. **Code review**
   - All code must be reviewed before merging
   - Security-focused review for authentication/authorization code
   - Use automated security scanning (Bandit, etc.)

### For Deployments

1. **HTTPS only**
   - Always use TLS/SSL in production
   - Redirect HTTP to HTTPS
   - Use valid certificates

2. **Database security**
   - Use strong passwords
   - Limit network access
   - Enable encryption at rest
   - Regular backups

3. **API security**
   - Implement rate limiting
   - Use API keys/tokens
   - Validate all inputs
   - Return minimal error information

4. **File uploads**
   - Validate file types
   - Scan for malware
   - Limit file sizes
   - Store in isolated locations

5. **Environment variables**
   - Never expose `.env` files
   - Use secrets management (AWS Secrets Manager, HashiCorp Vault, etc.)
   - Rotate credentials regularly

## Known Security Considerations

### Current Implementation

1. **File Upload Validation**
   - ✅ File type validation
   - ✅ File size limits
   - ⚠️ Malware scanning (not implemented yet)

2. **API Security**
   - ✅ Input validation
   - ⚠️ Rate limiting (not implemented yet)
   - ⚠️ Authentication (not implemented yet)

3. **Data Protection**
   - ⚠️ Encryption at rest (not implemented yet)
   - ⚠️ Encryption in transit (HTTP only in dev)
   - ✅ Temporary file cleanup

### Planned Security Enhancements

#### Phase 2 (Next Release)
- [ ] Implement JWT-based authentication
- [ ] Add rate limiting (per IP, per user)
- [ ] Add API key management
- [ ] Implement request signing

#### Phase 3
- [ ] Add malware scanning for uploads
- [ ] Implement file encryption
- [ ] Add audit logging
- [ ] Set up intrusion detection

## Security Headers

For production deployment, ensure these security headers are set:

```nginx
# Example Nginx configuration
add_header X-Frame-Options "SAMEORIGIN" always;
add_header X-Content-Type-Options "nosniff" always;
add_header X-XSS-Protection "1; mode=block" always;
add_header Referrer-Policy "strict-origin-when-cross-origin" always;
add_header Content-Security-Policy "default-src 'self'" always;
add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
```

## Dependency Security

### Automated Scanning

```bash
# Check for known vulnerabilities
safety check

# Security linting
bandit -r src/backend/ai-detection-service/app/

# Update dependencies
pip list --outdated
pip install --upgrade package_name
```

### Dependency Review

- All dependency updates reviewed before merging
- Major updates tested thoroughly
- Security advisories monitored regularly

## Incident Response Plan

### In Case of Security Breach

1. **Immediate actions**
   - Isolate affected systems
   - Preserve evidence
   - Notify maintainers

2. **Assessment**
   - Determine scope of breach
   - Identify compromised data
   - Assess impact

3. **Remediation**
   - Apply security fixes
   - Rotate credentials
   - Update affected systems

4. **Communication**
   - Notify affected users
   - Public disclosure (if appropriate)
   - Update security documentation

5. **Post-incident**
   - Root cause analysis
   - Implement preventive measures
   - Update security practices

## Security Contacts

- **Primary**: rasandilikshana@gmail.com
- **GitHub**: @rasandilikshana

## Acknowledgments

We thank security researchers who responsibly disclose vulnerabilities. Contributors will be acknowledged (unless they prefer to remain anonymous).

---

**Last Updated**: November 6, 2025
**Version**: 1.0.0
