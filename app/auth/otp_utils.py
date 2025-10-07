import pyotp
import time

def generate_otp_secret():
    """create a new 2FA"""
    return pyotp.random_base32()

def get_otp_token(secret):
    """Generate a 6-digit verification code based on the secret key"""
    totp = pyotp.TOTP(secret)
    return totp.now()

def verify_otp_token(secret, token):
    """Verify whether the verification code entered by the user is correct"""
    totp = pyotp.TOTP(secret)
    return totp.verify(token)

