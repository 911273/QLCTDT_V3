from typing import Optional


class CourseCRUDService:
    """Thin use-case layer for course CRUD and related section data."""

    def __init__(self, hp_repo):
        self.hp_repo = hp_repo

    def list_courses(self) -> list[dict]:
        return self.hp_repo.get_all()

    def get_course(self, hp_id: int) -> Optional[dict]:
        return self.hp_repo.get_by_id(hp_id)

    def create_course(self, data: dict) -> int:
        return self.hp_repo.create(data)

    def update_course(self, hp_id: int, data: dict) -> None:
        self.hp_repo.update(hp_id, data)

    def delete_course(self, hp_id: int) -> None:
        self.hp_repo.delete(hp_id)

    def clone_course(self, hp_id: int) -> Optional[int]:
        return self.hp_repo.clone(hp_id)

