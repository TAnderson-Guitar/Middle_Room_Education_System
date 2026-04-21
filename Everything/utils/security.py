import bcrypt

def hash_password(password):
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

def verify_password(password, hashed):
    if isinstance(hashed, str):
        hashed = hashed.encode()

    return bcrypt.checkpw(password.encode(), hashed)
