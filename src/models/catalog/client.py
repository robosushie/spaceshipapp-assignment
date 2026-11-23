from sqlmodel import Field, SQLModel


class Client(SQLModel, table=True):
    __tablename__ = "clients"

    client_id: str = Field(primary_key=True, max_length=32)
