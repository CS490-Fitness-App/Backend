# Marks the models/ directory as a Python package.
# Each file in this package defines SQLAlchemy ORM classes that mirror the existing MySQL schema.

from core.database import Base
# Clear metadata to avoid duplicate table definitions when reloading modules
Base.metadata.clear()

from .user         import CoachStatus, SessionFormat, User, Client, Coach, Admin
from .coach        import coach_specialities, CoachCertification, CoachAvailability, ClientCoach
from .exercise     import exercise_muscles, ExerciseCategory, MuscleGroup, ExperienceLevel, Unit, Exercise
from .workout      import Workout, WorkoutPlan, WorkoutLog, SetResult, SavedWorkout, ScheduledWorkout
from .log          import GoalType, Goal, MoodType, DailySurvey, WeightLog, AuditLog
from .payment      import CardType, Card, CoachPaymentHistory
from .notification import Notification
from .review       import Review, Report
from .chat         import Chat
from .notebook     import Notebook
