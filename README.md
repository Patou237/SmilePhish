# SmilePhish — Plateforme de simulation de phishing & sensibilisation

Guide complet, de A à Z. (Anciennement "YNAL Campagne" — rebrand complet en
"SmilePhish", design bleu & rouge.)

---

## Sommaire

- [A. Installation](#a-installation-une-seule-fois)
- [B. Lancer la plateforme](#b-lancer-la-plateforme)
- [C. Modèle de la plateforme (comptes, sociétés, organisations)](#c-modèle-de-la-plateforme)
- [D. Créer un compte et se connecter](#d-créer-un-compte-et-se-connecter)
- [E. Plans, quotas et licences d'entreprise](#e-plans-quotas-et-licences-dentreprise)
- [F. Créer et lancer une campagne](#f-créer-et-lancer-une-campagne)
- [G. Configurer l'envoi SMTP](#g-configurer-et-lancer-lenvoi)
- [H. Planifier une campagne (envoi différé)](#h-planifier-une-campagne-envoi-différé)
- [I. Exporter le rapport pour la direction](#i-exporter-le-rapport-pour-la-direction)
- [J. Super-administration & gouvernance](#j-super-administration--gouvernance)
- [K. Conformité, audit et traçabilité](#k-conformité-audit-et-traçabilité)
- [L. Assistance / support](#l-assistance--support)
- [M. Mises à jour de la plateforme](#m-mises-à-jour-de-la-plateforme)
- [N. Multi-langue](#n-multi-langue)
- [O. Exposer la plateforme pour Outlook/Internet](#o-exposer-la-plateforme-pour-que-les-liens-fonctionnent)
- [P. Garde-fous (à respecter)](#p-garde-fous-à-respecter)
- [Q. Ce qui est fonctionnel vs. démo/à compléter](#q-ce-qui-est-fonctionnel-vs-démoà-compléter)

---

## A. Installation (une seule fois)

1. Dézippez le dossier `smilephish` et ouvrez-le dans VSCode.
2. Ouvrez un terminal dans VSCode (Terminal → New Terminal).
3. Installez les dépendances :
   ```
   pip install -r requirements.txt
   ```
   (Flask, openpyxl, python-docx, reportlab, matplotlib, cryptography.)
4. **(Important)** Déclarez l'email qui doit devenir **super-administrateur**
   de la plateforme (vous, en tant que référent sécurité / éditeur de l'outil) :
   ```
   export SMILEPHISH_SUPERADMIN_EMAIL="votre-email@domaine.com"
   ```
   Le **premier compte créé avec cet email exact** recevra automatiquement le
   rôle super-admin. Faites-le en tout premier, avant toute autre inscription.
5. (Optionnel, recommandé) Si d'autres personnes doivent accéder à la
   plateforme depuis leur poste et que les destinataires doivent pouvoir
   cliquer sur les liens de tracking depuis Internet :
   ```
   export SMILEPHISH_PUBLIC_URL="http://VOTRE_IP_OU_DOMAINE:5000"
   ```
   Par défaut c'est `http://127.0.0.1:5000` (fonctionne en local uniquement —
   voir section O).

## B. Lancer la plateforme

```
python3 app.py
```
Puis ouvrez **http://127.0.0.1:5000**. La base (`data/smilephish.db`) se crée
automatiquement au premier lancement.

⚠️ **Pour que les campagnes planifiées se déclenchent** (voir section H), le
**serveur doit rester démarré en continu** — le planificateur est un
processus interne à `app.py` (aucun service externe requis), mais si le
processus Python s'arrête, plus aucune campagne planifiée ne part tant qu'il
n'est pas relancé. Pour un usage en production, lancez-le sur un serveur/VM
qui reste allumé (ou via un gestionnaire de process comme `systemd`, `pm2`,
ou un service cloud), pas uniquement sur le PC du planificateur.

## C. Modèle de la plateforme

SmilePhish distingue deux notions :

- **Une société abonnée** (`companies`) : l'entité qui souscrit un abonnement
  et détient **une licence** (voir section E), utilisable par **jusqu'à 5
  comptes** de cette société.
- **Une organisation ciblée** (`organisations`) : l'entreprise cliente (ou le
  service interne) **visée par une campagne de phishing**, rattachée au compte
  qui l'a créée. Un même compte peut gérer plusieurs organisations ciblées
  (utile si vous êtes consultant et menez des campagnes pour plusieurs
  clients).

Trois rôles existent :

| Rôle | Peut faire |
|---|---|
| **Membre** (`member`) | Créer/gérer ses propres campagnes et organisations, consulter son compte. |
| **Administrateur société** (`company_admin`) | Idem + souscrire/renouveler la licence de sa société, consulter l'audit des connexions limité à sa société. |
| **Super-administrateur** (`super_admin`) | Voir **toutes** les campagnes de **tous les comptes**, suspendre/réactiver une campagne même après son lancement, gérer les licences de toutes les sociétés (réinitialiser une clé compromise, révoquer), consulter l'audit complet de la plateforme, publier les mises à jour, traiter les tickets support. |

## D. Créer un compte et se connecter

1. Allez sur `/signup`. Les champs **Nom complet**, **Objectif d'utilisation
   déclaré** et l'acceptation des **conditions d'utilisation** sont
   **obligatoires** — c'est la traçabilité exigée pour un usage éthique
   (voir section K). Sans acceptation des conditions, le compte **ne peut
   pas être créé**.
2. Vous pouvez créer un compte avec **n'importe quelle adresse email**.
3. Si votre société a déjà souscrit une licence, saisissez sa **clé de
   licence** (format `SMPH-XXXX-XXXX-XXXX-XXXX`) pour rejoindre son
   abonnement — jusqu'à 5 comptes par société. Sans clé, un essai gratuit
   démarre automatiquement en votre nom (et une société à votre nom est créée
   pour vous, que vous pourrez abonner plus tard).
4. **Connexions simultanées** : un même compte peut être connecté sur
   **2 appareils/sessions maximum** en même temps. Une 3ᵉ connexion déconnecte
   automatiquement la session la plus ancienne (message affiché à la personne
   déconnectée).
5. Toute tentative de connexion (réussie ou échouée) est **journalisée** avec
   date/heure exactes, adresse IP et navigateur (voir section K).

## E. Plans, quotas et licences d'entreprise

| Plan | Emails par campagne | Plafond cumulé | Dashboard de suivi |
|---|---|---|---|
| **Essai gratuit** | 100 destinataires / campagne | 100 emails au total (à vie) | Oui |
| **Pro** (licence active) | 1000 destinataires / campagne | Aucun plafond cumulé | Oui, complet |

Le plan effectif d'un compte dépend de la **licence de sa société** : tant
qu'aucune licence Pro active n'est associée à la société du compte, celui-ci
reste en essai gratuit, même après avoir dépassé son plafond (les cibles
excédentaires d'une campagne sont tronquées, avec un message d'alerte sur le
tableau de bord).

### Durées de licence disponibles

Une société peut souscrire pour **1, 3, 6 ou 12 mois** (page "Mon compte" →
"Souscrire / renouveler"). Les durées proposées s'appuient sur les pratiques
courantes du marché SaaS B2B (mensuel, trimestriel, semestriel, annuel —
souvent avec une remise sur l'engagement annuel) ; il s'agit d'un repère
général de connaissance du secteur, **pas d'une étude de marché commandée et
vérifiée en temps réel** — à valider si vous bâtissez une offre commerciale
réelle dessus.

### Clé de licence

- Une **clé unique** (`SMPH-XXXX-XXXX-XXXX-XXXX`) est générée à la
  souscription pour la société.
- Utilisable par **jusqu'à 5 comptes** de cette société (saisie à
  l'inscription).
- **En cas de compromission** (clé divulguée, partagée en dehors de la
  société, etc.), **seul le super-administrateur** peut la réinitialiser
  (page `/superadmin/companies` → "Réinitialiser la clé") : l'ancienne clé
  cesse immédiatement de fonctionner pour toute nouvelle inscription.
- Le super-administrateur peut aussi **révoquer** entièrement la licence
  d'une société (passage automatique en essai gratuit pour tous ses comptes).

## F. Créer et lancer une campagne

1. Cliquez sur **"+ Nouvelle campagne"**.
2. Choisissez une organisation existante ou créez-en une nouvelle (nom de
   l'entreprise/service ciblé par le test).
3. Renseignez : nom de la campagne, objet de l'email, expéditeur affiché +
   email expéditeur (**un domaine/compte que vous contrôlez réellement** —
   voir garde-fous section P), le modèle HTML (variables `{{first_name}}`,
   `{{last_name}}`, `{{link}}`), et la liste des cibles : une ligne par
   personne, format `email,prenom,nom,departement`.
4. Un message d'alerte s'affiche si le nombre de cibles dépasse le quota de
   votre plan (voir section E) — les cibles en trop sont ignorées.
5. Sur le tableau de bord de la campagne : envoyez **immédiatement** ou
   **planifiez** l'envoi (section H).
6. Le tableau de bord affiche en direct les statistiques (envoyés / ouverts /
   cliqués / soumis / rejetés, en nombre et en %) et le **journal par
   destinataire** avec badges de couleur et date/heure exacte de chaque
   action — exploitable directement pour un rapport à la direction.

## G. Configurer et lancer l'envoi

| Champ | Ce que vous mettez |
|---|---|
| **Fournisseur du compte d'envoi** | Service de messagerie du compte utilisé pour **envoyer** (pas celui des destinataires). Le choisir pré-remplit serveur et port. |
| **Serveur SMTP** | Auto-rempli selon le fournisseur, ou à saisir pour un relais interne. |
| **Port** | 587 dans la quasi-totalité des cas (STARTTLS). |
| **Utilisateur SMTP** | Adresse email complète du compte d'envoi — doit être identique à "Email expéditeur" de la campagne. |
| **Mot de passe** | Celui du compte, ou un **mot de passe d'application** si le fournisseur l'exige. |
| **Délai entre chaque email** | 300 ms par défaut ; à ajuster selon le fournisseur. |

⚠️ **Erreur la plus fréquente ("Connection unexpectedly closed")** : le
serveur SMTP doit correspondre au fournisseur du compte **expéditeur**, pas à
celui des destinataires (ex. envoi depuis `@yahoo.fr` → serveur
`smtp.mail.yahoo.com`, jamais `smtp.gmail.com`, même si vos cibles sont sur
Gmail/Outlook).

### Paramètres exacts par fournisseur du compte d'envoi

| Fournisseur | Serveur SMTP | Port | Mot de passe d'application ? |
|---|---|---|---|
| **Gmail** / Google Workspace | `smtp.gmail.com` | 587 | **Oui, presque toujours** (myaccount.google.com → Sécurité → validation en 2 étapes puis mot de passe d'application). |
| **Outlook.com / Hotmail / Microsoft 365** | `smtp.office365.com` | 587 | Oui si double authentification activée (account.microsoft.com → Sécurité). |
| **Yahoo Mail** | `smtp.mail.yahoo.com` | 587 | **Oui, quasi systématiquement** (yahoo.com → Compte → Sécurité du compte). |
| Relais SMTP interne de l'entreprise | fourni par votre service IT | 25, 465 ou 587 | Selon la politique interne. |

Cibler des destinataires chez **n'importe quel fournisseur** (Outlook, Gmail,
Yahoo, domaine d'entreprise...) fonctionne sans configuration particulière :
seul le compte **d'envoi** doit être correctement paramétré ci-dessus.

### En cas d'erreur

- **"Connection unexpectedly closed"** : voir l'encart ci-dessus.
- **Authentification refusée** : utilisez un mot de passe d'application.
- **Rejets partiels** : des adresses individuelles peuvent être rejetées sans
  bloquer l'envoi aux autres — détail affiché sous le bouton d'envoi.

### Combien d'emails à la fois ?

La plateforme elle-même n'impose pas de limite technique d'envoi séquentiel
au-delà de votre quota de plan (section E) ; la vraie limite vient de votre
fournisseur SMTP (ex. ~500/jour en Gmail personnel, bien plus en
Microsoft 365/relais interne). Ajustez le délai entre emails en conséquence.

## H. Planifier une campagne (envoi différé)

Sur le tableau de bord d'une campagne, l'onglet "Planifier" permet de :

1. Choisir une **date et heure de déclenchement** (même si le poste qui a
   planifié est éteint à ce moment-là — **tant que le serveur SmilePhish
   lui-même tourne**, voir section B).
2. Saisir les identifiants SMTP à utiliser au moment du déclenchement : ils
   sont **chiffrés** (bibliothèque `cryptography`/Fernet, clé stockée dans
   `data/secret.key`) et stockés **uniquement pour un envoi planifié** —
   jamais pour un envoi immédiat.
3. Suivre l'état depuis la page **"Planifications"** (`/schedules`) :
   *planifiée*, *envoyée* ou *échouée* (avec le message d'erreur, par ex. si
   les identifiants SMTP sont invalides au moment de l'exécution).
4. **Plusieurs sociétés/campagnes en parallèle** : chaque planification est
   indépendante et horodatée ; le planificateur interne vérifie toutes les
   20 secondes les campagnes arrivées à échéance et les exécute dans l'ordre,
   quel que soit le nombre de sociétés ou de comptes concernés.
5. Si le **super-administrateur suspend** la campagne avant l'heure prévue
   (section J), l'envoi planifié est **bloqué** au moment de l'exécution,
   avec le motif affiché dans l'historique.

## I. Exporter le rapport pour la direction

4 formats + un CSV brut, disponibles en un clic sur le tableau de bord :

- **Excel (.xlsx)** : feuille "Résumé" (stats + %, graphique natif modifiable)
  et feuille "Détail par destinataire".
- **Word (.docx)** : résumé exécutif, tableau de statistiques, tableau
  nominatif détaillé, graphique intégré (image).
- **PDF** : mise en page imprimable, mêmes informations, graphique intégré.
- **HTML** : page autonome avec graphique SVG, pour un partage rapide.

Chaque export affiche le **nom de l'organisation ciblée**, le branding
SmilePhish (bleu & rouge), et pour chaque collaborateur ayant interagi : la
**date et l'heure exactes** d'ouverture, de clic et de soumission, ainsi que
le statut de sa dernière action — pour prioriser qui sensibiliser.

## J. Super-administration & gouvernance

Accessible uniquement au compte dont l'email correspond à
`SMILEPHISH_SUPERADMIN_EMAIL` (section A), via le lien **"Super-admin"** dans
le menu (visible seulement pour ce rôle) :

- **`/superadmin`** : liste de **toutes les campagnes** lancées par tous les
  comptes, avec statistiques résumées. Vous pouvez **suspendre** une campagne
  — y compris **déjà lancée** — si sa légitimité vous paraît douteuse (avec
  motif optionnel) ; elle est alors bloquée pour tout nouvel envoi (immédiat
  ou planifié) jusqu'à réactivation.
- **`/superadmin/companies`** : toutes les sociétés abonnées, leur clé de
  licence, son statut, ses sièges utilisés. Réinitialisation de clé ou
  révocation complète d'une licence en un clic.
- **`/superadmin/audit`** : piste d'audit complète (toutes connexions, tous
  comptes).
- **`/superadmin/updates`** : publication des notifications de mise à jour
  (section M).
- **`/superadmin/support`** : tickets d'assistance de tous les comptes
  (section L).

## K. Conformité, audit et traçabilité

- **Conditions d'utilisation** (`/terms`) : clauses contractuelles et
  réglementaires à accepter obligatoirement à l'inscription (usage
  strictement limité à des campagnes mandatées, pas d'usurpation de marque
  réelle, traçabilité des comptes, pouvoirs du super-admin, etc.). **Ce
  document est un cadre indicatif, pas un contrat validé par un juriste** — à
  faire relire avant tout usage commercial réel (voir section Q).
- **Traçabilité à l'inscription** : nom complet, téléphone (optionnel),
  objectif d'utilisation déclaré — permettent de retrouver le responsable
  d'une campagne en cas de signalement d'usage non éthique.
- **Piste d'audit des connexions** : chaque tentative de connexion (succès ou
  échec) est journalisée avec date/heure, IP et navigateur.
  - Un **administrateur de société** ne voit que les connexions des comptes
    de **sa propre société** (`/audit`).
  - Le **super-administrateur** voit l'intégralité des journaux de la
    plateforme (`/superadmin/audit`).
- **Sessions concurrentes** : maximum **2 connexions simultanées** par
  compte ; au-delà, la session la plus ancienne est automatiquement fermée.

## L. Assistance / support

Page **"Support"** (`/support`), accessible à tout compte connecté :
ouverture de tickets (sujet, message, urgence) et suivi de leurs propres
tickets. Le super-administrateur les traite depuis `/superadmin/support`.

⚠️ Il s'agit d'un **système de tickets uniquement** — aucune prise de main à
distance réelle sur le poste de l'utilisateur n'est implémentée. À brancher
sur un outil dédié (ex. TeamViewer, AnyDesk, assistance à distance Windows)
si une prise de main effective est nécessaire en production.

## M. Mises à jour de la plateforme

Le super-administrateur publie une mise à jour (version, titre, description,
action requise) depuis `/superadmin/updates`. Une bannière s'affiche alors à
**tous les comptes n'ayant pas encore acquitté** cette mise à jour, sur
chaque page, tant qu'ils n'ont pas cliqué sur "J'ai pris connaissance".

## N. Multi-langue

Sélecteur de langue dans le menu : **français (par défaut), anglais,
allemand, espagnol, chinois**. La langue est mémorisée par session. Le
système de traduction (`i18n.py`) est conçu pour être facilement étendu à
d'autres langues.

Par souci de temps, les écrans d'administration/légaux ajoutés dans cette
dernière évolution (compte & licence, conditions, support, pages
super-admin) sont **en français uniquement** ; les écrans existants
(accueil, nouvelle campagne, tableau de bord, connexion/inscription, page de
sensibilisation) restent disponibles dans les 5 langues.

## O. Exposer la plateforme pour que les liens fonctionnent

Si vous lancez tout en local, les liens de tracking ne seront cliquables que
depuis votre poste. Pour un test grandeur nature (collègues cliquant depuis
leur propre Outlook) :

- **Solution rapide (ngrok)** : installez [ngrok](https://ngrok.com), lancez
  `ngrok http 5000`, copiez l'URL publique fournie, puis :
  ```
  export SMILEPHISH_PUBLIC_URL="https://xxxx.ngrok-free.app"
  ```
  et relancez `python3 app.py`.
- **Solution interne** : déployez sur une VM/serveur de l'entreprise
  accessible depuis le réseau interne, utilisez son IP/nom DNS. **Ce même
  serveur doit rester démarré en continu** pour que les campagnes planifiées
  (section H) se déclenchent même si votre PC personnel est éteint.

## P. Garde-fous (à respecter)

- **Domaine d'envoi** : utilisez un domaine/compte que vous possédez
  réellement (jamais une usurpation de outlook.com / microsoft.com). Cibler
  des destinataires `@outlook.com` ou toute autre boîte est normal ;
  falsifier l'identité technique d'Outlook ne l'est pas, et l'outil ne le
  permet pas (pas de logo officiel copié, pas de clone de page de connexion).
- **Page cible** : dès le clic, sensibilisation immédiate avec les bons
  réflexes — aucune collecte de vrai mot de passe.
- **Cadre d'usage** : strictement interne, avec mandat de la direction, dans
  le cadre d'un programme de sensibilisation à la sécurité — formalisé
  désormais par l'acceptation obligatoire des conditions d'utilisation
  (section K) à l'inscription.

## Q. Ce qui est fonctionnel vs. démo/à compléter

Pour une transparence totale avant tout usage réel ou commercial :

| Fonctionnalité | Statut |
|---|---|
| Envoi SMTP réel, tracking ouverture/clic/soumission, dashboard, exports | ✅ Fonctionnel |
| Planification différée (serveur allumé requis) | ✅ Fonctionnel |
| Comptes, rôles, sociétés, licences, quotas | ✅ Fonctionnel |
| Sessions concurrentes, audit des connexions | ✅ Fonctionnel |
| Suspension/réactivation de campagne par le super-admin | ✅ Fonctionnel |
| Notifications de mise à jour + accusé de réception | ✅ Fonctionnel |
| **Souscription de licence** (`/company/subscribe`) | ⚠️ **Démo** : génère/renouvelle la clé en base, **aucune passerelle de paiement réelle** n'est branchée (pas de Stripe/PayPal/etc.) — à intégrer avant toute commercialisation. |
| **Support** (`/support`) | ⚠️ **Tickets uniquement**, pas de prise de main à distance réelle. |
| **Durées de licence (1/3/6/12 mois)** | ⚠️ Basées sur des pratiques générales du marché SaaS, pas une étude de marché commandée et vérifiée en direct. |
| **Conditions d'utilisation** (`/terms`) | ⚠️ Cadre indicatif rédigé pour l'usage ; à faire relire par un juriste avant tout usage contractuel réel. |
| Écrans super-admin / légaux / compte / support | ⚠️ Français uniquement (voir section N). |
