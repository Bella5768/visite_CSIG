<?php
require_once '../../config/config.php';

if (session_status() === PHP_SESSION_NONE) {
    session_start();
}

// Sauvegarde (si besoin pour logs)
$username = $_SESSION['nom_utilisateur'] ?? '';

// Détruire toutes les données de session
$_SESSION = [];
if (ini_get("session.use_cookies")) {
    $params = session_get_cookie_params();
    setcookie(session_name(), '', time() - 42000,
        $params["path"], $params["domain"],
        $params["secure"], $params["httponly"]
    );
}
session_destroy();

// Nouvelle session pour flash
session_start();
set_flash_message('info', 'Vous avez été déconnecté avec succès. À bientôt !');

// Redirection
redirect('login.php');
