import pytest
import jwt
from datetime import timedelta
from pydantic import ValidationError
from auth import get_password_hash, verify_password, create_access_token
from config import SECRET_KEY, ALGORITHM
from security_config import validate_secret
from schemas import UserCreate

@pytest.mark.parametrize("key", [None, "", "short", "x" * 64, "your-very-secure-secret-key-capstone-2026"])
def test_reject_insecure_keys(key):
    with pytest.raises(ValueError): validate_secret(key)

def test_password_and_jwt():
    password = "안전한 암호! 123"
    UserCreate(username="learner", password=password)
    hashed = get_password_hash(password)
    assert verify_password(password, hashed)
    assert not verify_password("wrong", hashed)
    token = create_access_token({"sub": "learner"})
    assert jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])["sub"] == "learner"
    with pytest.raises(jwt.ExpiredSignatureError):
        jwt.decode(create_access_token({"sub": "learner"}, timedelta(seconds=-1)), SECRET_KEY, algorithms=[ALGORITHM])

@pytest.mark.parametrize("password", ["short", "x" * 73, "한" * 25])
def test_password_bounds(password):
    with pytest.raises(ValidationError): UserCreate(username="learner", password=password)
