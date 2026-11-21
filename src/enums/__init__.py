from enum import StrEnum


class OrderStatus(StrEnum):
    delivered = "delivered"
    delayed = "delayed"
    in_transit = "in_transit"
    exception = "exception"
    canceled = "canceled"


class UserRole(StrEnum):
    analyst = "analyst"
    admin = "admin"
