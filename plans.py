"""
Définition des offres SmilePhish et de leurs quotas.

- "free" (Essai gratuit) : jusqu'à 100 destinataires par campagne, ET un quota cumulé
  de 100 emails envoyés À VIE sur l'ensemble du compte (toutes organisations/campagnes
  confondues) — c'est un essai, pas un usage récurrent illimité.
- "pro" (Pro) : jusqu'à 1000 destinataires envoyés en une seule campagne, sans plafond
  cumulé sur le nombre total de campagnes/envois.

Le passage en Pro ("/account/upgrade") est ici une bascule de démonstration : aucune
vraie passerelle de paiement n'est branchée. À remplacer par une intégration réelle
(Stripe, PayPal, virement + activation manuelle...) avant tout usage commercial.
"""

PLAN_LIMITS = {
    "free": {
        "max_targets_per_campaign": 100,
        "max_lifetime_sent": 100,
    },
    "pro": {
        "max_targets_per_campaign": 1000,
        "max_lifetime_sent": None,  # pas de plafond cumulé
    },
}


def limits_for(plan):
    return PLAN_LIMITS.get(plan, PLAN_LIMITS["free"])


def max_targets_per_campaign(plan):
    return limits_for(plan)["max_targets_per_campaign"]


def max_lifetime_sent(plan):
    return limits_for(plan)["max_lifetime_sent"]


# ---------------------------------------------------------------------------
# Durées de licence (abonnement d'une société cliente à l'offre Pro)
# ---------------------------------------------------------------------------
# Repères généraux observés sur le marché de la sensibilisation phishing / security
# awareness (KnowBe4, Proofpoint Security Awareness, Hoxhunt, usecure...) : l'offre
# annuelle est dominante, les formules plus courtes servent surtout de pilotes avant
# engagement. Ceci est une estimation de pratiques de marché généraliste, PAS une étude
# tarifaire vérifiée en direct — à confirmer par une recherche concurrentielle réelle
# avant toute communication commerciale.
LICENSE_DURATIONS = {
    1: {
        "label": "1 mois",
        "use_case": "Test ponctuel / pilote court avant engagement",
    },
    3: {
        "label": "3 mois",
        "use_case": "Pilote standard sur un trimestre",
    },
    6: {
        "label": "6 mois",
        "use_case": "Programme semestriel, courant en PME",
    },
    12: {
        "label": "12 mois",
        "use_case": "Offre standard du marché, la plus répandue (souvent avec remise vs mensuel)",
    },
}

LICENSE_MAX_SEATS = 5

