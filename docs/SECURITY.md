# GreenMind Security Documentation

This document outlines the security measures, practices, and incident response plan for the GreenMind project.

## 1. Security Checklist (Deployment)

Before moving to production, ensure the following are completed:

- [ ] **DEBUG=False**: Never run production with debug enabled.
- [ ] **SECRET_KEY**: Rotated and stored in a secure environment variable (not in Git).
- [ ] **HTTPS**: Use SSL/TLS for all communication. Django is configured to redirect to SSL.
- [ ] **Security Headers**: HSTS, XSS Filter, Content Type Nosniff, and X-Frame-Options are pre-configured in `settings.py`.
- [ ] **ALLOWED_HOSTS**: Set to specific production domains.
- [ ] **CORS/CSRF**: Configured to trust only known frontend/API origins.
- [ ] **Database Constraints**: Negative values for stock and price are blocked at the DB level via CHECK constraints.

## 2. Secrets Management

### Rotating SECRET_KEY

If the `SECRET_KEY` is compromised:

1. Generate a new key: `python -c "import secrets; print(secrets.token_urlsafe(50))"`
2. Update the environment variable on the server.
3. Restart the application.
   _Note: This will invalidate all current sessions._

## 3. Database Backup & Recovery

- **Backup Schedule**: Daily full backups, hourly transaction log backups (managed via SQL Server Agent).
- **Storage**: Backups should be stored on a separate physical drive or cloud storage (S3/Azure Blob).
- **Test**: Perform a restore test once every quarter.

## 4. Incident Response Plan

In case of a security breach:

1. **Containment**: Stop the application or revoke compromised API tokens immediately.
2. **Analysis**: Check `security.log` and `Admin_Action_Logs` in SQL Server to identify the breach source and affected data.
3. **Eradication**: Patch the vulnerability, rotate all credentials (DB, JWT, Secret Key).
4. **Recovery**: Restore from the latest clean backup if data was corrupted.
5. **Post-Mortem**: Document the incident and update security measures accordingly.

## 5. Audit Trail

All administrative actions (ADD/EDIT/DELETE products, stock simulation) are logged in the `Admin_Action_Logs` table with:

- UserID
- IP Address
- Timestamp
- Old vs New Values
