<?php
session_start();

// Inclusion des fichiers de configuration
require_once 'database.php';
require_once 'constants.php';

// Timezone
date_default_timezone_set('Africa/Conakry');

// Fonction pour nettoyer les données d'entrée
function sanitize_input($data) {
    return htmlspecialchars(strip_tags(trim($data)), ENT_QUOTES, 'UTF-8');
}

// Fonction pour rediriger
function redirect($url) {
    header("Location: $url");
    exit();
}

// Fonction pour afficher les messages flash
function set_flash_message($type, $message) {
    $_SESSION['flash_message'] = [
        'type' => $type,
        'message' => $message
    ];
}

function get_flash_message() {
    if (isset($_SESSION['flash_message'])) {
        $message = $_SESSION['flash_message'];
        unset($_SESSION['flash_message']);
        return $message;
    }
    return null;
}

// Fonction pour vérifier si l'utilisateur est connecté
function is_logged_in() {
    return isset($_SESSION['user_id']) && !empty($_SESSION['user_id']);
}

// Fonction pour obtenir les informations de l'utilisateur connecté
function get_current_user2() {
    if (is_logged_in()) {
        return [
            'id' => $_SESSION['user_id'],
            'nom_utilisateur' => $_SESSION['nom_utilisateur'],
            'nom' => $_SESSION['nom'],
            'prenoms' => $_SESSION['prenoms'],
            'role' => $_SESSION['role'],
            'poste' => $_SESSION['poste']
        ];
    }
    return null;
}

// Fonction pour vérifier les permissions
function has_permission($required_role) {
    if (!is_logged_in()) {
        return false;
    }
    
    if ($required_role === 'admin') {
        return $_SESSION['role'] === 'admin';
    }
    
    return true; // Tous les utilisateurs connectés ont accès aux fonctions de base
}
?>