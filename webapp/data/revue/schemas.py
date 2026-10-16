from ninja import Schema


class UserOut(Schema):
    id: int
    username: str


class ErrorOut(Schema):
    code: str
    detail: str
