---
source_path: "documents/Франция/Assistant abonnement.xlsx"
format: "xlsx"
source_sha256: "a77d2d9dbdd1a09accbd0d6003ae19454ae15edc338b8730f732522f76945747"
extractor: "extract-1"
---
## Лист: Abonnement

Название листа: Messages de l’assistant

Примечание листа: Barème publié par Assistant Product pour les abonnements LumenDesk, applicable depuis le 1er septembre 2026. Ces quotas sont par workspace et par mois, et non par utilisateur.

Столбцы: Offre ou sujet | Valeur | Unité | Condition

- [строка 8] Offre ou sujet: Starter; Valeur: 100; Unité: messages; Condition: Par workspace et par mois
- [строка 9] Offre ou sujet: Team; Valeur: 1200; Unité: messages; Condition: Par workspace et par mois
- [строка 10] Offre ou sujet: Enterprise; Valeur: 10000; Unité: messages; Condition: Par workspace et par mois
- [строка 11] Offre ou sujet: Remise à zéro; Valeur: 1; Unité: jour du mois; Condition: À 00:00 UTC le premier jour du mois
- [строка 12] Offre ou sujet: Message utilisateur; Valeur: 1; Unité: message; Condition: Une demande envoyée compte pour une unité
- [строка 13] Offre ou sujet: Erreur technique; Valeur: 0; Unité: message; Condition: Une demande rejetée par une erreur serveur ne compte pas
- [строка 14] Offre ou sujet: Solde; Valeur: Non reportable; Unité: règle; Condition: Le solde inutilisé expire à la fin du mois
- [строка 15] Offre ou sujet: Dépassement; Valeur: Assistant en lecture seule; Unité: règle; Condition: Les anciens échanges restent consultables
- [строка 16] Offre ou sujet: Option supplémentaire; Valeur: Accord commercial requis; Unité: règle; Condition: Le support ne peut pas inventer un quota additionnel

## Лист: Exemples de comptage

Название листа: Contrôle des demandes de septembre

Столбцы: Date UTC | Workspace | Demande | Réponse du service | Messages comptés

- [строка 6] Date UTC: 2026-09-01 10:30; Workspace: atelier-1; Demande: Résumé de réunion; Réponse du service: Erreur serveur; demande rejetée; Messages comptés: 0
- [строка 7] Date UTC: 2026-09-02 10:30; Workspace: atelier-2; Demande: Recherche de carte; Réponse du service: Demande envoyée; Messages comptés: 1
- [строка 8] Date UTC: 2026-09-03 10:30; Workspace: atelier-3; Demande: Explication du projet; Réponse du service: Demande envoyée; Messages comptés: 1
- [строка 9] Date UTC: 2026-09-04 10:30; Workspace: atelier-4; Demande: Synthèse de commentaires; Réponse du service: Demande envoyée; Messages comptés: 1
- [строка 10] Date UTC: 2026-09-05 10:30; Workspace: atelier-5; Demande: Liste des actions; Réponse du service: Demande envoyée; Messages comptés: 1
- [строка 11] Date UTC: 2026-09-06 10:30; Workspace: atelier-1; Demande: Résumé de réunion; Réponse du service: Demande envoyée; Messages comptés: 1
- [строка 12] Date UTC: 2026-09-07 10:30; Workspace: atelier-2; Demande: Recherche de carte; Réponse du service: Demande envoyée; Messages comptés: 1
- [строка 13] Date UTC: 2026-09-08 10:30; Workspace: atelier-3; Demande: Explication du projet; Réponse du service: Demande envoyée; Messages comptés: 1
- [строка 14] Date UTC: 2026-09-09 10:30; Workspace: atelier-4; Demande: Synthèse de commentaires; Réponse du service: Erreur serveur; demande rejetée; Messages comptés: 0
- [строка 15] Date UTC: 2026-09-10 10:30; Workspace: atelier-5; Demande: Liste des actions; Réponse du service: Demande envoyée; Messages comptés: 1
- [строка 16] Date UTC: 2026-09-11 10:30; Workspace: atelier-1; Demande: Résumé de réunion; Réponse du service: Demande envoyée; Messages comptés: 1
- [строка 17] Date UTC: 2026-09-12 10:30; Workspace: atelier-2; Demande: Recherche de carte; Réponse du service: Demande envoyée; Messages comptés: 1
- [строка 18] Date UTC: 2026-09-13 10:30; Workspace: atelier-3; Demande: Explication du projet; Réponse du service: Demande envoyée; Messages comptés: 1
- [строка 19] Date UTC: 2026-09-14 10:30; Workspace: atelier-4; Demande: Synthèse de commentaires; Réponse du service: Demande envoyée; Messages comptés: 1
- [строка 20] Date UTC: 2026-09-15 10:30; Workspace: atelier-5; Demande: Liste des actions; Réponse du service: Demande envoyée; Messages comptés: 1
- [строка 21] Date UTC: 2026-09-16 10:30; Workspace: atelier-1; Demande: Résumé de réunion; Réponse du service: Demande envoyée; Messages comptés: 1
- [строка 22] Date UTC: 2026-09-17 10:30; Workspace: atelier-2; Demande: Recherche de carte; Réponse du service: Erreur serveur; demande rejetée; Messages comptés: 0
- [строка 23] Date UTC: 2026-09-18 10:30; Workspace: atelier-3; Demande: Explication du projet; Réponse du service: Demande envoyée; Messages comptés: 1
- [строка 24] Date UTC: 2026-09-19 10:30; Workspace: atelier-4; Demande: Synthèse de commentaires; Réponse du service: Demande envoyée; Messages comptés: 1
- [строка 25] Date UTC: 2026-09-20 10:30; Workspace: atelier-5; Demande: Liste des actions; Réponse du service: Demande envoyée; Messages comptés: 1
- [строка 26] Date UTC: 2026-09-01 10:30; Workspace: atelier-1; Demande: Résumé de réunion; Réponse du service: Demande envoyée; Messages comptés: 1
- [строка 27] Date UTC: 2026-09-02 10:30; Workspace: atelier-2; Demande: Recherche de carte; Réponse du service: Demande envoyée; Messages comptés: 1
- [строка 28] Date UTC: 2026-09-03 10:30; Workspace: atelier-3; Demande: Explication du projet; Réponse du service: Demande envoyée; Messages comptés: 1
- [строка 29] Date UTC: 2026-09-04 10:30; Workspace: atelier-4; Demande: Synthèse de commentaires; Réponse du service: Demande envoyée; Messages comptés: 1
- [строка 30] Date UTC: 2026-09-05 10:30; Workspace: atelier-5; Demande: Liste des actions; Réponse du service: Erreur serveur; demande rejetée; Messages comptés: 0
- [строка 31] Date UTC: 2026-09-06 10:30; Workspace: atelier-1; Demande: Résumé de réunion; Réponse du service: Demande envoyée; Messages comptés: 1
- [строка 32] Date UTC: 2026-09-07 10:30; Workspace: atelier-2; Demande: Recherche de carte; Réponse du service: Demande envoyée; Messages comptés: 1
- [строка 33] Date UTC: 2026-09-08 10:30; Workspace: atelier-3; Demande: Explication du projet; Réponse du service: Demande envoyée; Messages comptés: 1
- [строка 34] Date UTC: 2026-09-09 10:30; Workspace: atelier-4; Demande: Synthèse de commentaires; Réponse du service: Demande envoyée; Messages comptés: 1
- [строка 35] Date UTC: 2026-09-10 10:30; Workspace: atelier-5; Demande: Liste des actions; Réponse du service: Demande envoyée; Messages comptés: 1

## Лист: Questions clients

Название листа: Réponses validées lors de la revue

Столбцы: Question | Réponse

- [строка 6] Question: Combien pour Team ?; Réponse: 1200 messages par workspace et par mois
- [строка 7] Question: Quand le solde change-t-il ?; Réponse: Remise à zéro le premier jour du mois à 00:00 UTC
- [строка 8] Question: Solde inutilisé; Réponse: Il expire à la fin du mois et n’est pas reportable
- [строка 9] Question: Un fil égale-t-il un message ?; Réponse: Un même fil peut consommer plusieurs messages
- [строка 10] Question: Erreur serveur; Réponse: Une demande rejetée par une erreur serveur compte pour zéro
- [строка 11] Question: Après dépassement; Réponse: Les anciens échanges restent consultables, assistant en lecture seule
- [строка 12] Question: Messages supplémentaires; Réponse: Un accord commercial est nécessaire; le support ne peut pas inventer un quota
