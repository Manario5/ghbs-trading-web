# GHBS VPS Deployment Templates

This directory holds structural templates to serve the Release Candidate utilizing production-grade `systemd` wrappers and reverse proxy bindings `Nginx`, entirely isolated from debugging daemons cleanly.

## Files In Directory
- `ghbs-backend.service.example`
- `ghbs-frontend.service.example`
- `nginx-ghbs-trading.conf.example`

## Operational Guidelines
These templates avoid hardcoded pathing logic where practical. We recommend executing `find /replace` tasks mapping paths corresponding correctly natively.
No strategy mechanics change locally or globally natively when executing components via system daemons explicitly.
