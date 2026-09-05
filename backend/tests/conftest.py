"""Shared Pytest test fixtures."""

from typing import Generator
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.common.enums import UserRole
from app.core.database import Base, get_db
from app.core.security import hash_password
from app.main import app
from app.models.user import User


@pytest.fixture(scope="session")
def engine():
    """Create a persistent in-memory SQLite engine for the test session."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db(engine) -> Generator[Session, None, None]:
    """Provide a transactional database session per test with automatic rollback."""
    connection = engine.connect()
    transaction = connection.begin()
    TestingSessionLocal = sessionmaker(
        autocommit=False, autoflush=False, bind=connection
    )
    session = TestingSessionLocal()

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def client(db: Session) -> Generator[TestClient, None, None]:
    """Provide a TestClient with database session dependency overridden."""
    def _override_get_db():
        yield db

    app.dependency_overrides[get_db] = _override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def test_user(db: Session) -> User:
    """Create a standard active SALES_REP user."""
    user = User(
        name="Sales Representative",
        email="sales.rep@dealflow360.local",
        password_hash=hash_password("Password123!"),
        role=UserRole.SALES_REP,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def inactive_user(db: Session) -> User:
    """Create an inactive user."""
    user = User(
        name="Inactive Staff",
        email="inactive@dealflow360.local",
        password_hash=hash_password("Password123!"),
        role=UserRole.SALES_REP,
        is_active=False,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def admin_user(db: Session) -> User:
    """Create an active ADMIN user."""
    user = User(
        name="System Admin",
        email="admin@dealflow360.local",
        password_hash=hash_password("AdminSecure123!"),
        role=UserRole.ADMIN,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user
