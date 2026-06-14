<?php
require_once __DIR__ . '/../../config/config.php';
require_once __DIR__ . '/visiteurs_functions.php';

// Vérifier la session (AJAX, donc pas de redirection)
if (!is_logged_in()) {
    header('Content-Type: application/json');
    echo json_encode(['error' => 'Session expirée']);
    exit;
}

// Récupérer le terme de recherche
$query = isset($_GET['q']) ? trim($_GET['q']) : '';

if (empty($query) || strlen($query) < 2) {
    header('Content-Type: application/json');
    echo json_encode([]);
    exit;
}

// Effectuer la recherche
$results = search_visiteurs_ajax($query);

// Retourner les résultats en JSON
header('Content-Type: application/json');
echo json_encode($results);
?>