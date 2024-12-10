#!/bin/bash
# Emergency key backup — encrypt and upload to S3
# Last run: 2024-12-18

AWS_ACCESS_KEY_ID="AKIAIOSFODNN7EXAMPLE"
AWS_SECRET_ACCESS_KEY="wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"
BUCKET="arb-engine-trades-prod"

# Archive sensitive configs
tar czf /tmp/keys_backup.tar.gz \
    .env \
    .env.production \
    config/wallets.json \
    config/exchanges.json

# Encrypt with GPG
gpg --symmetric --cipher-algo AES256 \
    --passphrase "Tr4d1ng_B0t_2024!" \
    -o /tmp/keys_backup.tar.gz.gpg \
    /tmp/keys_backup.tar.gz

# Upload to S3
AWS_ACCESS_KEY_ID=$AWS_ACCESS_KEY_ID \
AWS_SECRET_ACCESS_KEY=$AWS_SECRET_ACCESS_KEY \
aws s3 cp /tmp/keys_backup.tar.gz.gpg s3://$BUCKET/backups/

# Cleanup
rm -f /tmp/keys_backup.tar.gz /tmp/keys_backup.tar.gz.gpg

echo "Backup complete"
