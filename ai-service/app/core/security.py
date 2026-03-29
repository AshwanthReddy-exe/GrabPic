import hmac
import hashlib
import base64
import time
from app.config import settings

def verify_token(event_id: str, filename: str, token: str) -> bool:
    if not token or "." not in token:
        return False
        
    try:
        # Split token: encodedPayload.encodedSignature
        parts = token.split(".")
        if len(parts) != 2:
            return False
            
        encoded_payload, encoded_signature = parts
        
        # Decode payload
        # Add padding if necessary for standard b64 decode
        payload_bytes = base64.urlsafe_b64decode(encoded_payload + "=" * (-len(encoded_payload) % 4))
        payload = payload_bytes.decode("utf-8")
        
        # Payload format: eventId:filename:exp
        payload_parts = payload.split(":")
        if len(payload_parts) != 3:
            return False
            
        p_event_id, p_filename, p_exp = payload_parts
        
        # Strict validation
        if p_event_id != event_id or p_filename != filename:
            return False
            
        # Check expiration
        now = int(time.time())
        if now > int(p_exp):
            return False
            
        # Verify signature
        secret = settings.IMAGE_TOKEN_SECRET.encode("utf-8")
        expected_mac = hmac.new(secret, payload.encode("utf-8"), hashlib.sha256).digest()
        expected_signature = base64.urlsafe_b64encode(expected_mac).rstrip(b"=").decode("utf-8")
        
        return hmac.compare_digest(encoded_signature, expected_signature)
        
    except Exception as e:
        print(f"Token verification error: {e}")
        return False
