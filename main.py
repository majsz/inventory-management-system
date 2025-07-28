# -*- coding: utf-8 -*-
"""

Inventory Management System
A Python application for managing inventory with Firebird database integration.
Features: User authentication, product management, multi-format reporting.

"""

import fdb
import pyperclip # Schowek
from openpyxl import Workbook # Excel
from datetime import date

# Parametry polaczenia

# Database configuration - update these values for your environment
host = 'localhost'
database = 'path/to/your/database.fdb'  
dbUser = 'user'
dbPassword = 'password'  


def fetchDatabase(host, database, dbUser, dbPassword):

    try:

        con = fdb.connect(host=host, database=database, user=dbUser, password=dbPassword, charset='WIN1250')

        cur = con.cursor()
        
        userLogIn(cur, con)
        

    except fdb.fbcore.DatabaseError as e:

        print(f"Blad polaczenia z baza danych: {e}")

    finally:

        if 'con' in locals() and con:

            con.close()


def userLogIn(cur, con):
    while True:
        print("\nLOGOWANIE (\"x\" kończy program)")
        login = input("Login: ").strip()
        if login.lower() == "x":
            return

        password = input("Hasło: ").strip()

        try:
            cur.execute("SELECT id, imie, nazwisko FROM uzytkownicy WHERE login = ? AND haslo = ?", (login, password))
            user = cur.fetchone()
            if user:
                print(f"Zalogowano jako: {user[1]} {user[2]}")
                menu(cur, user[0], con)
                break
            else:
                print("Błędny login lub hasło.\n")
        except fdb.DatabaseError as e:
            print(f"Błąd bazy danych podczas logowania: {e}")


    
def menu(cur, userId, con):
    c = 0
    while c != 4:
        print("\nMENU")
        print("Wybierz czynność:")
        print("1 - Dodanie towaru")
        print("2 - Podsumowanie")
        print("3 - Wylogowanie")
        print("x - Zakończ program")
        c = input("Wybrano: ")
        while c not in ("1","2", "3", "x"):
            print("Niepoprawne dane")
            c = input("Wybrano: ")
        if c =="x":
            return
        c = int(c)
        if c == 1:
            addArticle(cur, userId, con)
        elif c == 2:
            summarize(cur, userId)
        elif c == 3: 
            print("Nastąpiło wylogowanie.")
            userLogIn(cur, con)
            return
        

def addArticle(cur, userId, con):
    print("DODAWANIE PRODUKTU")
    try:
        
        code = ""
        while code != "x":
            code = input("Podaj kod produktu: ")
            while not (code.isnumeric() and len(code) in (8, 13)):
                if code == "x":
                    return
                print("Niepoprawny kod EAN")
                code = input("Kod: ")
            if code == "x":
                return
            # jesli ean nie ma 13 znakow uzupelnij zerami z lewej strony ? ean -> varchar?
            
            code = int(code)
            cur.execute("SELECT id FROM produkty WHERE produkty.kod = ?", (code,))
            
            productId = cur.fetchone()
            if not productId:
                print("Brak produktu w bazie")
                continue
            productId = productId[0]
            
            quantity = input("Ilość: ")
            while not quantity.isnumeric() and quantity != "":
                if quantity == "x":
                    continue
                print("Niepoprawne dane")
                quantity = input("Ilość: ")
            if quantity == "x":
                continue
            elif quantity == "":
                quantity = 1
            else:
                quantity = int(quantity)
            
            tekst = input("Wpisz uwagi (max 150 znaków): ")

            if len(tekst) > 150:
                tekst = tekst[:147] + "..."
                print("Twój tekst został skrócony do 150 znaków:")
            if tekst == "":
                tekst = None
            
            cur.execute("INSERT into inwentaryzacja (produkt, ilosc, uzytkownik, uwagi) VALUES (?,?,?,?)", (productId, quantity, userId, tekst))

            con.commit()
            code = input("Aby zakończyć dodawanie produktów kliknij \"x\"\n")
    except fdb.DatabaseError as e:
        print(f"Błąd bazy danych: {e}")
    
def summarize(cur, userId):
    print("Wybierz rodzaj podsumowania:")
    print("x - Powrót")
    print("1 - Szczegółowe")
    print("2 - Krótkie")
    c = input("Wybrano: ")
    while(c not in ("x", "1", "2")):
        print("Niepoprawne dane")
        c = input("Wybrano: ")
    if c == "x":
            return    
    c = int(c)
    query = ""
    if c == 1:
        query = """SELECT inwentaryzacja.id, produkty.kod, kategorie.nazwa AS kategoria,
        inwentaryzacja.ilosc, firmy.nazwa as firma, inwentaryzacja.data, uzytkownicy.imie || ' ' || uzytkownicy.nazwisko AS uzytkownik, inwentaryzacja.uwagi
        FROM inwentaryzacja
        LEFT JOIN produkty ON inwentaryzacja.produkt = produkty.id
        LEFT JOIN kategorie ON produkty.kategoria = kategorie.id
        LEFT JOIN firmy ON produkty.firma = firmy.id
        LEFT JOIN uzytkownicy ON inwentaryzacja.uzytkownik = uzytkownicy.id"""
    else:
        query = """SELECT produkty.kod, kategorie.nazwa AS kategoria, SUM(inwentaryzacja.ilosc) AS suma_ilosci
        FROM inwentaryzacja
        LEFT JOIN produkty ON inwentaryzacja.produkt = produkty.id
        LEFT JOIN kategorie ON produkty.kategoria = kategorie.id
        GROUP BY produkty.kod, kategorie.nazwa;"""
    
    print("Wybierz sposób zapisu danych")
    
    print("x - Powrót")
    print("1 - Wklej do schowka")
    print("2 - Plik Excel")
    print("3 - Plik TXT")

    c = input("Wybrano: ")
    while(c not in ("x", "1", "2", "3")):
        print("Niepoprawne dane")
        c = input("Wybrano: ")
    if c == "x":
            return    
    c = int(c)
    
    getData(cur, query, c, userId)

def getValidFilename():
    forbidden_chars = '<>:"/\\|?*'
    while True:
        filename = input("Podaj nazwę pliku (np. plik): ").strip()
        if filename and not any(char in filename for char in forbidden_chars):
            return filename
        print("Nieprawidłowa nazwa pliku! Unikaj znaków: < > : \" / \\ | ? *")


def getData(cur, query, saveType, userLogIn):
    if saveType != 1:
        outputFile = getValidFilename()
    
    cur.execute("select min(data) from inwentaryzacja")
    minDate = cur.fetchone()[0]

    cur.execute("select max(data) from inwentaryzacja")
    maxDate = cur.fetchone()[0]

    cur.execute("select uzytkownicy.imie || ' ' || uzytkownicy.nazwisko AS uzytkownik from inwentaryzacja LEFT JOIN uzytkownicy ON inwentaryzacja.uzytkownik = uzytkownicy.id")
    user = cur.fetchone()[0]

    naglowek = f"INWENTARYZACJA \n{minDate.strftime('%Y-%m-%d')} - {maxDate.strftime('%Y-%m-%d')} \nWykonana przez {user}, dnia {date.today()}"
    print(naglowek)
    
    cur.execute(query)
    columns = [desc[0] for desc in cur.description]
    rows = cur.fetchall()
    
    tsv = naglowek + "\n\n" + "\t".join(columns) + "\n"
    
    for row in rows:
        row_str = [str(val) if val is not None else "" for val in row]
        line = "\t".join(row_str)
        tsv += line + "\n"
        
        for col, val in zip(columns, row):
            print(f"{col} = {val}")
        print() 
    
    if saveType == 1:  
        pyperclip.copy(tsv)
        print("Skopiowano dane do schowka!")
        
    elif saveType == 2:
        makeExcelFile(outputFile, naglowek, columns, rows)
        
    elif saveType == 3:
        makeTxtFile(outputFile, naglowek, columns, rows)
        
 
def makeTxtFile(outputFile, naglowek, columns, rows):
    outputFile = outputFile + ".txt"
    try:
        with open(outputFile, 'w', encoding='utf-8') as f:
            f.write(f"{naglowek}\n\n")
            
            for row in rows:
                for col, val in zip(columns, row):
                    f.write(f"{col} = {val}\n")
                f.write("\n") 
        print(f"Dane zapisane w pliku TXT: {outputFile}")
    except IOError as e:
        print(f"Błąd zapisywania pliku: {e}")
        

def makeExcelFile(outputFile, naglowek, columns, rows):
    outputFile = outputFile + ".xlsx"
    try:
        wb = Workbook()
        ws = wb.active
        ws.title = "Inwentaryzacja"
        
        ws.append([naglowek])
        ws.append([])  
        ws.append(columns)
        
        for row in rows:
            ws.append(list(row))
        
        wb.save(outputFile)
        print(f"Dane zapisane w pliku Excel: {outputFile}")
    except Exception as e:
        print(f"Błąd tworzenia pliku: {e}")


fetchDatabase(host, database, dbUser, dbPassword)
