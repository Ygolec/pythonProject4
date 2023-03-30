import random
from typing import List
from pydantic import BaseModel
from fastapi import FastAPI, HTTPException


class Participant(BaseModel):
    id: int | None
    name: str
    wish: str
    recipient: 'Participant' = None


class Group(BaseModel):
    id: int | None
    name: str
    description: str | None
    participants: List[Participant] = []


app = FastAPI()

groups = []
participants = []


@app.get('/groups', response_model=List[Group])
async def get_groups():
    groups_without_participants = [group.copy(update={"participants": []}) for group in groups]
    return groups_without_participants


@app.post("/group", response_model=int)
async def create_group(group: Group):
    max_id = max([g.id for g in groups]) if groups else 0
    group.id = max_id + 1
    group.participants = []
    groups.append(group)
    return group.id


@app.get('/group/{id}', response_model=Group)
async def get_group(id: int):
    for group in groups:
        if group.id == id:
            return group
        raise HTTPException(status_code=404, detail="Группа не найдена")


@app.put('/group/{id}', response_model=Group)
async def put_group(id: int, group: Group):
    for g in groups:
        if g.id == id:
            if group.name:
                g.name = group.name
            if group.description is not None:
                g.description = group.description
            return g
        raise HTTPException(status_code=404, detail="Группа не найдена")


@app.delete("/group/{id}")
async def delete_group(id: int):
    for group in groups:
        if group.id == id:
            groups.remove(group)
            return
        raise HTTPException(status_code=404, detail="Группа не найдена")


@app.post("/group/{id}/participant", response_model=int)
async def add_participant_in_group(id: int, participant: Participant):
    for group in groups:
        if group.id == id:
            max_id = max([g.id for g in participants]) if participants else 0
            participant.id = max_id + 1
            group.participants.append(participant)
            participants.append(participant)
            return participant.id
        raise HTTPException(status_code=404, detail="Группа не найдена")


@app.delete("/group/{groupId}/participant/{participantId}")
async def delete_participant_in_group(groupID: int, participantID: int):
    for group in groups:
        if group.id == groupID:
            for participant in group.participants:
                if participant.id == participantID:
                    group.participants.remove(participant)
                    participants.remove(participant)
                    return ({"message": "Участник удален"})
            raise HTTPException(status_code=404, detail="Участник не найден")
        raise HTTPException(status_code=404, detail="Группа не найдена")


@app.post("/group/{id}/toss", response_model=List[Participant])
async def toss(id: int):
    for group in groups:
        if group.id == id:
            if len(group.participants) < 3:
                raise HTTPException(status_code=409, detail="Недостаточно участников для проведенья жеребьевки")
            recipients = []
            for participant in group.participants:
                potential_recipients = [p for p in group.participants if
                                        p.id != participant.id and p.id not in recipients]
                if len(potential_recipients) == 0:
                    raise HTTPException(status_code=409, detail="Недостаточно участников для проведенья жеребьевки")
                recipient = random.choice(potential_recipients)
                participant.recipient = {"id": recipient.id, "name": recipient.name, "wish": recipient.wish}
                recipients.append(recipient.id)
            return group.participants
        raise HTTPException(status_code=409, detail="Группа не найдена")


@app.get("/group/{groupId}/participant/{participantId}/recipient")
async def get_recipient(groupID: int, participantId: int):
    for group in groups:
        if group.id == groupID:
            for participant in group.participants:
                if participant.id == participantId:
                    if participant.recipient is None:
                        raise HTTPException(status_code=404, detail="Получатель не найден")
                    return participant.recipient
                raise HTTPException(status_code=404, detail="Участник не найден")
            raise HTTPException(status_code=404, detail="Группа не найдена")
