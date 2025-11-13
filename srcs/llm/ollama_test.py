from ollama import generate

# Regular response
prompt = ("""
hodnocení žáka – Jan Novák
Jan během tohoto pololetí prokázal výrazný posun v mnoha oblastech. V hodinách se zpravidla chová soustředěně a udržuje si aktivní přístup k práci. Při samostatných úkolech dokáže uvažovat systematicky a hledat vlastní řešení, i když občas potřebuje více času na dokončení úkolu.
V matematice Jan projevuje dobré logické myšlení a nebojí se zkoušet různé postupy. U složitějších úloh je však potřeba, aby si důsledněji kontroloval výsledky a nevzdával se po prvním neúspěchu.
V českém jazyce pracuje pečlivě, má bohatou slovní zásobu a dobře formuluje své myšlenky. Písemný projev je čitelný a přehledný, i když by mohl více dbát na gramatickou správnost.
V přírodovědných předmětech se Jan zajímá o praktické ukázky a pokusy, které výrazně podporují jeho zapojení. V diskusi dokáže pokládat smysluplné otázky a přispívá k příjemné atmosféře ve třídě.
V kolektivu je přátelský, spolupracuje ochotně a slušně se vyjadřuje ke spolužákům. Dokáže nabídnout pomoc těm, kteří si s úkolem neví rady, a při skupinové práci na sebe často bere roli organizátora.
Pokud bude Jan i nadále udržovat svou motivaci, pravidelně se připravovat a nebát se požádat o radu, má velký potenciál dál se zlepšovat a dosahovat velmi dobrých výsledků.
========================================================
                 HODNOCENÍ ŽÁKA Tereza Novotná – 1. POLOLETÍ
========================================================
Předmět                 | Známka | Slovní hodnocení
--------------------------------------------------------
Český jazyk             | 2      | Solidní práce, mírné chyby v pravopisu.
Matematika              | 1      | Výborné logické myšlení, precizní postupy.
Anglický jazyk          | 2      | Dobrá komunikace, zlepšit slovní zásobu.
Informatika             | 1      | Nadprůměrné dovednosti, samostatný přístup.
Dějepis                 | 3      | Základní znalosti, chybí hlubší souvislosti.
Zeměpis                 | 2      | Spolehlivý výkon, dobrá orientace v mapách.
Fyzika                  | 3      | Průměrné porozumění, slabší v aplikaci vzorců.
Chemie                  | 2      | Snaživý, dobře zvládá laboratorní úkoly.
Biologie                | 1      | Velmi dobré znalosti a aktivita v hodinách.
Tělesná výchova         | 1      | Vynikající fyzická kondice a přístup.
Výtvarná výchova        | 2      | Kreativní, občas nesoustředěný.
Hudební výchova         | 3      | Základní rytmické schopnosti, slabší zpěv.
--------------------------------------------------------
Chování                 | 1      | Vzorové, aktivní zapojení a respekt k ostatním.
Docházka                | 96 %   | Minimum omluvených absencí.
========================================================
Celkové shrnutí: Žák dosahuje velmi dobrých výsledků, vyniká zejména
v technických a přírodovědných předmětech. Rezervy má v humanitních oborech,
ale projevuje snahu se zlepšovat.
""")

system = "Jste asistent pro porovnávání studentů. Vaším úkolem je analyzovat hodnocení dvou studentů a připravit stručné, objektivní porovnání jejich výkonů, silných a slabých stránek, chování a účasti. Vyhodnoťte jejich studijní výsledky předmět po předmětu, upozorněte na oblasti, kde jeden student vyniká oproti druhému, a shrňte celkový potenciál každého studenta. Odpověď formulujte jasně, srozumitelně a neutrálně, bez přílišných detailů, aby byla vhodná pro pedagogické účely."

response = generate('llama3.1:8b', prompt, system=system)
print(response['response'])