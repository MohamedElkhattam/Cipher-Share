# crypto_utils.py
import os
import secrets

# for encryption 
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC  # for encrypting passwords
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend

# for hashing password
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

# Password Hasher instance (Argon2)
ph = PasswordHasher()


def hash_password(password):
    hashed_password = ph.hash(password)
    return hashed_password


def verify_password(password, hashed_password):
    try:
        return ph.verify(hashed_password, password)
    except VerifyMismatchError:
        return False


# === KEY DERIVATION (for encryption) ===
def derive_key_from_password(password, salt):
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100000,
        backend=default_backend()
    )
    return kdf.derive(password.encode())


# === ENCRYPTION / DECRYPTION ===
def encrypt_data(data, key):
    iv = secrets.token_bytes(16)
    cipher = Cipher(algorithms.AES(key), modes.CFB(iv), backend=default_backend())
    encryptor = cipher.encryptor()
    return iv + encryptor.update(data) + encryptor.finalize()


def decrypt_data(ciphertext, key):
    iv = ciphertext[:16]
    cipher = Cipher(algorithms.AES(key), modes.CFB(iv), backend=default_backend())
    decryptor = cipher.decryptor()
    return decryptor.update(ciphertext[16:]) + decryptor.finalize()


# === USAGE EXAMPLE ===
if __name__ == "__main__":
    user_password = "MySecurePassword123"

    print("\n--- Password Hashing ---")
    hashed = hash_password(user_password)
    print("Hashed:", hashed)
    print("Verified:", verify_password(user_password, hashed))

    # salt = os.urandom(16)
    # print("\n--- Key Derivation ---")
    # key = derive_key_from_password(password, salt)
    # print("Key (hex):", key.hex())
    #
    # print("\n--- Encrypt/Decrypt ---")
    # secret = b"This is a secret message."
    # encrypted = encrypt_data(secret, key)
    # print("Encrypted:", encrypted.hex())
    #
    # decrypted = decrypt_data(encrypted, key)
    # print("Decrypted:", decrypted.decode())
