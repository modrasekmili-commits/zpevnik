import re
from config import chromaticka_rada

def transponuj_text(text, posun):
    if posun == 0: return text
    def nahrad(m):
        p = m.group(0); z = re.match(r"([CDEFGAH][#b]?)(.*)", p)
        if not z: return p
        try:
            # Oprava pro hledání v chromatické řadě (podpora B i A# podle toho, co máš v configu)
            idx = (chromaticka_rada.index(z.group(1)) + posun) % 12
            return chromaticka_rada[idx] + z.group(2)
        except: return p
    # Rozšířený regex pro transpozici (podpora mi, maj, atd.)
    return re.sub(r"\b[CDEFGAH][#b]?[a-z0-9/]*\b", nahrad, text)

def is_chord_line(line):
    clean = line.strip()
    if not clean: return False
    
    # Rozšířený regex pro detekci akordů (přidáno 'mi' pro český zápis)
    chords = re.findall(r"\b[CDEFGAH][#b]?(?:m|mi|dim|maj|sus|add|[0-9])*(?=\s|$)\b", line)
    if not chords: return False
    
    # Spočítáme slova, která zaručeně NEJSOU akordy (obsahují českou diakritiku nebo jsou dlouhá)
    # Tím zajistíme, že řádek s textem "Byl jsi můj" nebude označen jako akordy
    words = [w for w in clean.split() if len(re.sub(r'[^a-zA-Záéíóúýčďěňřšťůž]', '', w)) > 2]
    
    # Pokud jsme našli akordy a je jich víc nebo stejně jako ostatních slov, je to akordový řádek
    return len(chords) >= (len(words) - len(chords))

def najdi_vsechny_akordy_v_textu(text):
    """Vrátí množinu unikátních akordů nalezených v textu."""
    # I zde přidáno 'mi' pro správnou detekci v knihovně
    return set(re.findall(r"\b[CDEFGAH][#b]?(?:m|mi|dim|maj|sus|add|[0-9])*(?=\s|$)\b", text))

