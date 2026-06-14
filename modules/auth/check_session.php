<?php
require_once '../../config/config.php';

// Enregistrer le nom d'utilisateur avant la déconnexion pour le message
$username = isset($_SESSION['nom_utilisateur']) ? $_SESSION['nom_utilisateur'] : '';

// Détruire la session
session_destroy();

// Démarrer une nouvelle session pour le message flash
session_start();
set_flash_message('info', 'Vous avez été déconnecté avec succès. À bientôt !');

// Rediriger vers la page de connexion
redirect('login.php');
?>