Tema #3 AI
Ciupitu Andrei, 341C4

Detalii de implementare ------------------------------------------------------

Pentru afisarea simularii am folosit pygame.

Clasa World reprezinta mediul simularii care realizeaza comenzile alese de
catre blipsi.

Blipsii cunosc doar parametrii specificati in tema. La fiecare tura, acestia
primesc de la mediu directiile in care se pot deplasa, directia catre apa si
directia care conduce catre cei mai multi blipsi. Restul parametrilor sunt
implementati ca atribute ale clasei Blip.

Algoritmul folosit de catre blipsi:

Daca au suficiente resurse, se misca aleator sau exploreaza harta catre Vest
pentru a putea gasi lacul.
Daca au nevoie de apa, se duc fie catre lac, daca se afla in SEE_RANGE,
fie catre ceilalti blipsi.
Daca au nevoie de mancare se duc catre Est pana cand ajung la padure.
In padure fie isi iau suficienta hrana cat sa se poata inmulti, fie
exploreaza aleator prin padure pentru a nu epuiza resursele dintr-o
singura casuta.

Observatii parametrii --------------------------------------------------------

In urma testarii am observat ca modificarea parametrilor ce tin de inmultirea
blipsilor conduce la o instabilitate a populatiei. Astfel:
    - Crescand BUDDING_PROB sau scazand BUDDING_MIN_RES populatia creste
    necontrolat.
    - Crescand BUDDING_FACTOR populatia creste mai greu datorita consumului
    suplimentar de resurse.
    - Crescand BUDDING_TIME se vor crea blipsi noi mult mai rar, deci media
    populatiei va scadea.
    - Scazand MIN_BUDDING_AGE populatia creste constant

Modificarea INIT_POP sau AGE_VAR nu produce diferente majore.
Modificarea MAX_LIFE conduce la modificarea mediei populatiei.

Cresterea FOOD_BUILD si FOOD_SIZE conduce la cresterea necontrolata a
populatiei, deoarece mai multi blipsii se pot mentine deasupra
BUDDING_MIN_RES.

Scazand MAX_RES media populatiei scade deoarece, blipsii nu mai au suficiente
resurse pentru a se inmultii.

Crescand costurile pentru miscare, populatia scade, in special la modificarea
costurilor de mancare, deoarece aceasta este o resursa limitata.

Scaderea SEE_RANGE duce la scaderea populatiei deoarece este nevoie de mai
multe ture de explorare pentru a putea detecta lacul.

Perechi de parametrii --------------------------------------------------------

(BUDDING_PROB, BUDDING_TIME) -> Cresterea BUDDING_TIME compenseaza pentru
cresterea BUDDING_PROB deoarece blipsii stau mai multe runde inmuguriti.

(FOOD_BUILD, FOOD_SIZE) -> Cresterea FOOD_BUILD poate compensa pentru scaderea
FOOD_SIZE deoarece mancarea se regenereaza mult mai repede, deci blipsii vor
pierde mult mai putine resurse cautand mancare.

(POWER_TO_MOVE, VAPOUR_TO_MOVE) -> Scaderea ambilor parametrii duce la
cresterea constanta a populatiei. Scaderea POWER_TO_MOVE, dar cresterea
VAPOUR_TO_MOVE cu cateva unitati, conduce de asemenea la cresterea constanta
a populatiei, deoarece apa este o resursa nelimitata. In schimb, scaderea
VAPOUR_TO_MOVE, si cresterea POWER_TO_MOVE, produce fluctuatii ale
populatiei, deoarece populatia creste pana cand se epuizeaza mancarea si
apoi scade pana cand se regenereaza.

(MAX_RES, SEE_RANGE) -> Cresterea MAX_RES compenseaza scaderea SEE_RANGE
deoarece blipsii au mai multe resurse pentru a putea explora harta, astfel
populatia creste.

(BUDDING_PROB, BUDDING_MIN_RES) -> Se poate compensa scaderea unuia din cei
doi factori prin cresterea celuilalt.
