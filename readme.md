## Instalace Windows

- Nainstalujte si poslední verzi *Pythonu*: https://www.python.org/downloads/
  - Nechte instalátor přidat *Python* do *PATH*
- Nainstalujte si pythoní request knihovnu: *cmd.exe* &rightarrow; `pip3 install request`
- Spusťte program
  - Mělo by stačit poklepání na `__main__.py`
  - Případně *cmd.exe* &rightarrow; `cd C:\\cesta\\k\\teto\\slozce\\bitmex\\` &rightarrow; `python3 __main__.py`

## Instalace macOS

- Nainstalujte si poslední verzi *Pythonu*: https://www.python.org/downloads/
- Nainstalujte si pythoní request knihovnu: *macOS terminál* &rightarrow; `pip3 install request`
- Spusťte program: *macOS terminál* &rightarrow; `cd /cesta/k/teto/slozce/bitmex/` &rightarrow; `python3 __main__.py`

## Po instalaci

- Než něco začnete dělat, *Account Management &rightarrow; New Account*
- Pokud program zamrzne na *Open Positions*, pomocí *CTRL+C* mu v terminálu pošlete *SIGINT*. Mělo by to přerušit čekání na odpověd serveru.
- Pokud nastane chyba při vyřizování *orderu* pro více účtů, vypíše se pro každý účet, který postihla. Takhle můžete určit, pro které účty byl *request* úspěšný.
- Bacha na chybné *requesty*. Když jich *BitMEX* dostane moc, může vaší ip adresu blacklistnout na hodinu nebo případně i na týden.
- Detaily k vašim účtům se ukládají do souboru `accounts` v této složce (při prvním spuštění se vytvoří). Git ho ignoruje, ale i tak bych si na něj dával pozor.
- Pokud se nebudou chtít načíst *Positions, Orders, Stop Orders* ani *Order History*, zkontrolujte, jestli jsou všechny klíče, co máte v *Account Managementu*, validní. Případně zkuste jednotlivé účty smazat a znovu je do programu přidat.

## Nový frontend

- Chcete-li program spustit s vyvíjeným alternativním GUI, zadejte mu v příkazové řádce argument `newfrontend`
```sh
python3 __main__.py newfrontend
```
- Doporučený způsob vypínání programu je přes GUI. Používání POSIX signálů může vést k nedokončeným requestům.
