import os
# for encryption
from cryptography.hazmat.primitives import hashes, padding
from cryptography.hazmat.backends import default_backend
# for encrypting passwords
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
# for hashing password
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
import secrets
import hashlib
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
def encrypt_files(data, key):
    iv = os.urandom(16)
    cipher = Cipher(algorithms.AES(key), modes.CBC(iv),
                    backend=default_backend())

    encryptor = cipher.encryptor()
    padder = padding.PKCS7(128).padder()  # 16-Bytes
    padded_data = padder.update(data) + padder.finalize()

    encrypted_data = encryptor.update(padded_data) + encryptor.finalize()
    return iv + encrypted_data
    # CBC mode is the most efficient one with the file encryption


def decrypt_files(ciphertext, key):
    iv = ciphertext[:16]
    cipher = Cipher(algorithms.AES(key), modes.CBC(iv),
                    backend=default_backend())
    decryptor = cipher.decryptor()

    padded_plaintext = decryptor.update(ciphertext[16:]) + decryptor.finalize()

    unpadder = padding.PKCS7(128).unpadder()
    plaintext = unpadder.update(padded_plaintext) + unpadder.finalize()

    return plaintext


def hash_sha256(data):
    digest = hashes.Hash(hashes.SHA256())
    digest.update(data)
    hashed = digest.finalize()
    return hashed.hex()

def hash_sha1(data):
    return hashlib.sha1(data.encode())


def generate_key_pair():
    P = int("""
       FFFFFFFF FFFFFFFF C90FDAA2 2168C234 C4C6628B 80DC1CD1
       29024E08 8A67CC74 020BBEA6 3B139B22 514A0879 8E3404DD
       EF9519B3 CD3A431B 302B0A6D F25F1437 4FE1356D 6D51C245
       E485B576 625E7EC6 F44C42E9 A637ED6B 0BFF5CB6 F406B7ED
       EE386BFB 5A899FA5 AE9F2411 7C4B1FE6 49286651 ECE65381
       FFFFFFFF FFFFFFFF
       """.replace(" ", "").replace("\n", ""), 16)
    G = 5
    private_key = secrets.randbelow(P - 2) + 1
    public_key = pow(G, private_key, P)
    return private_key, public_key, P
