import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from database.database import Player, get_db

router = APIRouter(prefix="/api", tags=["players"])


class PlayerCreate(BaseModel):
    name: str = Field(..., min_length=1)
    age: int | None = None
    gender: str | None = None
    sport: str = "Cricket"
    role: str | None = None
    experience_level: str | None = None
    preferred_activity: str | None = None
    training_goals: str | None = None
    previous_performance: float | None = None


class PlayerOut(BaseModel):
    id: str
    name: str
    age: int | None = None
    gender: str | None = None
    sport: str
    role: str | None = None
    experience_level: str | None = None
    preferred_activity: str | None = None
    training_goals: str | None = None
    previous_performance: float | None = None


@router.post("/players", response_model=PlayerOut)
def create_player(payload: PlayerCreate, db: Session = Depends(get_db)):
    player = Player(
        id=str(uuid.uuid4()),
        name=payload.name,
        age=payload.age,
        gender=payload.gender,
        sport=payload.sport,
        role=payload.role,
        experience_level=payload.experience_level,
        preferred_activity=payload.preferred_activity,
        training_goals=payload.training_goals,
        previous_performance=payload.previous_performance,
    )
    db.add(player)
    db.commit()
    db.refresh(player)
    return player


@router.get("/players", response_model=list[PlayerOut])
def list_players(db: Session = Depends(get_db)):
    players = db.query(Player).all()
    return players


@router.get("/players/{player_id}", response_model=PlayerOut)
def get_player(player_id: str, db: Session = Depends(get_db)):
    player = db.query(Player).filter(Player.id == player_id).first()
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")
    return player


@router.put("/players/{player_id}", response_model=PlayerOut)
def update_player(player_id: str, payload: PlayerCreate, db: Session = Depends(get_db)):
    player = db.query(Player).filter(Player.id == player_id).first()
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")

    player.name = payload.name
    player.age = payload.age
    player.gender = payload.gender
    player.sport = payload.sport
    player.role = payload.role
    player.experience_level = payload.experience_level
    player.preferred_activity = payload.preferred_activity
    player.training_goals = payload.training_goals
    player.previous_performance = payload.previous_performance

    db.commit()
    db.refresh(player)
    return player
