import enum


class UserRole(enum.StrEnum):
    user = "user"
    creator = "creator"
    moderator = "moderator"
    admin = "admin"
