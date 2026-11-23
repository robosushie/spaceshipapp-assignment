from sqlmodel import Field, SQLModel


class Carrier(SQLModel, table=True):
    __tablename__ = "carriers"

    name: str = Field(primary_key=True, max_length=64)
