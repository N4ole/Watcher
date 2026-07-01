"""Détection d'insultes avec gestion des orthographes alternatives.

La normalisation gère :
  - la casse et les accents (é -> e) ;
  - le « leet speak » (c0nnard, s@lope, pu7ain...) ;
  - les lettres répétées (connnnard -> conard) ;
  - la ponctuation / séparateurs (c-o-n-n-a-r-d, con.nard) ;
  - les lettres espacées (c o n n a r d).

Le dictionnaire ci-dessous n'a pas vocation à être exhaustif : ajoute/retire
des termes dans `_WORDS`, `_ROOTS` et `_PHRASES` selon ta modération.
"""
import re
import unicodedata

# Substitutions « leet speak » les plus courantes.
_LEET = str.maketrans(
    {
        "0": "o", "1": "i", "3": "e", "4": "a", "5": "s", "7": "t",
        "8": "b", "9": "g", "@": "a", "$": "s", "€": "e", "!": "i",
        "|": "i", "£": "l",
    }
)


def _collapse(text: str) -> str:
    """Réduit les lettres répétées : 'coooonnard' -> 'conard'."""
    return re.sub(r"(.)\1+", r"\1", text)


def normalize(text: str) -> str:
    """Minuscule, sans accents, leet appliqué, lettres uniquement, réduit."""
    text = unicodedata.normalize("NFKD", text)
    text = text.encode("ascii", "ignore").decode("ascii")
    text = text.lower().translate(_LEET)
    text = re.sub(r"[^a-z]+", " ", text)
    return _collapse(text).strip()


# --- Dictionnaire --------------------------------------------------------- #
# Termes vérifiés en mot entier (après normalisation/réduction). Inclut les
# abréviations et les mots courts (pour éviter les faux positifs par sous-chaîne).
_WORDS = {
    "con", "cons", "conard", "conasse", "cone", "conne", "conard",
    "salope", "salaud", "salopard", "pute", "putain", "poufiase", "poufe",
    "encule", "enculer", "enfoire", "batard", "merde", "merdeux", "merdique",
    "ordure", "abruti", "abrutie", "cretin", "cretine", "debile", "imbecile",
    "idiot", "idiote", "tocard", "boufon", "mongol", "mongolien", "bolos",
    "boloss", "casos", "gouine", "tarluze", "tapete", "pd", "pede", "tg",
    "ntm", "fdp", "raclure", "vermine", "clochard", "guignol", "blaireau",
    "trainee", "pignouf", "atarde",
    # Slurs (à filtrer) :
    "negro", "bougnoule", "bicot",
}

# Racines vérifiées aussi en sous-chaîne (formes segmentées / obfusquées).
# On évite volontairement les racines courtes ou trop génériques (con, pute...).
_ROOTS = {
    "conard", "conasse", "salopard", "encule", "enculer", "enfoire",
    "putain", "poufiase", "tarluze", "bougnoule", "mongolien", "raclure",
    "batard", "clochard",
}

# Expressions à détecter comme séquence de mots.
_PHRASES = [
    "ta gueule", "ferme ta gueule", "nique ta mere", "niquer ta mere",
    "fils de pute", "fille de pute", "trou du cul", "va te faire encule",
    "va te faire foutre", "sac a merde", "tas de merde", "sous merde",
    "encule de ta race",
]

_WORDS = {_collapse(w) for w in _WORDS}
_ROOTS = {_collapse(w) for w in _ROOTS}
_PHRASES = [_collapse(normalize(p)) for p in _PHRASES]


def _matches_word(token: str) -> bool:
    if token in _WORDS:
        return True
    # Tolérance sur le pluriel / suffixes simples.
    if token.endswith("s") and token[:-1] in _WORDS:
        return True
    return False


def find_insult(text: str) -> str | None:
    """Renvoie l'insulte détectée dans le texte, ou None."""
    norm = normalize(text)
    if not norm:
        return None
    tokens = norm.split()

    # 1) Mot entier.
    for token in tokens:
        if _matches_word(token):
            return token

    # 2) Lettres espacées : on recolle les suites de lettres seules.
    merged, group = [], []
    for token in tokens:
        if len(token) == 1:
            group.append(token)
        else:
            if group:
                merged.append("".join(group))
                group = []
    if group:
        merged.append("".join(group))
    for word in merged:
        word = _collapse(word)
        if _matches_word(word):
            return word
        if any(root in word for root in _ROOTS):
            return word

    # 3) Racines en sous-chaîne (obfuscation par séparateurs).
    despaced = _collapse(norm.replace(" ", ""))
    for root in _ROOTS:
        if root in despaced:
            return root

    # 4) Expressions.
    padded = f" {norm} "
    for phrase in _PHRASES:
        if f" {phrase} " in padded:
            return phrase

    return None
