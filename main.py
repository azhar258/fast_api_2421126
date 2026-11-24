from datetime import date
from decimal import Decimal

from fastapi import FastAPI, HTTPException, Path, Response, status
from pydantic import BaseModel, ConfigDict, Field, field_serializer


class BookInput(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "title": "The Hobbit",
                    "author": "Azhar Ansari",
                    "isbn": "9780547928227",
                    "published_date": "1937-09-21",
                    "price": 14.99,
                }
            ]
        }
    )

    title: str = Field(min_length=1)
    author: str = Field(min_length=1)
    isbn: str = Field(min_length=10, max_length=17)
    published_date: date
    price: Decimal = Field(gt=0, max_digits=8, decimal_places=2)

    @field_serializer("price", when_used="json", return_type=float)
    def serialize_price(self, price: Decimal) -> float:
        return float(price)


class Book(BookInput):
    id: int


app = FastAPI(title="Bookstore API", version="1.0.0")

books: dict[int, Book] = {
    1: Book(
        id=1,
        title="The Hobbit",
        author="J.R.R. Tolkien",
        isbn="9780547928227",
        published_date=date(1937, 9, 21),
        price=Decimal("14.99"),
    ),
    2: Book(
        id=2,
        title="Pride and Prejudice",
        author="Jane Austen",
        isbn="9780141439518",
        published_date=date(1813, 1, 28),
        price=Decimal("9.50"),
    ),
}


def ensure_unique_isbn(isbn: str, except_id: int | None = None) -> None:
    if any(book.isbn == isbn and book.id != except_id for book in books.values()):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A book with this ISBN already exists.",
        )


@app.get("/")
def read_root() -> dict[str, str]:
    return {"message": "Welcome to the Bookstore API"}


@app.get("/books", response_model=list[Book])
def list_books() -> list[Book]:
    return list(books.values())


@app.get("/books/{book_id}", response_model=Book)
def get_book(book_id: int = Path(gt=0)) -> Book:
    book = books.get(book_id)
    if book is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Book not found.",
        )
    return book


@app.post("/books", response_model=Book, status_code=status.HTTP_201_CREATED)
def create_book(book_input: BookInput) -> Book:
    ensure_unique_isbn(book_input.isbn)
    book_id = max(books, default=0) + 1
    book = Book(id=book_id, **book_input.model_dump())
    books[book_id] = book
    return book


@app.put("/books/{book_id}", response_model=Book)
def update_book(book_input: BookInput, book_id: int = Path(gt=0)) -> Book:
    if book_id not in books:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Book not found.",
        )
    ensure_unique_isbn(book_input.isbn, except_id=book_id)
    book = Book(id=book_id, **book_input.model_dump())
    books[book_id] = book
    return book


@app.delete("/books/{book_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_book(book_id: int = Path(gt=0)) -> Response:
    if books.pop(book_id, None) is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Book not found.",
        )
    return Response(status_code=status.HTTP_204_NO_CONTENT)
