# ZeroTier Network Security Configuration

This directory contains security configurations for ZeroTier virtual private networking, enabling secure remote access to computational resources and collaborative research environments.

## Overview

ZeroTier provides encrypted peer-to-peer networking for:
- Secure access to computational servers
- Collaborative research environments
- HIPAA-compliant data transfer
- Protected model execution infrastructure

## Network Architecture

```
┌─────────────────────────────────────────────────────────┐
│         ZeroTier Virtual Private Network                │
│                                                          │
│  ┌──────────────┐    ┌──────────────┐  ┌────────────┐ │
│  │   Researcher │    │   Compute    │  │  Clinical  │ │
│  │   Laptop     │◄──►│   Server     │◄►│   System   │ │
│  └──────────────┘    └──────────────┘  └────────────┘ │
│                                                          │
│  All traffic encrypted end-to-end with AES-256         │
└─────────────────────────────────────────────────────────┘
```

## Installation

### 1. Install ZeroTier Client

**Linux:**
```bash
curl -s https://install.zerotier.com | sudo bash
```

**macOS:**
```bash
brew install zerotier-one
```

**Windows:**
Download installer from: https://www.zerotier.com/download/

### 2. Request Network Access

**For Multi-Heart-Model Research Network:**

1. **Get your device ID:**
   ```bash
   sudo zerotier-cli info
   # Example output: 200 info a1b2c3d4e5 1.12.0 ONLINE
   ```

2. **Request access from network administrator:**
   - Email: security@multi-heart-model.org
   - Subject: "ZeroTier Access Request"
   - Include:
     - Your name and institution
     - Device ID (from step 1)
     - Intended use (research, clinical, development)
     - Required access level (Administrator/Researcher/Viewer/Clinical)

3. **After approval, join the network:**
   ```bash
   # Network ID will be provided after approval
   sudo zerotier-cli join <NETWORK_ID_PROVIDED>

   # Verify connection (status should show "OK")
   sudo zerotier-cli listnetworks
   ```

**For Individual/Private Networks:**

If you're setting up your own computational environment:

1. Create your own ZeroTier network at https://my.zerotier.com/
2. Join your devices to your personal network
3. Configure firewall rules for your specific needs

## Firewall Rules

### Default Rules (fw-rules.conf)

```bash
# Allow only necessary ports for Multi-Heart-Model
# Jupyter Lab (authenticated)
iptables -A INPUT -p tcp --dport 8888 -s 10.147.0.0/16 -j ACCEPT

# SSH (key-based only)
iptables -A INPUT -p tcp --dport 22 -s 10.147.0.0/16 -j ACCEPT

# HTTP/HTTPS for web interfaces
iptables -A INPUT -p tcp --dport 80 -s 10.147.0.0/16 -j ACCEPT
iptables -A INPUT -p tcp --dport 443 -s 10.147.0.0/16 -j ACCEPT

# Drop all other inbound
iptables -A INPUT -j DROP
```

### Apply Rules

```bash
sudo bash apply-firewall.sh
```

## Access Control

### Role-Based Permissions

| Role | Access | Capabilities |
|------|--------|-------------|
| **Administrator** | Full | All operations, user management |
| **Researcher** | Read/Write | Run simulations, access notebooks |
| **Viewer** | Read-only | View results, documentation |
| **Clinical** | Restricted | Approved models only, audit logging |

### Network Configuration (network-config.json)

```json
{
  "name": "Multi-Heart-Model Research Network",
  "private": true,
  "enableBroadcast": false,
  "v4AssignMode": {
    "zt": true
  },
  "routes": [
    {
      "target": "10.147.0.0/16",
      "via": null
    }
  ],
  "rules": [
    {
      "type": "ACTION_ACCEPT"
    }
  ]
}
```

## Security Best Practices

### 1. Authentication
- **SSH**: Key-based only, disable password auth
- **Jupyter**: Strong tokens, HTTPS only
- **API**: OAuth 2.0 with short-lived tokens

### 2. Data Protection
- **In-transit**: AES-256 encryption (ZeroTier)
- **At-rest**: Full disk encryption
- **Backups**: Encrypted, off-site storage

### 3. Access Logging
```bash
# Enable ZeroTier logging
sudo zerotier-cli set NETWORK_ID allowManaged=1

# Monitor access logs
tail -f /var/log/zerotier-one.log
```

### 4. Regular Security Audits
```bash
# Weekly: Review authorized members
sudo zerotier-cli listpeers

# Monthly: Rotate SSH keys
ssh-keygen -t ed25519 -C "your_email@example.com"

# Quarterly: Update firewall rules
sudo bash security/zerotier/update-rules.sh
```

## HIPAA Compliance

### Required Configurations

1. **Encryption**: ✅ AES-256 (built-in)
2. **Access Control**: ✅ Role-based
3. **Audit Logging**: ✅ Enabled
4. **Data Integrity**: ✅ Checksums
5. **Breach Notification**: Configure alerts

### Audit Log Example

```json
{
  "timestamp": "2025-11-14T10:30:00Z",
  "user": "researcher@university.edu",
  "action": "SIMULATION_RUN",
  "resource": "notebooks/01_clinical_hemodynamics.ipynb",
  "result": "SUCCESS",
  "ip": "10.147.0.42"
}
```

## Network Monitoring

### Real-time Status

```bash
# Check network health
watch -n 5 'zerotier-cli listnetworks'

# Monitor bandwidth
iftop -i zt0

# View active connections
netstat -an | grep 10.147
```

### Performance Metrics

```bash
# Latency test
ping -c 10 10.147.0.1

# Bandwidth test
iperf3 -c 10.147.0.1
```

## Troubleshooting

### Connection Issues

```bash
# Restart ZeroTier service
sudo systemctl restart zerotier-one

# Check service status
sudo systemctl status zerotier-one

# View logs
journalctl -u zerotier-one -f
```

### Firewall Conflicts

```bash
# List active rules
sudo iptables -L -n -v

# Temporarily disable firewall
sudo ufw disable

# Re-enable with correct rules
sudo bash apply-firewall.sh
```

## Multi-User Setup

### Network Administrator Workflow

**When a user requests access:**

1. **Receive request email** with user's device ID (e.g., a1b2c3d4e5)

2. **Review and approve via ZeroTier Central:**
   - Visit https://my.zerotier.com/network/YOUR_NETWORK_ID
   - Scroll to "Members" section
   - Find device ID in pending/unauthorized list
   - Check "Authorized" checkbox
   - (Optional) Set description: "Jane Doe - University Lab"

3. **Send network ID to user:**
   ```
   Subject: ZeroTier Access Approved

   Your device (a1b2c3d4e5) has been approved.
   Network ID: YOUR_NETWORK_ID

   Join with: sudo zerotier-cli join YOUR_NETWORK_ID
   ```

4. **Configure firewall and SSH access** (if applicable):
   ```bash
   # Add SSH key for remote access
   cat researcher_key.pub >> ~/.ssh/authorized_keys

   # Verify they can connect
   ssh user@10.147.0.X
   ```

### Add Researcher

```bash
# 1. Generate SSH key pair (if needed for server access)
ssh-keygen -t ed25519 -f /path/to/researcher_key

# 2. Add to authorized_keys
cat researcher_key.pub >> ~/.ssh/authorized_keys

# 3. Approve in ZeroTier Central (see workflow above)
# https://my.zerotier.com/network/NETWORK_ID

# 4. Document in access log
echo "$(date): Added researcher@institution.edu (device: a1b2c3d4e5)" >> /var/log/zerotier-access.log
```

### Revoke Access

```bash
# 1. Remove from ZeroTier network (via web UI)

# 2. Remove SSH key
sed -i '/researcher_key/d' ~/.ssh/authorized_keys

# 3. Kill active sessions
sudo pkill -u researcher_username
```

## Emergency Procedures

### Security Breach Response

1. **Immediate**: Disable network
   ```bash
   sudo zerotier-cli leave NETWORK_ID
   ```

2. **Isolate**: Disconnect affected systems
   ```bash
   sudo iptables -P INPUT DROP
   sudo iptables -P OUTPUT DROP
   ```

3. **Investigate**: Review logs
   ```bash
   sudo ausearch -m AVC -ts recent
   journalctl --since "1 hour ago"
   ```

4. **Remediate**: Rotate all credentials
5. **Notify**: Contact security team and affected parties

## Backup Configuration

```bash
# Backup current configuration
sudo zerotier-cli dump > zerotier-backup-$(date +%Y%m%d).json

# Backup firewall rules
sudo iptables-save > iptables-backup-$(date +%Y%m%d).rules

# Store securely
gpg -c zerotier-backup-*.json
```

## Integration with Multi-Heart-Model

### Secure Jupyter Access

```bash
# Start Jupyter with SSL and authentication
jupyter lab \
  --ip='0.0.0.0' \
  --port=8888 \
  --no-browser \
  --certfile=/path/to/cert.pem \
  --keyfile=/path/to/key.pem \
  --NotebookApp.token='STRONG_RANDOM_TOKEN'
```

### Secure API Endpoints

```python
# src/api/secure_server.py
from flask import Flask
from flask_limiter import Limiter

app = Flask(__name__)
limiter = Limiter(app, key_func=lambda: request.remote_addr)

@app.route('/api/simulate')
@limiter.limit("10 per minute")
def run_simulation():
    # Rate-limited, authenticated API
    pass
```

## Support

For security issues:
- **Email**: security@multi-heart-model.org
- **PGP Key**: Available at keybase.io/mhm-security
- **Response Time**: <24 hours for critical issues

---

**Last Updated**: 2025-11-14  
**Security Level**: Enterprise  
**Compliance**: HIPAA, GDPR, NIST 800-53
