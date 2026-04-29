import bcrypt

def hash_password(password):
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

def verify_password(password, hashed):
    if not hashed:
        return False

    if isinstance(hashed, str):
        hashed = hashed.encode()

    try:
        return bcrypt.checkpw(password.encode(), hashed)
    except Exception:
        return False
