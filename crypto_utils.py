"""
Chiffrement des identifiants SMTP pour les envois PLANIFIÉS uniquement.

Important : pour un envoi immédiat ("Envoyer maintenant"), les identifiants SMTP ne
sont toujours jamais stockés (comportement inchangé). Mais une campagne PLANIFIÉE doit
pouvoir s'envoyer automatiquement plus tard, sans que vous soyez présent pour ressaisir
le mot de passe : il faut donc le conserver quelque part. Il est stocké chiffré
(Fernet / AES symétrique) avec une clé générée localement et stockée dans
`data/secret.key` (jamais dans le code, jamais dans la base de données).

Protégez ce fichier comme un mot de passe : quiconque y a accès peut déchiffrer les
identifiants SMTP stockés pour les envois planifiés. Ne le committez jamais dans un
dépôt de code, ne l'envoyez jamais par email.
"""

import os
from cryptography.fernet import Fernet

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
KEY_PATH = os.path.join(BASE_DIR, "data", "secret.key")

_fernet = None


def _load_or_create_key():
    os.makedirs(os.path.dirname(KEY_PATH), exist_ok=True)
    if os.path.exists(KEY_PATH):
        with open(KEY_PATH, "rb") as f:
            return f.read()
    key = Fernet.generate_key()
    with open(KEY_PATH, "wb") as f:
        f.write(key)
    try:
        os.chmod(KEY_PATH, 0o600)
    except OSError:
        pass
    return key


def get_fernet():
    global _fernet
    if _fernet is None:
        _fernet = Fernet(_load_or_create_key())
    return _fernet


def encrypt(plain_text):
    if plain_text is None:
        return None
    return get_fernet().encrypt(plain_text.encode("utf-8")).decode("utf-8")


def decrypt(token):
    if token is None:
        return None
    return get_fernet().decrypt(token.encode("utf-8")).decode("utf-8")
