#!/bin/bash
# Generate TLS certificates for production MQTT broker
# Multi-Heart-Model System
#
# Usage:
#   ./generate_certificates.sh
#
# This script generates:
# - CA certificate and key
# - Server certificate and key
# - Client certificates for each service
#
# Certificate validity: 10 years (adjust as needed for production)

set -e  # Exit on error

CERT_DIR="/home/user/Multi-Heart-Model/deployment/security/certs"
DAYS_VALID=3650  # 10 years

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Multi-Heart-Model Certificate Generator${NC}"
echo -e "${GREEN}========================================${NC}\n"

# Create certificate directory
mkdir -p "$CERT_DIR"
cd "$CERT_DIR"

# =============================================================================
# 1. Generate Certificate Authority (CA)
# =============================================================================

echo -e "${YELLOW}[1/4] Generating Certificate Authority (CA)...${NC}"

if [ -f "ca.crt" ]; then
    echo -e "${YELLOW}Warning: CA certificate already exists. Skipping...${NC}"
else
    # Generate CA private key
    openssl genrsa -out ca.key 4096

    # Generate CA certificate
    openssl req -new -x509 -days $DAYS_VALID -key ca.key -out ca.crt \
        -subj "/C=US/ST=Missouri/L=St. Louis/O=Multi-Heart-Model/OU=Security/CN=Multi-Heart-Model CA"

    echo -e "${GREEN}✅ CA certificate generated${NC}"
fi

# =============================================================================
# 2. Generate Server Certificate
# =============================================================================

echo -e "\n${YELLOW}[2/4] Generating MQTT Server Certificate...${NC}"

if [ -f "server.crt" ]; then
    echo -e "${YELLOW}Warning: Server certificate already exists. Skipping...${NC}"
else
    # Generate server private key
    openssl genrsa -out server.key 2048

    # Generate certificate signing request (CSR)
    openssl req -new -key server.key -out server.csr \
        -subj "/C=US/ST=Missouri/L=St. Louis/O=Multi-Heart-Model/OU=MQTT Broker/CN=mqtt.multi-heart-model.local"

    # Create server certificate extensions file
    cat > server_ext.cnf << EOF
basicConstraints=CA:FALSE
keyUsage=digitalSignature,keyEncipherment
extendedKeyUsage=serverAuth
subjectAltName=@alt_names

[alt_names]
DNS.1=mqtt.multi-heart-model.local
DNS.2=localhost
DNS.3=*.multi-heart-model.local
IP.1=127.0.0.1
IP.2=::1
EOF

    # Sign server certificate with CA
    openssl x509 -req -in server.csr -CA ca.crt -CAkey ca.key \
        -CAcreateserial -out server.crt -days $DAYS_VALID \
        -extfile server_ext.cnf

    # Clean up
    rm server.csr server_ext.cnf

    # Set appropriate permissions
    chmod 600 server.key
    chmod 644 server.crt

    echo -e "${GREEN}✅ Server certificate generated${NC}"
fi

# =============================================================================
# 3. Generate Client Certificates
# =============================================================================

echo -e "\n${YELLOW}[3/4] Generating Client Certificates...${NC}"

# List of clients needing certificates
clients=(
    "hbcm_service"
    "nodered"
    "motorhand"
    "opensim"
    "web_backend"
    "monitor"
    "tak_bridge"
    "admin"
)

for client in "${clients[@]}"; do
    if [ -f "client_${client}.crt" ]; then
        echo -e "${YELLOW}  Skipping ${client} (already exists)${NC}"
        continue
    fi

    echo -e "  Generating certificate for: ${client}"

    # Generate client private key
    openssl genrsa -out "client_${client}.key" 2048

    # Generate CSR
    openssl req -new -key "client_${client}.key" -out "client_${client}.csr" \
        -subj "/C=US/ST=Missouri/L=St. Louis/O=Multi-Heart-Model/OU=Client/CN=${client}"

    # Create client certificate extensions
    cat > "client_${client}_ext.cnf" << EOF
basicConstraints=CA:FALSE
keyUsage=digitalSignature,keyEncipherment
extendedKeyUsage=clientAuth
EOF

    # Sign client certificate with CA
    openssl x509 -req -in "client_${client}.csr" -CA ca.crt -CAkey ca.key \
        -CAcreateserial -out "client_${client}.crt" -days $DAYS_VALID \
        -extfile "client_${client}_ext.cnf"

    # Clean up
    rm "client_${client}.csr" "client_${client}_ext.cnf"

    # Set permissions
    chmod 600 "client_${client}.key"
    chmod 644 "client_${client}.crt"
done

echo -e "${GREEN}✅ Client certificates generated for ${#clients[@]} clients${NC}"

# =============================================================================
# 4. Generate Combined PEM Files (for convenience)
# =============================================================================

echo -e "\n${YELLOW}[4/4] Generating combined PEM files...${NC}"

for client in "${clients[@]}"; do
    if [ ! -f "client_${client}_combined.pem" ]; then
        cat "client_${client}.crt" "client_${client}.key" "ca.crt" > "client_${client}_combined.pem"
        chmod 600 "client_${client}_combined.pem"
    fi
done

echo -e "${GREEN}✅ Combined PEM files generated${NC}"

# =============================================================================
# 5. Create README and usage instructions
# =============================================================================

cat > README.md << 'EOF'
# Multi-Heart-Model TLS Certificates

## Files Generated

### Certificate Authority (CA)
- `ca.crt` - CA certificate (public)
- `ca.key` - CA private key (KEEP SECRET)

### MQTT Server
- `server.crt` - Server certificate
- `server.key` - Server private key (KEEP SECRET)

### Client Certificates
For each client, three files are generated:
- `client_<name>.crt` - Client certificate
- `client_<name>.key` - Client private key (KEEP SECRET)
- `client_<name>_combined.pem` - Combined certificate+key+CA for convenience

## Usage

### MQTT Broker Configuration
Configure Mosquitto to use these certificates in `mosquitto_production.conf`:

```conf
cafile /path/to/certs/ca.crt
certfile /path/to/certs/server.crt
keyfile /path/to/certs/server.key
```

### Client Configuration (Python/Paho MQTT)

```python
import paho.mqtt.client as mqtt

client = mqtt.Client()
client.tls_set(
    ca_certs="certs/ca.crt",
    certfile="certs/client_hbcm_service.crt",
    keyfile="certs/client_hbcm_service.key"
)
client.connect("mqtt.multi-heart-model.local", 8883)
```

### Client Configuration (Node-RED)

In MQTT node configuration:
- Enable TLS
- CA Certificate: Upload `ca.crt`
- Client Certificate: Upload `client_nodered.crt`
- Client Key: Upload `client_nodered.key`

### Client Configuration (mosquitto_pub/sub)

```bash
mosquitto_pub \
    --cafile certs/ca.crt \
    --cert certs/client_admin.crt \
    --key certs/client_admin.key \
    -h mqtt.multi-heart-model.local \
    -p 8883 \
    -t test/topic \
    -m "Hello, secure MQTT!"
```

## Security Best Practices

1. **Keep private keys secret**: Never commit `.key` files to version control
2. **Restrict permissions**: Private keys should be readable only by their owner (600)
3. **Rotate certificates**: Consider rotating certificates annually in production
4. **Backup CA key**: Store CA key securely offline after certificate generation
5. **Use different certificates per environment**: Don't reuse production certs in development

## Certificate Validation

Verify a certificate:
```bash
openssl x509 -in server.crt -text -noout
```

Verify certificate chain:
```bash
openssl verify -CAfile ca.crt server.crt
```

## Regenerating Certificates

To regenerate all certificates:
```bash
rm -rf certs/*
./generate_certificates.sh
```

⚠️ **Warning**: This will invalidate all existing certificates. All clients must be reconfigured.

## Troubleshooting

### "Certificate verify failed"
- Ensure client has correct CA certificate
- Check certificate dates (not expired)
- Verify hostname matches certificate CN or SAN

### "Connection refused"
- Check MQTT broker is listening on port 8883
- Verify firewall allows traffic on port 8883
- Check broker logs for TLS errors

### "Handshake failure"
- Ensure TLS version compatibility (TLS 1.2+)
- Check cipher suite compatibility
- Verify client certificate is signed by same CA as server
EOF

echo -e "\n${GREEN}========================================${NC}"
echo -e "${GREEN}Certificate Generation Complete!${NC}"
echo -e "${GREEN}========================================${NC}\n"

echo -e "Certificates generated in: ${CERT_DIR}"
echo -e "\nNext steps:"
echo -e "1. Review generated certificates"
echo -e "2. Update mosquitto_production.conf with correct paths"
echo -e "3. Distribute client certificates to respective services"
echo -e "4. ${RED}IMPORTANT: Add *.key files to .gitignore${NC}"
echo -e "5. Start MQTT broker: mosquitto -c mosquitto_production.conf"

echo -e "\n${YELLOW}Security Reminders:${NC}"
echo -e "- ${RED}Never commit private keys (.key files) to version control${NC}"
echo -e "- Store CA key (ca.key) securely offline"
echo -e "- Set restrictive file permissions on all .key files"
echo -e "- Consider using a hardware security module (HSM) for production"

# Create .gitignore to prevent accidental commits
cat > .gitignore << 'EOF'
# Private keys - NEVER commit these!
*.key
*.pem

# Certificate signing requests (not needed after signing)
*.csr

# Serial files
*.srl

# Backup files
*.bak
*.old
EOF

echo -e "\n${GREEN}✅ Created .gitignore to protect private keys${NC}"
