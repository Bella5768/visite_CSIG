<?php
require_once __DIR__ . '/../../config/config.php';

// Fonction pour créer un nouveau visiteur
function create_visiteur($data) {
    try {
        $pdo = get_db_connection();
        
        // Vérifier si le numéro d'identité existe déjà 
        $stmt = $pdo->prepare("
            SELECT id FROM visiteurs 
            WHERE numero_identite = ? AND type_identite = ?
        ");
        $stmt->execute([$data['numero_identite'], $data['type_identite']]);
        
        if ($stmt->fetch()) {
            return [
                'success' => false, 
                'message' => 'Un visiteur avec ce numéro d\'identité existe déjà'
            ];
        }
        
        $stmt = $pdo->prepare("
            INSERT INTO visiteurs (type_identite, numero_identite, nom, prenoms, 
                                 telephone, email, adresse)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ");
        
        $stmt->execute([
            $data['type_identite'],
            $data['numero_identite'],
            $data['nom'],
            $data['prenoms'],
            $data['telephone'] ?: null,
            $data['email'] ?: null,
            $data['adresse'] ?: null
        ]);
        
        $visiteur_id = $pdo->lastInsertId();
        
        return [
            'success' => true, 
            'visiteur_id' => $visiteur_id,
            'message' => 'Visiteur créé avec succès'
        ];
        
    } catch (Exception $e) {
        error_log("Erreur création visiteur : " . $e->getMessage());
        return [
            'success' => false, 
            'message' => 'Erreur lors de la création du visiteur'
        ];
    }
}

// Fonction pour modifier un visiteur
// CORRECTION : La signature de la fonction a été modifiée pour correspondre
// au script modifier.php. Elle reçoit des variables individuelles.
function update_visiteur($visiteur_id, $nom, $prenoms, $type_identite, $numero_identite, $telephone, $email) {
    try {
        $pdo = get_db_connection();
        
        // Vérifier si le numéro d'identité existe déjà (sauf pour ce visiteur)
        $stmt = $pdo->prepare("
            SELECT id FROM visiteurs 
            WHERE numero_identite = ? AND type_identite = ? AND id != ?
        ");
        $stmt->execute([$numero_identite, $type_identite, $visiteur_id]);
        
        if ($stmt->fetch()) {
            return [
                'success' => false, 
                'message' => 'Un autre visiteur avec ce numéro d\'identité existe déjà'
            ];
        }
        
        $stmt = $pdo->prepare("
            UPDATE visiteurs 
            SET type_identite = ?, numero_identite = ?, nom = ?, prenoms = ?, 
                telephone = ?, email = ?
            WHERE id = ?
        ");
        
        // La ligne ci-dessous exécute la requête avec les paramètres reçus.
        $stmt->execute([
            $type_identite,
            $numero_identite,
            $nom,
            $prenoms,
            $telephone ?: null,
            $email ?: null,
            $visiteur_id
        ]);
        
        return [
            'success' => true, 
            'message' => 'Visiteur modifié avec succès'
        ];
        
    } catch (Exception $e) {
        error_log("Erreur modification visiteur : " . $e->getMessage());
        return [
            'success' => false, 
            'message' => 'Erreur lors de la modification du visiteur'
        ];
    }
}

// Fonction pour obtenir un visiteur par ID
function get_visiteur_by_id($visiteur_id) {
    try {
        $pdo = get_db_connection();
        
        $stmt = $pdo->prepare("
            SELECT * FROM visiteurs WHERE id = ?
        ");
        $stmt->execute([$visiteur_id]);
        
        return $stmt->fetch(PDO::FETCH_ASSOC);
        
    } catch (Exception $e) {
        error_log("Erreur récupération visiteur : " . $e->getMessage());
        return null;
    }
}

// Fonction pour rechercher des visiteurs
function search_visiteurs($criteria, $limit = 50) {
    try {
        $pdo = get_db_connection();
        
        $where_conditions = [];
        $params = [];
        
        if (!empty($criteria['search_term'])) {
            $search_term = '%' . $criteria['search_term'] . '%';
            $where_conditions[] = "(nom LIKE ? OR prenoms LIKE ? OR numero_identite LIKE ? OR telephone LIKE ? OR email LIKE ?)";
            $params = array_merge($params, [$search_term, $search_term, $search_term, $search_term, $search_term]);
        }
        
        if (!empty($criteria['type_identite'])) {
            $where_conditions[] = "type_identite = ?";
            $params[] = $criteria['type_identite'];
        }
        
        if (!empty($criteria['nom'])) {
            $where_conditions[] = "(nom LIKE ? OR prenoms LIKE ?)";
            $search_nom = '%' . $criteria['nom'] . '%';
            $params[] = $search_nom;
            $params[] = $search_nom;
        }
        
        if (!empty($criteria['numero_identite'])) {
            $where_conditions[] = "numero_identite LIKE ?";
            $params[] = '%' . $criteria['numero_identite'] . '%';
        }
        
        $where_clause = empty($where_conditions) ? '' : 'WHERE ' . implode(' AND ', $where_conditions);
        
        $sql = "
            SELECT v.*, 
                    COUNT(vi.id) as nb_visites,
                    MAX(vi.date_visite) as derniere_visite,
                    SUM(CASE WHEN vi.heure_sortie IS NULL AND vi.statut = 'en_cours' THEN 1 ELSE 0 END) as visites_en_cours
            FROM visiteurs v
            LEFT JOIN visites vi ON v.id = vi.visiteur_id
            {$where_clause}
            GROUP BY v.id
            ORDER BY v.nom, v.prenoms
            LIMIT ?
        ";
        
        $params[] = (int)$limit;
        $stmt = $pdo->prepare($sql);
        $stmt->execute($params);
        
        return $stmt->fetchAll(PDO::FETCH_ASSOC);
        
    } catch (Exception $e) {
        error_log("Erreur recherche visiteurs : " . $e->getMessage());
        return [];
    }
}

// Fonction pour recherche AJAX rapide - CORRIGÉE
function search_visiteurs_ajax($query) {
    try {
        $pdo = get_db_connection();
        
        $stmt = $pdo->prepare("
            SELECT id, nom, prenoms, numero_identite, type_identite, telephone, email
            FROM visiteurs 
            WHERE nom LIKE ? OR prenoms LIKE ? OR numero_identite LIKE ?
            ORDER BY nom, prenoms
            LIMIT 10
        ");
        
        $search_term = '%' . $query . '%';
        $stmt->execute([$search_term, $search_term, $search_term]);
        
        return $stmt->fetchAll(PDO::FETCH_ASSOC);
        
    } catch (Exception $e) {
        error_log("Erreur recherche AJAX visiteurs : " . $e->getMessage());
        return [];
    }
}

// Fonction pour obtenir tous les visiteurs avec pagination - CORRIGÉE
function get_all_visiteurs($page = 1, $per_page = 20, $order_by = 'nom') {
    try {
        $pdo = get_db_connection();
        $offset = ($page - 1) * $per_page;
        
        // Requête pour compter le total
        $count_stmt = $pdo->prepare("SELECT COUNT(*) FROM visiteurs");
        $count_stmt->execute();
        $total = $count_stmt->fetchColumn();
        
        // Validation de l'ordre
        $allowed_orders = ['nom', 'prenoms', 'date_creation', 'numero_identite'];
        if (!in_array($order_by, $allowed_orders)) {
            $order_by = 'nom';
        }
        
        // CORRECTION PRINCIPALE : Utiliser la syntaxe MySQL correcte
        $sql = "
            SELECT v.*, 
                    COALESCE(COUNT(vi.id), 0) as nb_visites,
                    MAX(vi.date_visite) as derniere_visite,
                    COALESCE(SUM(CASE WHEN vi.heure_sortie IS NULL AND vi.statut = 'en_cours' THEN 1 ELSE 0 END), 0) as visites_en_cours
            FROM visiteurs v
            LEFT JOIN visites vi ON v.id = vi.visiteur_id
            GROUP BY v.id, v.type_identite, v.numero_identite, v.nom, v.prenoms, v.telephone, v.email, v.adresse, v.date_creation
            ORDER BY v.{$order_by}, v.prenoms
            LIMIT {$per_page} OFFSET {$offset}
        ";
        
        $stmt = $pdo->prepare($sql);
        $stmt->execute();
        $visiteurs = $stmt->fetchAll(PDO::FETCH_ASSOC);
        
        return [
            'visiteurs' => $visiteurs,
            'total' => $total,
            'pages' => ceil($total / $per_page),
            'current_page' => $page
        ];
        
    } catch (Exception $e) {
        error_log("Erreur récupération visiteurs : " . $e->getMessage());
        return [
            'visiteurs' => [],
            'total' => 0,
            'pages' => 0,
            'current_page' => 1
        ];
    }
}

// Fonction pour obtenir l'historique complet des visites d'un visiteur
function get_visiteur_historique($visiteur_id, $limit = 50) {
    try {
        $pdo = get_db_connection();
        
        $stmt = $pdo->prepare("
            SELECT vi.id, vi.date_visite, vi.heure_entree, vi.heure_sortie, 
                    vi.type_visite, vi.observations, vi.statut, 
                    vi.agent_entree, vi.agent_sortie,
                    m.libelle as motif,
                    c.nom as correspondant_nom, c.prenoms as correspondant_prenoms,
                    c.departement, c.fonction
            FROM visites vi
            JOIN motifs_visite m ON vi.motif_id = m.id
            LEFT JOIN correspondants c ON vi.correspondant_id = c.id
            WHERE vi.visiteur_id = ?
            ORDER BY vi.date_visite DESC, vi.heure_entree DESC
            LIMIT ?
        ");
        
        $stmt->execute([$visiteur_id, $limit]);
        return $stmt->fetchAll(PDO::FETCH_ASSOC);
        
    } catch (Exception $e) {
        error_log("Erreur historique visiteur : " . $e->getMessage());
        return [];
    }
}

// Fonction pour obtenir les statistiques d'un visiteur
function get_visiteur_stats($visiteur_id) {
    try {
        $pdo = get_db_connection();
        
        // Statistiques générales
        $stmt = $pdo->prepare("
            SELECT 
                COUNT(*) as total_visites,
                COUNT(CASE WHEN heure_sortie IS NOT NULL THEN 1 END) as visites_terminees,
                COUNT(CASE WHEN heure_sortie IS NULL AND statut = 'en_cours' THEN 1 END) as visites_en_cours,
                COUNT(CASE WHEN statut = 'annulee' THEN 1 END) as visites_annulees,
                MIN(date_visite) as premiere_visite,
                MAX(date_visite) as derniere_visite,
                AVG(TIMESTAMPDIFF(MINUTE, 
                    CONCAT(date_visite, ' ', heure_entree), 
                    CONCAT(date_visite, ' ', heure_sortie)
                )) as duree_moyenne_minutes
            FROM visites 
            WHERE visiteur_id = ?
        ");
        $stmt->execute([$visiteur_id]);
        $stats_generales = $stmt->fetch(PDO::FETCH_ASSOC);
        
        // Motifs les plus fréquents
        $stmt = $pdo->prepare("
            SELECT m.libelle, COUNT(*) as nb_visites
            FROM visites v
            JOIN motifs_visite m ON v.motif_id = m.id
            WHERE v.visiteur_id = ?
            GROUP BY m.id, m.libelle
            ORDER BY nb_visites DESC
            LIMIT 5
        ");
        $stmt->execute([$visiteur_id]);
        $motifs_frequents = $stmt->fetchAll(PDO::FETCH_ASSOC);
        
        // Correspondants les plus fréquents
        $stmt = $pdo->prepare("
            SELECT c.nom, c.prenoms, c.departement, COUNT(*) as nb_visites
            FROM visites v
            JOIN correspondants c ON v.correspondant_id = c.id
            WHERE v.visiteur_id = ?
            GROUP BY c.id
            ORDER BY nb_visites DESC
            LIMIT 5
        ");
        $stmt->execute([$visiteur_id]);
        $correspondants_frequents = $stmt->fetchAll(PDO::FETCH_ASSOC);
        
        // Visites par mois (12 derniers mois)
        $stmt = $pdo->prepare("
            SELECT 
                DATE_FORMAT(date_visite, '%Y-%m') as mois,
                COUNT(*) as nb_visites
            FROM visites 
            WHERE visiteur_id = ? 
                AND date_visite >= DATE_SUB(CURDATE(), INTERVAL 12 MONTH)
            GROUP BY DATE_FORMAT(date_visite, '%Y-%m')
            ORDER BY mois
        ");
        $stmt->execute([$visiteur_id]);
        $visites_par_mois = $stmt->fetchAll(PDO::FETCH_ASSOC);
        
        return [
            'generales' => $stats_generales,
            'motifs_frequents' => $motifs_frequents,
            'correspondants_frequents' => $correspondants_frequents,
            'visites_par_mois' => $visites_par_mois
        ];
        
    } catch (Exception $e) {
        error_log("Erreur statistiques visiteur : " . $e->getMessage());
        return [
            'generales' => [],
            'motifs_frequents' => [],
            'correspondants_frequents' => [],
            'visites_par_mois' => []
        ];
    }
}

// Fonction pour supprimer un visiteur (soft delete ou vérification des contraintes)
function delete_visiteur($visiteur_id) {
    try {
        $pdo = get_db_connection();
        
        // Vérifier s'il y a des visites associées
        $stmt = $pdo->prepare("SELECT COUNT(*) FROM visites WHERE visiteur_id = ?");
        $stmt->execute([$visiteur_id]);
        $nb_visites = $stmt->fetchColumn();
        
        if ($nb_visites > 0) {
            return [
                'success' => false, 
                'message' => "Impossible de supprimer ce visiteur car il a {$nb_visites} visite(s) enregistrée(s)"
            ];
        }
        
        $stmt = $pdo->prepare("DELETE FROM visiteurs WHERE id = ?");
        $stmt->execute([$visiteur_id]);
        
        return [
            'success' => true, 
            'message' => 'Visiteur supprimé avec succès'
        ];
        
    } catch (Exception $e) {
        error_log("Erreur suppression visiteur : " . $e->getMessage());
        return [
            'success' => false, 
            'message' => 'Erreur lors de la suppression du visiteur'
        ];
    }
}

// Fonction pour valider les données d'un visiteur
function validate_visiteur_data($data, $visiteur_id = null) {
    $errors = [];
    
    // Validation du nom
    if (empty(trim($data['nom']))) {
        $errors[] = 'Le nom est obligatoire';
    } elseif (strlen(trim($data['nom'])) < 2) {
        $errors[] = 'Le nom doit contenir au moins 2 caractères';
    }
    
    // Validation des prénoms
    if (empty(trim($data['prenoms']))) {
        $errors[] = 'Le prénom est obligatoire';
    } elseif (strlen(trim($data['prenoms'])) < 2) {
        $errors[] = 'Le prénom doit contenir au moins 2 caractères';
    }
    
    // Validation du type d'identité
    $types_valides = array_keys(TYPES_IDENTITE);
    if (empty($data['type_identite']) || !in_array($data['type_identite'], $types_valides)) {
        $errors[] = 'Le type d\'identité est obligatoire';
    }
    
    // Validation du numéro d'identité
    if (empty(trim($data['numero_identite']))) {
        $errors[] = 'Le numéro d\'identité est obligatoire';
    } elseif (strlen(trim($data['numero_identite'])) < 3) {
        $errors[] = 'Le numéro d\'identité doit contenir au moins 3 caractères';
    }
    
    // Validation du téléphone (optionnel mais format si fourni)
    if (!empty($data['telephone'])) {
        $telephone = preg_replace('/[^0-9+\-\s()]/', '', $data['telephone']);
        if (strlen($telephone) < 8) {
            $errors[] = 'Le format du numéro de téléphone n\'est pas valide';
        }
    }
    
    // Validation de l'email (optionnel mais format si fourni)
    if (!empty($data['email']) && !filter_var($data['email'], FILTER_VALIDATE_EMAIL)) {
        $errors[] = 'Le format de l\'email n\'est pas valide';
    }
    
    return $errors;
}

// Fonction pour dupliquer un visiteur (copie avec nouveau numéro d'identité)
function duplicate_visiteur($visiteur_id) {
    try {
        $visiteur = get_visiteur_by_id($visiteur_id);
        if (!$visiteur) {
            return ['success' => false, 'message' => 'Visiteur introuvable'];
        }
        
        // Créer une copie avec un nouveau numéro d'identité
        $new_data = $visiteur;
        unset($new_data['id'], $new_data['date_creation']);
        $new_data['numero_identite'] = $new_data['numero_identite'] . '_COPIE';
        $new_data['nom'] = $new_data['nom'] . ' (Copie)';
        
        return create_visiteur($new_data);
        
    } catch (Exception $e) {
        error_log("Erreur duplication visiteur : " . $e->getMessage());
        return ['success' => false, 'message' => 'Erreur lors de la duplication'];
    }
}

// Fonction pour obtenir les visiteurs fréquents (plus de X visites)
function get_visiteurs_frequents($min_visites = 5, $limit = 20) {
    try {
        $pdo = get_db_connection();
        
        $stmt = $pdo->prepare("
            SELECT v.*, COUNT(vi.id) as nb_visites,
                    MAX(vi.date_visite) as derniere_visite,
                    MIN(vi.date_visite) as premiere_visite
            FROM visiteurs v
            JOIN visites vi ON v.id = vi.visiteur_id
            GROUP BY v.id
            HAVING nb_visites >= ?
            ORDER BY nb_visites DESC, derniere_visite DESC
            LIMIT ?
        ");
        
        $stmt->execute([$min_visites, $limit]);
        return $stmt->fetchAll(PDO::FETCH_ASSOC);
        
    } catch (Exception $e) {
        error_log("Erreur visiteurs fréquents : " . $e->getMessage());
        return [];
    }
}
?>