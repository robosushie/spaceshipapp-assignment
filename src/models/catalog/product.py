from sqlmodel import Field, SQLModel


class Product(SQLModel, table=True):
    __tablename__ = "products"

    sku: str = Field(primary_key=True, max_length=64)
    category: str = Field(max_length=32, index=True)
