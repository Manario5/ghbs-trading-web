const fs = require('fs');
const files = [
  'scripts/release_status.sh',
  'scripts/systemd_status.sh',
  'scripts/private_public_exposure_check.sh',
  'scripts/full_https_rollback_checklist.sh',
  'deploy/nginx-ghbs-domain-http.conf.example',
  'deploy/nginx-ghbs-local-sandbox.conf.example',
  'deploy/nginx-ghbs-trading.conf.example',
  'deploy/nginx-ghbs-tailscale-private.conf.example',
  'deploy/ghbs-backend.service.example',
  'docs/SANDBOX_RUNBOOK.md',
  'docs/VPS_DEPLOYMENT_RUNBOOK.md',
  'docs/PHASE_6J_VPS_SERVICE_DEPLOYMENT_HARDENING_REPORT.md',
  'docs/PHASE_6K_VPS_SERVICE_TEMPLATES_REPORT.md',
  'docs/PHASE_3A_REPORT.md',
];
files.forEach(f => {
  if (fs.existsSync(f)) {
    let content = fs.readFileSync(f, 'utf8');
    let mod = content.replace(/8000/g, '8001');
    if (content !== mod) {
      fs.writeFileSync(f, mod);
      console.log('Updated ' + f);
    }
  }
});
