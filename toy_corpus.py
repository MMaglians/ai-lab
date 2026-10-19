"""Mini corpus di prova (testi originali) e domande con la risposta attesa."""

DOCS = [
    {"id": "volley-set", "title": "Pallavolo: punteggio",
     "text": "Un set di pallavolo si vince arrivando a 25 punti con almeno due punti di vantaggio. "
             "Il quinto set, quando serve, si gioca a 15 punti."},
    {"id": "volley-rotazione", "title": "Pallavolo: rotazione",
     "text": "Quando una squadra conquista il servizio, i sei giocatori ruotano di una posizione "
             "in senso orario. Chi arriva in posizione di battuta serve per la propria squadra."},
    {"id": "volley-tocchi", "title": "Pallavolo: tocchi",
     "text": "Ogni squadra ha al massimo tre tocchi per rimandare la palla nel campo avversario. "
             "Lo stesso giocatore non puo' toccare la palla due volte di seguito."},
    {"id": "volley-libero", "title": "Pallavolo: libero",
     "text": "Il libero indossa una maglia di colore diverso dai compagni e gioca solo come "
             "difensore, in seconda linea. Non puo' attaccare la palla sopra il bordo della rete."},
    {"id": "chitarra-accordatura", "title": "Chitarra: accordatura",
     "text": "L'accordatura standard della chitarra a sei corde, dalla piu' grave alla piu' acuta, "
             "e' Mi, La, Re, Sol, Si, Mi. Si accorda con un accordatore elettronico o a orecchio."},
    {"id": "chitarra-barre", "title": "Chitarra: barre'",
     "text": "Nel barre' l'indice preme tutte le corde sullo stesso tasto, trasformando una forma "
             "di accordo aperto in un accordo mobile che si puo' spostare lungo il manico."},
    {"id": "chitarra-capotasto", "title": "Chitarra: capotasto",
     "text": "Il capotasto si applica su un tasto e alza l'intonazione di tutte le corde di un "
             "semitono per ogni tasto, permettendo di cambiare tonalita' senza cambiare le forme."},
    {"id": "chitarra-pentatonica", "title": "Chitarra: pentatonica",
     "text": "La scala pentatonica minore ha cinque note per ottava ed e' la base di moltissimi "
             "assoli di blues e rock, perche' le sue posizioni sul manico sono facili da memorizzare."},
    {"id": "giapp-kana", "title": "Giapponese: kana",
     "text": "Hiragana e katakana sono due sillabari, ciascuno con 46 caratteri di base. "
             "L'hiragana serve per le parole giapponesi e la grammatica, il katakana per i prestiti."},
    {"id": "giapp-particelle", "title": "Giapponese: particelle",
     "text": "La particella wa indica il tema della frase, ga il soggetto grammaticale e o "
             "l'oggetto diretto del verbo. Le particelle seguono sempre la parola a cui si riferiscono."},
    {"id": "giapp-kanji", "title": "Giapponese: kanji",
     "text": "Quasi ogni kanji ha due tipi di lettura: la lettura on, di origine cinese, e la "
             "lettura kun, giapponese. Quale usare dipende dalla parola in cui il kanji compare."},
    {"id": "giapp-verbi", "title": "Giapponese: verbi",
     "text": "Nella forma del dizionario i verbi giapponesi finiscono in u. I verbi in ru si "
             "dividono in due gruppi, e questo gruppo determina come si coniugano."},
]

# (domanda, id del documento che contiene la risposta)
QUERIES = [
    ("A quanti punti finisce un set?", "volley-set"),
    ("Come si dispongono i giocatori dopo aver preso il servizio?", "volley-rotazione"),
    ("Quante volte si puo' toccare la palla prima di mandarla di la'?", "volley-tocchi"),
    ("Chi e' il giocatore con la maglia diversa che difende soltanto?", "volley-libero"),
    ("How many strings does a guitar have and how are they tuned?", "chitarra-accordatura"),
    ("Come faccio a suonare un accordo di Fa con tutte le corde bloccate dall'indice?", "chitarra-barre"),
    ("Come alzo la tonalita' di un brano senza imparare nuovi accordi?", "chitarra-capotasto"),
    ("Quale scala conviene per iniziare a improvvisare un assolo blues?", "chitarra-pentatonica"),
    ("Quanti caratteri ha l'alfabeto per scrivere le parole straniere in giapponese?", "giapp-kana"),
    ("Che differenza c'e' tra ga e wa?", "giapp-particelle"),
    ("Perche' lo stesso ideogramma si legge in modi diversi?", "giapp-kanji"),
    ("Come si coniuga un verbo che termina in ru?", "giapp-verbi"),
]