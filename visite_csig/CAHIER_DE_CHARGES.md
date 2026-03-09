# Cahier des Charges - Système de Gestion de Rendez-vous CSIG

## 1. Présentation du Projet

### 1.1 Contexte
La Cité des Sciences et de l'Innovation de Guinée (CSIG) souhaite mettre en place un système de gestion de rendez-vous pour optimiser l'accueil des visiteurs et la planification des entretiens.

### 1.2 Objectifs
- Automatiser la prise de rendez-vous en ligne
- Gérer les créneaux de disponibilité
- Notifier automatiquement les parties concernées
- Assurer un suivi efficace des rendez-vous
- Améliorer l'expérience utilisateur

## 2. Spécifications Fonctionnelles

### 2.1 Module de Gestion des Créneaux
- **Création de créneaux** : Administration peut définir des plages horaires
- **Association aux motifs** : Chaque créneau lié à un type de visite
- **Gestion de capacité** : Limiter le nombre de visiteurs par créneau
- **Visualisation calendrier** : Interface intuitive pour voir les disponibilités

### 2.2 Module de Prise de Rendez-vous Public
- **Formulaire en ligne** : Interface accessible sans authentification
- **Sélection par motif** : Choix du type de visite
- **Affichage des créneaux** : Voir uniquement les disponibilités
- **Validation automatique** : Vérification en temps réel
- **Confirmation immédiate** : Email de confirmation envoyé

### 2.3 Module de Suivi
- **Token unique** : Lien de suivi personnalisé pour chaque rendez-vous
- **Statuts en temps réel** : Planifié, confirmé, en cours, terminé, annulé
- **Historique** : Traçabilité complète des modifications

### 2.4 Module de Notification
- **Email demandeur** : Confirmation avec détails du rendez-vous
- **Email correspondant** : Notification quand un rendez-vous lui est assigné
- **Rappels automatiques** : Alertes avant le rendez-vous
- **Templates personnalisés** : Emails professionnels avec branding CSIG

### 2.5 Module d'Administration Interne
- **Tableau de bord** : Vue d'ensemble des activités
- **Gestion des motifs** : Types de visite configurables
- **Gestion des correspondants** : Personnel interne assignable
- **Export des données** : Rapports et statistiques

## 3. Spécifications Techniques

### 3.1 Architecture
- **Framework** : Django 4.2.28
- **Base de données** : SQLite (développement) / PostgreSQL (production)
- **Frontend** : Bootstrap 5 + Bootstrap Icons
- **Backend** : Python 3.14

### 3.2 Modèles de Données

#### RendezVous
- visiteur (ForeignKey)
- motif (ForeignKey)
- correspondant (ForeignKey, nullable)
- creneau (ForeignKey, nullable)
- date_rendez_vous (DateField)
- heure_debut/fin (TimeField)
- statut (CharField, choices)
- sujet (CharField)
- description (TextField)
- cree_par (ForeignKey, nullable)

#### CreneauDisponibilite
- motif (ForeignKey)
- date (DateField)
- heure_debut/fin (TimeField)
- capacite (PositiveIntegerField)
- actif (BooleanField)

#### Visiteur
- nom/prenoms (CharField)
- telephone/email (CharField, nullable)
- adresse (TextField)
- type_identite/numero_identite (CharField, nullable)

### 3.3 Contraintes
- **Unicités** : Un rendez-vous actif par créneau maximum
- **Validation** : Champs obligatoires vérifiés
- **Sécurité** : Protection CSRF et validation des entrées

## 4. Interface Utilisateur

### 4.1 Formulaire Public
- **Design responsive** : Compatible mobile/desktop
- **Branding institutionnel** : Logos officiels CSIG/Simandou
- **Navigation intuitive** : Étapes claires et guidées
- **Validation temps réel** : Messages d'erreur explicites

### 4.2 Administration
- **Interface moderne** : Cards, modals, tableaux interactifs
- **Actions rapides** : CRUD via modals sans rechargement
- **Filtres et recherche** : Trouver rapidement les informations
- **Exports** : CSV/PDF pour les rapports

## 5. Fonctionnalités Avancées

### 5.1 Gestion des Conflits
- **Détection automatique** : Pas de double réservation
- **Alertes immédiates** : Messages clairs en cas de conflit
- **Mise à jour temps réel** : Interface synchronisée

### 5.2 Sécurité
- **Accès contrôlé** : Rôles et permissions définis
- **Journalisation** : Traçabilité des actions
- **Protection données** : Validation et sanitisation

### 5.3 Performance
- **Optimisation requêtes** : select_related, prefetch_related
- **Cache statique** : Whitenoise pour les assets
- **Pagination** : Grandes listes gérées efficacement

## 6. Déploiement et Maintenance

### 6.1 Configuration Production
- **Domaine stable** : URL publique pour le formulaire
- **Email SMTP** : Configuration multi-fournisseurs
- **HTTPS** : Sécurisation des communications
- **Backup** : Sauvegarde régulière des données

### 6.2 Monitoring
- **Logs détaillés** : Traçabilité des erreurs
- **Métriques usage** : Statistiques de fréquentation
- **Alertes système** : Notification des problèmes

## 7. Livrables

### 7.1 Code Source
- Application Django complète
- Templates HTML responsives
- Fichiers CSS/JS optimisés
- Documentation technique

### 7.2 Documentation
- Manuel utilisateur
- Guide administrateur
- Documentation API
- Procédures déploiement

### 7.3 Tests
- Tests unitaires modèles
- Tests fonctionnels vues
- Tests intégration email
- Tests de sécurité

## 8. Évolutions Futures

### 8.1 Phase 2
- **Application mobile** : Version native iOS/Android
- **Intégration calendrier** : Synchronisation Google/Outlook
- **Notifications SMS** : Rappels par message texte
- **Paiement en ligne** : Pour certains types de visite

### 8.2 Phase 3
- **Intelligence artificielle** : Optimisation plannification
- **Tableaux de bord avancés** : Analytics prédictifs
- **API publique** : Intégration partenaires
- **Multilingue** : Support anglais/français

## 9. Contraintes et Exigences

### 9.1 Temporelles
- **Développement** : 4-6 semaines
- **Tests** : 1-2 semaines
- **Déploiement** : 1 semaine
- **Formation** : 2 jours

### 9.2 Budgétaires
- **Développement** : À définir
- **Hébergement** : Coût mensuel estimé
- **Maintenance** : Contrat annuel support

### 9.3 Réglementaires
- **RGPD** : Conformité protection données
- **Lois guinéennes** : Respect réglementation locale
- **Accessibilité** : WCAG 2.1 niveau AA

## 10. Validation et Recette

### 10.1 Critères d'acceptation
- ✅ Formulaire public fonctionnel
- ✅ Emails automatiques opérationnels
- ✅ Gestion des créneaux efficace
- ✅ Interface admin intuitive
- ✅ Pas de double réservation
- ✅ Performance acceptable

### 10.2 Tests utilisateur
- **Scénarios nominaux** : Cas d'utilisation standards
- **Cas limites** : Gestion erreurs
- **Tests charge** : Utilisation simultanée
- **Tests sécurité** : Tentatives intrusion

---

**Version** : 1.0  
**Date** : Mars 2026  
**Auteur** : Équipe de développement CSIG  
**Contact** : support@csig-guinee.org
