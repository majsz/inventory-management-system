# Inventory Management System

Python-based inventory management application with Firebird database integration.

## Features
- User authentication and login system
- Product management (add, edit, remove)
- Multi-format reporting (Excel, TXT, clipboard)
- Database integration with SQL queries

## Technologies
- Python
- Firebird Database
- SQL
- Libraries: fdb, openpyxl, pyperclip

## Database Schema
Required tables:
- `inwentaryzacja`: produkt, ilosc, data, uzytkownik(id)
- `uzytkownicy`: imie, nazwisko, login, haslo
- `kategoria`: nazwa
- `produkt`: kod, kategoria(id), firma(id)
- `firmy`: nazwa
