CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR UNIQUE,
    password VARCHAR NOT NULL
);

CREATE TABLE reviews (
    id SERIAL PRIMARY KEY,
    isbn VARCHAR NOT NULL,
    rating INTEGER CHECK (rating >= 1),
    text VARCHAR DEFAULT '',
    username VARCHAR NOT NULL,
    CHECK (rating <= 5)
);

CREATE TABLE books (
    id SERIAL PRIMARY KEY,
    title VARCHAR NOT NULL,
    author VARCHAR NOT NULL,
    year INTEGER NOT NULL,
    ISBN INTEGER NOT NULL
);