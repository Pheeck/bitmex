## Instalace

- Nainstalujte si poslední verzi pythonu: https://www.python.org/downloads/
- Nainstalujte si pythoní request knihovnu: OSX terminál &rightarrow; `pip3 install request`
- Spusťte program: OSX terminál &rightarrow; `cd /cesta/k/teto/slozce/bitmex/` &rightarrow; `python3 __main__.py`

## Po instalaci

- Než něco začnete dělat, Account Management &rightarrow; New Account
- Pokud program zamrzne na Open Positions, pomocí CTRL+C mu v terminálu pošlete SIGINT. Mělo by to přerušit čekání na odpověd serveru.
- Pokud nastane chyba při vyřizování Orderu pro víc účtů, vypíše se pro každý účet, který postihla. Takhle můžete určit, pro které účty byl request úspěšný.
- Bacha na chybné requesty. Když jich BitMEX dostane moc, může vaší ip adresu blacklistnout na hodinu nebo případně i na týden.
