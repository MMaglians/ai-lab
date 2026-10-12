"""Confronto zero-shot e few-shot su una classificazione a etichette fisse."""
from llm_client import MODEL, get_client, with_retry

client = get_client()
LABELS = {"bug", "richiesta_funzione", "domanda", "altro"}

messaggi = [
    "L'app si chiude quando premo salva",
    "Sarebbe bello avere la modalità scura",
    "Come esporto i dati in CSV?",
    "Ottimo lavoro ragazzi!",
    "Il pulsante login non fa niente su Firefox",
    "Potete aggiungere l'export in PDF?",
]

#zero: fornisco solo l'istruzione del compito
#few: aggiungo al prompt esempi

ZERO = "Classifica il messaggio in una categoria: bug, richiesta_funzione, domanda, altro.\nMessaggio: {m}"
FEW = """Classifica il messaggio. Rispondi SOLO con l'etichetta.
Messaggio: Non riesco a caricare le foto -> bug
Messaggio: Aggiungete il calendario condiviso -> richiesta_funzione
Messaggio: Dove trovo le impostazioni? -> domanda
Messaggio: {m} ->"""


def run(template: str) -> int:
    valide = 0
    for m in messaggi:
        out = with_retry(lambda: client.interactions.create(
            model=MODEL, input=template.format(m=m),
            generation_config={"temperature": 0.0}, store=False,
        )).output_text.strip()
        ok = out in LABELS
        valide += ok
        print(f"{'OK ' if ok else 'NO '} {out!r:40} <- {m}")
    return valide


#test di conformità del formato
#NOTA: il test non misura la correttezza.
#Nell'output potreste vedere che il modello ha classificato correttamente, 
#ma il formato è sbagliato, pertanto avremo NO
for nome, t in (("zero-shot", ZERO), ("few-shot", FEW)):
    print(f"\n== {nome} ==")
    print(f"Risposte nel formato esatto: {run(t)}/{len(messaggi)}")