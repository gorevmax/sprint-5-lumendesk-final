---
source_path: "documents/Выгрузки/webhooks-reprises.csv"
format: "csv"
source_sha256: "10a7bb9caae6eaf623872d5b4eb5e2e2f97c12afb3aadb07aa60092c5ff70ee5"
extractor: "extract-1"
---
Столбцы: Nature | Étape ou livraison | Minutes depuis envoi initial | Événement | HTTP | Observation

- [строка 2] Nature: calendrier; Étape ou livraison: Tentative 1; Minutes depuis envoi initial: 0; Observation: Envoi initial à 0 minute.
- [строка 3] Nature: calendrier; Étape ou livraison: Tentative 2; Minutes depuis envoi initial: 1; Observation: Nouvel envoi à 1 minute.
- [строка 4] Nature: calendrier; Étape ou livraison: Tentative 3; Minutes depuis envoi initial: 5; Observation: Nouvel envoi à 5 minutes.
- [строка 5] Nature: calendrier; Étape ou livraison: Tentative 4; Minutes depuis envoi initial: 15; Observation: Nouvel envoi à 15 minutes.
- [строка 6] Nature: calendrier; Étape ou livraison: Tentative 5; Minutes depuis envoi initial: 60; Observation: Nouvel envoi à 60 minutes.
- [строка 7] Nature: calendrier; Étape ou livraison: Tentative 6; Minutes depuis envoi initial: 240; Observation: Dernier envoi à 240 minutes.
- [строка 8] Nature: consigne; Étape ou livraison: Échec final; Observation: Après la sixième tentative en échec, l’événement prend l’état dead_letter.
- [строка 9] Nature: consigne; Étape ou livraison: Suspension; Observation: Trois événements dead_letter en une heure suspendent l’abonnement.
- [строка 10] Nature: consigne; Étape ou livraison: Reprise; Observation: Un administrateur réactive l’abonnement après un test HTTP 2xx.
- [строка 11] Nature: consigne; Étape ou livraison: Identifiant; Observation: L’event ID reste identique pendant toutes les tentatives.
- [строка 12] Nature: consigne; Étape ou livraison: Délai réseau; Observation: Chaque tentative a un délai de réponse maximal de 10 secondes.
- [строка 13] Nature: journal du test du 8 septembre; Étape ou livraison: livraison-31; Minutes depuis envoi initial: 0; Événement: cartes.cree; HTTP: 503; Observation: service aval indisponible; horloge mesurée depuis le premier envoi du même événement
- [строка 14] Nature: journal du test du 8 septembre; Étape ou livraison: livraison-32; Minutes depuis envoi initial: 1; Événement: commentaire.ajoute; HTTP: 429; Observation: Retry-After reçu; horloge mesurée depuis le premier envoi du même événement
- [строка 15] Nature: journal du test du 8 septembre; Étape ou livraison: livraison-33; Minutes depuis envoi initial: 5; Événement: carte.modifie; HTTP: 200; Observation: accusé de réception; horloge mesurée depuis le premier envoi du même événement
- [строка 16] Nature: journal du test du 8 septembre; Étape ou livraison: livraison-34; Minutes depuis envoi initial: 15; Événement: fichier.disponible; HTTP: 504; Observation: délai réseau dépassé; horloge mesurée depuis le premier envoi du même événement
- [строка 17] Nature: journal du test du 8 septembre; Étape ou livraison: livraison-35; Minutes depuis envoi initial: 60; Événement: membre.invite; HTTP: 202; Observation: traitement accepté; horloge mesurée depuis le premier envoi du même événement
- [строка 18] Nature: journal du test du 8 septembre; Étape ou livraison: livraison-36; Minutes depuis envoi initial: 240; Événement: carte.archive; HTTP: 500; Observation: erreur du destinataire; horloge mesurée depuis le premier envoi du même événement
- [строка 19] Nature: journal du test du 8 septembre; Étape ou livraison: livraison-37; Minutes depuis envoi initial: 0; Événement: cartes.cree; HTTP: 503; Observation: service aval indisponible; horloge mesurée depuis le premier envoi du même événement
- [строка 20] Nature: journal du test du 8 septembre; Étape ou livraison: livraison-38; Minutes depuis envoi initial: 1; Événement: commentaire.ajoute; HTTP: 429; Observation: Retry-After reçu; horloge mesurée depuis le premier envoi du même événement
- [строка 21] Nature: journal du test du 8 septembre; Étape ou livraison: livraison-39; Minutes depuis envoi initial: 5; Événement: carte.modifie; HTTP: 200; Observation: accusé de réception; horloge mesurée depuis le premier envoi du même événement
- [строка 22] Nature: journal du test du 8 septembre; Étape ou livraison: livraison-40; Minutes depuis envoi initial: 15; Événement: fichier.disponible; HTTP: 504; Observation: délai réseau dépassé; horloge mesurée depuis le premier envoi du même événement
- [строка 23] Nature: journal du test du 8 septembre; Étape ou livraison: livraison-41; Minutes depuis envoi initial: 60; Événement: membre.invite; HTTP: 202; Observation: traitement accepté; horloge mesurée depuis le premier envoi du même événement
- [строка 24] Nature: journal du test du 8 septembre; Étape ou livraison: livraison-42; Minutes depuis envoi initial: 240; Événement: carte.archive; HTTP: 500; Observation: erreur du destinataire; horloge mesurée depuis le premier envoi du même événement
- [строка 25] Nature: journal du test du 8 septembre; Étape ou livraison: livraison-43; Minutes depuis envoi initial: 0; Événement: cartes.cree; HTTP: 503; Observation: service aval indisponible; horloge mesurée depuis le premier envoi du même événement
- [строка 26] Nature: journal du test du 8 septembre; Étape ou livraison: livraison-44; Minutes depuis envoi initial: 1; Événement: commentaire.ajoute; HTTP: 429; Observation: Retry-After reçu; horloge mesurée depuis le premier envoi du même événement
- [строка 27] Nature: journal du test du 8 septembre; Étape ou livraison: livraison-45; Minutes depuis envoi initial: 5; Événement: carte.modifie; HTTP: 200; Observation: accusé de réception; horloge mesurée depuis le premier envoi du même événement
- [строка 28] Nature: journal du test du 8 septembre; Étape ou livraison: livraison-46; Minutes depuis envoi initial: 15; Événement: fichier.disponible; HTTP: 504; Observation: délai réseau dépassé; horloge mesurée depuis le premier envoi du même événement
- [строка 29] Nature: journal du test du 8 septembre; Étape ou livraison: livraison-47; Minutes depuis envoi initial: 60; Événement: membre.invite; HTTP: 202; Observation: traitement accepté; horloge mesurée depuis le premier envoi du même événement
- [строка 30] Nature: journal du test du 8 septembre; Étape ou livraison: livraison-48; Minutes depuis envoi initial: 240; Événement: carte.archive; HTTP: 500; Observation: erreur du destinataire; horloge mesurée depuis le premier envoi du même événement
- [строка 31] Nature: journal du test du 8 septembre; Étape ou livraison: livraison-49; Minutes depuis envoi initial: 0; Événement: cartes.cree; HTTP: 503; Observation: service aval indisponible; horloge mesurée depuis le premier envoi du même événement
- [строка 32] Nature: journal du test du 8 septembre; Étape ou livraison: livraison-50; Minutes depuis envoi initial: 1; Événement: commentaire.ajoute; HTTP: 429; Observation: Retry-After reçu; horloge mesurée depuis le premier envoi du même événement
- [строка 33] Nature: journal du test du 8 septembre; Étape ou livraison: livraison-51; Minutes depuis envoi initial: 5; Événement: carte.modifie; HTTP: 200; Observation: accusé de réception; horloge mesurée depuis le premier envoi du même événement
- [строка 34] Nature: journal du test du 8 septembre; Étape ou livraison: livraison-52; Minutes depuis envoi initial: 15; Événement: fichier.disponible; HTTP: 504; Observation: délai réseau dépassé; horloge mesurée depuis le premier envoi du même événement
- [строка 35] Nature: journal du test du 8 septembre; Étape ou livraison: livraison-53; Minutes depuis envoi initial: 60; Événement: membre.invite; HTTP: 202; Observation: traitement accepté; horloge mesurée depuis le premier envoi du même événement
- [строка 36] Nature: journal du test du 8 septembre; Étape ou livraison: livraison-54; Minutes depuis envoi initial: 240; Événement: carte.archive; HTTP: 500; Observation: erreur du destinataire; horloge mesurée depuis le premier envoi du même événement
