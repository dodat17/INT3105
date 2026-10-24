from uuid import UUID, uuid4

from app.domain.auth.model import Actor, require_admin
from app.domain.cinema.model import Room, Seat, generate_seats
from app.domain.errors import BusinessRuleViolation, NotFoundError, RoomNameAlreadyUsedError
from app.domain.ports import UnitOfWorkFactory


class RoomService:
    def __init__(self, uow_factory: UnitOfWorkFactory) -> None:
        self._uow_factory = uow_factory

    def list_rooms(self, actor: Actor) -> list[Room]:
        require_admin(actor)
        with self._uow_factory() as uow:
            return uow.rooms.list_all()

    def get_room(self, actor: Actor, room_id: UUID) -> tuple[Room, list[Seat]]:
        require_admin(actor)
        with self._uow_factory() as uow:
            room = uow.rooms.get(room_id)
            if room is None:
                raise NotFoundError
            return room, uow.rooms.seats(room_id)

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

    def update_room(
        self, actor: Actor, room_id: UUID, *, name: str, rows: int, cols: int, vip_rows: set[int]
    ) -> Room:
        require_admin(actor)
        room = Room(id=room_id, name=name.strip(), rows=rows, cols=cols)
        seats = generate_seats(room_id, rows, cols, vip_rows)
        with self._uow_factory() as uow:
            # Same lock as showtime creation, so no showtime can slip in during the change.
            if uow.rooms.lock(room_id) is None:
                raise NotFoundError
            # Showtime inventory and tickets point at the current seats.
            if uow.showtimes.exists_for_room(room_id):
                raise BusinessRuleViolation("Không thể sửa phòng đã có suất chiếu.")
            other = uow.rooms.get_by_name(room.name)
            if other is not None and other.id != room_id:
                raise RoomNameAlreadyUsedError
            uow.rooms.update(room, seats)
            uow.commit()
        return room
