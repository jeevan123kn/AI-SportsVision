import os
from sqlalchemy import create_engine, Column, String, Integer, Float, Text, DateTime, ForeignKey, JSON, text
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
from datetime import datetime

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./sportsvision.db")
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def ensure_schema():
    with engine.begin() as conn:
        player_columns = [row[1] for row in conn.execute(text("PRAGMA table_info(players)"))]
        if 'gender' not in player_columns:
            conn.execute(text("ALTER TABLE players ADD COLUMN gender VARCHAR"))
        if 'preferred_activity' not in player_columns:
            conn.execute(text("ALTER TABLE players ADD COLUMN preferred_activity VARCHAR"))
        if 'training_goals' not in player_columns:
            conn.execute(text("ALTER TABLE players ADD COLUMN training_goals TEXT"))
        if 'previous_performance' not in player_columns:
            conn.execute(text("ALTER TABLE players ADD COLUMN previous_performance FLOAT DEFAULT 0.0"))

        session_columns = [row[1] for row in conn.execute(text("PRAGMA table_info(sessions)"))]
        for column_name, column_sql in {
            'weaknesses': 'JSON',
            'repeated_mistakes': 'JSON',
            'recommendations': 'JSON',
            'prediction_data': 'JSON',
        }.items():
            if column_name not in session_columns:
                conn.execute(text(f"ALTER TABLE sessions ADD COLUMN {column_name} {column_sql}"))


def init_db():
    Base.metadata.create_all(bind=engine)
    ensure_schema()


class Player(Base):
    __tablename__ = "players"
    id = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=False)
    age = Column(Integer, nullable=True)
    gender = Column(String, nullable=True)
    sport = Column(String, nullable=False)
    role = Column(String, nullable=True)
    experience_level = Column(String, nullable=True)
    preferred_activity = Column(String, nullable=True)
    training_goals = Column(String, nullable=True)
    previous_performance = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)
    sessions = relationship("Session", back_populates="player")


class Session(Base):
    __tablename__ = "sessions"
    id = Column(String, primary_key=True, index=True)
    player_id = Column(String, ForeignKey("players.id"), nullable=False)
    date = Column(DateTime, default=datetime.utcnow)
    sport = Column(String, nullable=False)
    activity = Column(String, nullable=False)
    video_reference = Column(String, nullable=True)
    overall_score = Column(Float, default=0.0)
    technique_score = Column(Float, default=0.0)
    balance_score = Column(Float, default=0.0)
    movement_score = Column(Float, default=0.0)
    consistency_score = Column(Float, default=0.0)
    stability_score = Column(Float, default=0.0)
    weaknesses = Column(JSON, default=list)
    repeated_mistakes = Column(JSON, default=list)
    recommendations = Column(JSON, default=list)
    prediction_data = Column(JSON, default=dict)
    player = relationship("Player", back_populates="sessions")


class PerformanceMetric(Base):
    __tablename__ = "performance_metrics"
    id = Column(String, primary_key=True, index=True)
    session_id = Column(String, nullable=False)
    metric_name = Column(String, nullable=False)
    metric_value = Column(Float, default=0.0)
    metric_type = Column(String, nullable=True)


class Weakness(Base):
    __tablename__ = "weaknesses"
    id = Column(String, primary_key=True, index=True)
    session_id = Column(String, nullable=False)
    feature = Column(String, nullable=False)
    issue = Column(String, nullable=False)
    severity = Column(String, nullable=False)
    evidence = Column(String, nullable=True)
    suggested_improvement = Column(String, nullable=True)


class Recommendation(Base):
    __tablename__ = "recommendations"
    id = Column(String, primary_key=True, index=True)
    session_id = Column(String, nullable=False)
    title = Column(String, nullable=False)
    description = Column(String, nullable=False)
    reason = Column(String, nullable=True)


class PredictionRecord(Base):
    __tablename__ = "predictions"
    id = Column(String, primary_key=True, index=True)
    player_id = Column(String, nullable=False)
    current_performance = Column(Float, default=0.0)
    previous_performance = Column(Float, default=0.0)
    trend = Column(Float, default=0.0)
    predicted_future_performance = Column(Float, default=0.0)
    confidence = Column(Float, default=0.0)
    notes = Column(Text, nullable=True)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
