import os
import binascii

# Generate a 24-byte (192-bit) random key
secret_key = binascii.hexlify(os.urandom(24)).decode('utf-8')
print(secret_key)