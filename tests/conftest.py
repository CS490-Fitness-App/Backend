import pytest
from unittest.mock import MagicMock
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Import all models so Base.metadata knows about every table before create_all
import models.user        # noqa: F401
import models.exercise    # noqa: F401
import models.workout     # noqa: F401
import models.coach       # noqa: F401
import models.log         # noqa: F401
import models.chat        # noqa: F401
import models.notification  # noqa: F401
import models.payment     # noqa: F401
import models.review      # noqa: F401
import models.notebook    # noqa: F401

from core.database import Base, get_db
from dependencies.rbac import require_admin
from models.exercise import ExerciseCategory, ExperienceLevel, MuscleGroup
from main import app

_engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
)
_TestingSession = sessionmaker(bind=_engine)


@pytest.fixture(scope="session", autouse=True)
def _create_tables():
    Base.metadata.create_all(bind=_engine)
    yield
    Base.metadata.drop_all(bind=_engine)


@pytest.fixture
def db():
    session = _TestingSession()
    yield session
    session.rollback()
    session.close()


@pytest.fixture
def client(db):
    mock_admin = MagicMock()
    mock_admin.role = "admin"

    def _override_get_db():
        yield db

    app.dependency_overrides[get_db] = _override_get_db
    app.dependency_overrides[require_admin] = lambda: mock_admin

    with TestClient(app) as c:
        yield c

    app.dependency_overrides.clear()


@pytest.fixture
def seed_lookup(db):
    cat = ExerciseCategory(category_name="Strength")
    level = ExperienceLevel(experience_level_name="Beginner")
    muscle = MuscleGroup(muscle_group_name="Chest")
    db.add_all([cat, level, muscle])
    db.flush()
    return {
        "category_id": cat.category_id,
        "level_id": level.experience_level_id,
        "muscle_id": muscle.muscle_group_id,
    }
