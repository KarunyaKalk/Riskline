import time
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

from app.main import app
from app.core.database import Base
from app.api.deps import get_db
from app.core.security import create_access_token, hash_password
from app.models.organization import Organization
from app.models.user import User, UserRole

# Use in-memory SQLite engine for standalone benchmark
engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)

db = TestingSessionLocal()
test_org = Organization(name="Benchmark Org", slug="benchmark-org")
db.add(test_org)
db.flush()

test_user = User(
    org_id=test_org.id,
    email="benchmark@company.com",
    hashed_password=hash_password("Password123!"),
    role=UserRole.ADMIN,
    status="active",
)
db.add(test_user)
db.commit()

token_claims = {
    "sub": str(test_user.id),
    "org_id": str(test_org.id),
    "role": "admin",
}
test_token = create_access_token(data=token_claims)
headers = {"Authorization": f"Bearer {test_token}"}


def override_get_db():
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)


def run_benchmark(concurrency: int = 50):
    print(f"\n==================================================")
    print(f"🚀 Running Load Benchmark ({concurrency} concurrent requests)")
    print(f"==================================================")

    # 1. Health check benchmark
    start_time = time.time()
    for _ in range(concurrency):
        resp = client.get("/health")
        assert resp.status_code == 200
    duration = time.time() - start_time
    print(f"✅ Endpoint /health: {concurrency} requests completed in {duration:.3f}s ({(concurrency/duration):.1f} req/s)")

    # 2. Get Changes benchmark
    start_time = time.time()
    for _ in range(concurrency):
        resp = client.get("/api/v1/changes", headers=headers)
        assert resp.status_code == 200
    duration = time.time() - start_time
    print(f"✅ Endpoint GET /api/v1/changes: {concurrency} requests completed in {duration:.3f}s ({(concurrency/duration):.1f} req/s)")

    # 3. Submit Changes benchmark
    start_time = time.time()
    for i in range(10):
        payload = {
            "title": f"Load Benchmark Change #{i}",
            "description": "Benchmark load testing migration payload",
        }
        resp = client.post("/api/v1/changes", json=payload, headers=headers)
        assert resp.status_code == 201
    duration = time.time() - start_time
    print(f"✅ Endpoint POST /api/v1/changes: 10 mutation requests completed in {duration:.3f}s ({(10/duration):.1f} req/s)")

    print(f"==================================================\n")


if __name__ == "__main__":
    run_benchmark(50)
