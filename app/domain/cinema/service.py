from uuid import uuid4

from app.domain.auth.model import Actor, require_admin
from app.domain.cinema.model import Room, generate_seats
from app.domain.cinema.ports import CinemaUnitOfWorkFactory
from app.domain.errors import RoomNameAlreadyUsedError


class RoomService:
    def __init__(self, uow_factory: CinemaUnitOfWorkFactory) -> None:
        self._uow_factory = uow_factory

    def list_rooms(self, actor: Actor) -> list[Room]:
        require_admin(actor)
        with self._uow_factory() as uow:
            return uow.rooms.list_all()

    def create_room(
        self, actor: Actor, *, name: str, rows: int, cols: int, vip_rows: set[int]
    ) -> Room:
        require_admin(actor)
        room = Room(id=uuid4(), name=name.strip(), rows=rows, cols=cols)
        seats = generate_seats(room.id, rows, cols, vip_rows)
        # Room and all its seats are written in one transaction: never a room without seats.
        with self._uow_factory() as uow:
            if uow.rooms.get_by_name(room.name) is not None:
                raise RoomNameAlreadyUsedError
            uow.rooms.add(room, seats)
            uow.commit()
        return room
