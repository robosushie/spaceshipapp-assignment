from sqlmodel import Field, SQLModel


class Warehouse(SQLModel, table=True):
    __tablename__ = "warehouses"

    code: str = Field(primary_key=True, max_length=32)
    region: str = Field(max_length=16, index=True)
    origin_city: str = Field(max_length=128)
