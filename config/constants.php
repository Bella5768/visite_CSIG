<?php
// Constantes de l'application
define('APP_NAME', 'Gestion des Visites - CSI');
define('APP_VERSION', '1.0.0');
define('ITEMS_PER_PAGE', 20);
define('SESSION_TIMEOUT', 3600); // 1 heure

// Couleurs institutionnelles
define('PRIMARY_COLOR', '#1e3a8a'); // Bleu institutionnel
define('SECONDARY_COLOR', '#3b82f6');
define('SUCCESS_COLOR', '#10b981');
define('WARNING_COLOR', '#f59e0b');
define('DANGER_COLOR', '#ef4444');

// Types d'identité
define('TYPES_IDENTITE', [
    'carte_nationale' => 'Carte Nationale d\'Identité',
    'passeport' => 'Passeport',
    'carte_electeur' => 'Carte d\'Électeur',
    'autre' => 'Autre document'
]);
?>