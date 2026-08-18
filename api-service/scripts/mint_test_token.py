import sys
from jose import jwt
from app.config import settings

tenant_id = sys.argv[1]
student_id = sys.argv[2] if len(sys.argv) > 2 else "s1"

token = jwt.encode(
    {"tenant_id": tenant_id, "student_id": student_id, "aud": settings.jwt_audience, "iss": settings.jwt_issuer},
    settings.jwt_dev_secret,
    algorithm="HS256",
)
print(token)
