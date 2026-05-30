import base64
import io

import pyotp
import qrcode
from django.conf import settings
from django.core.signing import BadSignature, SignatureExpired, TimestampSigner

CHALLENGE_SALT = 'analytica-totp-challenge'
CHALLENGE_MAX_AGE = 600  # 10 minutes


def generate_totp_secret() -> str:
    return pyotp.random_base32()


def build_totp_uri(user, secret: str) -> str:
    issuer = getattr(settings, 'TOTP_ISSUER', 'Analytica')
    label = user.email or user.username
    return pyotp.totp.TOTP(secret).provisioning_uri(name=label, issuer_name=issuer)


def qr_code_data_url(uri: str) -> str:
    img = qrcode.make(uri)
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    encoded = base64.b64encode(buffer.getvalue()).decode('ascii')
    return f'data:image/png;base64,{encoded}'


def verify_totp_code(secret: str, code: str) -> bool:
    if not secret or not code:
        return False
    normalized = str(code).strip().replace(' ', '')
    if not normalized.isdigit() or len(normalized) != 6:
        return False
    totp = pyotp.TOTP(secret)
    return totp.verify(normalized, valid_window=1)


def issue_challenge_token(user_id: int, purpose: str) -> str:
    signer = TimestampSigner(salt=CHALLENGE_SALT)
    return signer.sign(f'{user_id}:{purpose}')


def parse_challenge_token(token: str):
    signer = TimestampSigner(salt=CHALLENGE_SALT)
    raw = signer.unsign(token, max_age=CHALLENGE_MAX_AGE)
    user_id_str, purpose = raw.split(':', 1)
    return int(user_id_str), purpose


def read_challenge_token(token: str):
    try:
        return parse_challenge_token(token)
    except (BadSignature, SignatureExpired, ValueError):
        return None, None
