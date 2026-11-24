from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

import main


BOOK_PAYLOAD = {
    "title": "The Fellowship of the Ring",
    "author": "J.R.R. Tolkien",
    "isbn": "9780618640157",
    "published_date": "1954-07-29",
    "price": 19.99,
}


@pytest.fixture
def client(monkeypatch: pytest.MonkeyPatch) -> Iterator[TestClient]:
    monkeypatch.setattr(main, "books", main.books.copy())
    with TestClient(main.app) as test_client:
        yield test_client


def test_list_books_returns_seed_data(client: TestClient) -> None:
    response = client.get("/books")

    assert response.status_code == 200
    assert [book["id"] for book in response.json()] == [1, 2]


def test_get_missing_book_returns_404(client: TestClient) -> None:
    response = client.get("/books/999")

    assert response.status_code == 404


def test_create_book_assigns_id(client: TestClient) -> None:
    response = client.post("/books", json=BOOK_PAYLOAD)

    assert response.status_code == 201
    assert response.json()["id"] == 3
    assert response.json()["price"] == 19.99


def test_create_book_rejects_duplicate_isbn(client: TestClient) -> None:
    response = client.post(
        "/books",
        json={**BOOK_PAYLOAD, "isbn": "9780547928227"},
    )

    assert response.status_code == 409


def test_create_book_rejects_invalid_price(client: TestClient) -> None:
    response = client.post(
        "/books",
        json={**BOOK_PAYLOAD, "price": -1},
    )

    assert response.status_code == 422


def test_update_book_replaces_book(client: TestClient) -> None:
    response = client.put(
        "/books/1",
        json={**BOOK_PAYLOAD, "title": "Updated title"},
    )

    assert response.status_code == 200
    assert response.json()["title"] == "Updated title"


def test_delete_book_removes_book(client: TestClient) -> None:
    response = client.delete("/books/1")

    assert response.status_code == 204
    assert client.get("/books/1").status_code == 404
