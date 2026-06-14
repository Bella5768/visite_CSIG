<?php
require_once __DIR__.'/../../config/config.php';

// Fonction pour créer une nouvelle visite
function create_visite($data) {
    try {
        $pdo = get_db_connection();
        
        $stmt = $pdo->prepare("
            INSERT INTO visites (visiteur_id, motif_id, correspondant_id, type_visite, 
                               date_visite, heure_entree, observations, agent_entree)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ");
        
        $stmt->execute([
            $data['visiteur_id'],
            $data['motif_id'],
            $data['correspondant_id'] ?: null,
            $data['type_visite'],
            $data['date_visite'],
            $data['heure_entree'],
            $data['observations'] ?: null,
            $data['agent_entree']
        ]);
        
        return ['success' => true, 'visite_id' => $pdo->lastInsertId(), 'message' => 'Visite enregistrée avec succès'];
        
    } catch (Exception $e) {
        error_log("Erreur création visite : " . $e->getMessage());
        return ['success' => false, 'message' => 'Erreur lors de l\'enregistrement de la visite'];
    }
}

// Fonction pour enregistrer la sortie d'un visiteur
function record_sortie($visite_id, $agent_sortie, $observations = null) {
    try {
        $pdo = get_db_connection();
        
        $stmt = $pdo->prepare("
            UPDATE visites 
            SET heure_sortie = NOW(), 
                agent_sortie = ?, 
                statut = 'terminee',
                observations = CONCAT(COALESCE(observations, ''), CASE WHEN observations IS NOT NULL THEN '\n--- Sortie ---\n' ELSE '' END, COALESCE(?, ''))
            WHERE id = ? AND heure_sortie IS NULL
        ");
        
        $stmt->execute([$agent_sortie, $observations, $visite_id]);
        
        if ($stmt->rowCount() > 0) {
            return ['success' => true, 'message' => 'Sortie enregistrée avec succès'];
        } else {
            return ['success' => false, 'message' => 'Visite non trouvée ou sortie déjà enregistrée'];
        }
        
    } catch (Exception $e) {
        error_log("Erreur enregistrement sortie : " . $e->getMessage());
        return ['success' => false, 'message' => 'Erreur lors de l\'enregistrement de la sortie'];
    }
}

// Fonction pour obtenir les visites du jour
function get_visites_jour($date = null) {
    try {
        $pdo = get_db_connection();
        
        if (!$date) {
            $date = date('Y-m-d');
        }
        
        $stmt = $pdo->prepare("
            SELECT v.id, v.date_visite, v.heure_entree, v.heure_sortie, v.type_visite, 
                   v.observations, v.statut, v.agent_entree, v.agent_sortie,
                   vi.nom, vi.prenoms, vi.numero_identite, vi.type_identite, vi.telephone,
                   m.libelle as motif,
                   c.nom as correspondant_nom, c.prenoms as correspondant_prenoms, 
                   c.departement, c.fonction
            FROM visites v
            JOIN visiteurs vi ON v.visiteur_id = vi.id
            JOIN motifs_visite m ON v.motif_id = m.id
            LEFT JOIN correspondants c ON v.correspondant_id = c.id
            WHERE DATE(v.date_visite) = ?
            ORDER BY v.heure_entree DESC
        ");
        
        $stmt->execute([$date]);
        return $stmt->fetchAll(PDO::FETCH_ASSOC);
        
    } catch (Exception $e) {
        error_log("Erreur récupération visites du jour : " . $e->getMessage());
        return [];
    }
}

// Fonction pour obtenir les visites en cours (pas encore sorties)
function get_visites_en_cours($date = null) {
    try {
        $pdo = get_db_connection();
        
        if (!$date) {
            $date = date('Y-m-d');
        }
        
        $stmt = $pdo->prepare("
            SELECT v.id, v.date_visite, v.heure_entree, v.type_visite, 
                   v.observations, v.agent_entree,
                   vi.nom, vi.prenoms, vi.numero_identite, vi.type_identite, vi.telephone,
                   m.libelle as motif,
                   c.nom as correspondant_nom, c.prenoms as correspondant_prenoms, 
                   c.departement, c.fonction
            FROM visites v
            JOIN visiteurs vi ON v.visiteur_id = vi.id
            JOIN motifs_visite m ON v.motif_id = m.id
            LEFT JOIN correspondants c ON v.correspondant_id = c.id
            WHERE DATE(v.date_visite) = ? AND v.heure_sortie IS NULL AND v.statut = 'en_cours'
            ORDER BY v.heure_entree ASC
        ");
        
        $stmt->execute([$date]);
        return $stmt->fetchAll(PDO::FETCH_ASSOC);
        
    } catch (Exception $e) {
        error_log("Erreur récupération visites en cours : " . $e->getMessage());
        return [];
    }
}

// Fonction pour rechercher des visites
function search_visites($criteria) {
    try {
        $pdo = get_db_connection();
        
        $where_conditions = [];
        $params = [];
        
        if (!empty($criteria['numero_identite'])) {
            $where_conditions[] = "vi.numero_identite LIKE ?";
            $params[] = '%' . $criteria['numero_identite'] . '%';
        }
        
        if (!empty($criteria['nom'])) {
            $where_conditions[] = "(vi.nom LIKE ? OR vi.prenoms LIKE ?)";
            $params[] = '%' . $criteria['nom'] . '%';
            $params[] = '%' . $criteria['nom'] . '%';
        }
        
        if (!empty($criteria['date_debut'])) {
            $where_conditions[] = "DATE(v.date_visite) >= ?";
            $params[] = $criteria['date_debut'];
        }
        
        if (!empty($criteria['date_fin'])) {
            $where_conditions[] = "DATE(v.date_visite) <= ?";
            $params[] = $criteria['date_fin'];
        }
        
        if (!empty($criteria['motif_id'])) {
            $where_conditions[] = "v.motif_id = ?";
            $params[] = $criteria['motif_id'];
        }
        
        if (!empty($criteria['correspondant_id'])) {
            $where_conditions[] = "v.correspondant_id = ?";
            $params[] = $criteria['correspondant_id'];
        }
        
        if (!empty($criteria['statut'])) {
            $where_conditions[] = "v.statut = ?";
            $params[] = $criteria['statut'];
        }
        
        $where_clause = empty($where_conditions) ? '' : 'WHERE ' . implode(' AND ', $where_conditions);
        
        $sql = "
            SELECT v.id, v.date_visite, v.heure_entree, v.heure_sortie, v.type_visite, 
                   v.observations, v.statut, v.agent_entree, v.agent_sortie,
                   vi.nom, vi.prenoms, vi.numero_identite, vi.type_identite, vi.telephone,
                   m.libelle as motif,
                   c.nom as correspondant_nom, c.prenoms as correspondant_prenoms, 
                   c.departement, c.fonction
            FROM visites v
            JOIN visiteurs vi ON v.visiteur_id = vi.id
            JOIN motifs_visite m ON v.motif_id = m.id
            LEFT JOIN correspondants c ON v.correspondant_id = c.id
            {$where_clause}
            ORDER BY v.date_visite DESC, v.heure_entree DESC
            LIMIT 100
        ";
        
        $stmt = $pdo->prepare($sql);
        $stmt->execute($params);
        return $stmt->fetchAll(PDO::FETCH_ASSOC);
        
    } catch (Exception $e) {
        error_log("Erreur recherche visites : " . $e->getMessage());
        return [];
    }
}

// Fonction pour obtenir l'historique des visites d'un visiteur
function get_historique_visiteur($visiteur_id, $limit = 20) {
    try {
        $pdo = get_db_connection();
        
        $stmt = $pdo->prepare("
            SELECT v.id, v.date_visite, v.heure_entree, v.heure_sortie, v.type_visite, 
                   v.observations, v.statut, v.agent_entree, v.agent_sortie,
                   m.libelle as motif,
                   c.nom as correspondant_nom, c.prenoms as correspondant_prenoms, 
                   c.departement, c.fonction
            FROM visites v
            JOIN motifs_visite m ON v.motif_id = m.id
            LEFT JOIN correspondants c ON v.correspondant_id = c.id
            WHERE v.visiteur_id = ?
            ORDER BY v.date_visite DESC, v.heure_entree DESC
            LIMIT ?
        ");
        
        $stmt->execute([$visiteur_id, $limit]);
        return $stmt->fetchAll(PDO::FETCH_ASSOC);
        
    } catch (Exception $e) {
        error_log("Erreur historique visiteur : " . $e->getMessage());
        return [];
    }
}

// Fonction pour obtenir tous les motifs de visite actifs
function get_motifs_visite() {
    try {
        $pdo = get_db_connection();
        
        $stmt = $pdo->prepare("
            SELECT id, libelle, description
            FROM motifs_visite 
            WHERE actif = 1 
            ORDER BY libelle
        ");
        
        $stmt->execute();
        return $stmt->fetchAll(PDO::FETCH_ASSOC);
        
    } catch (Exception $e) {
        error_log("Erreur récupération motifs : " . $e->getMessage());
        return [];
    }
}

// Fonction pour obtenir tous les correspondants actifs
function get_correspondants() {
    try {
        $pdo = get_db_connection();
        
        $stmt = $pdo->prepare("
            SELECT id, nom, prenoms, fonction, departement, telephone, email
            FROM correspondants 
            WHERE actif = 1 
            ORDER BY nom, prenoms
        ");
        
        $stmt->execute();
        return $stmt->fetchAll(PDO::FETCH_ASSOC);
        
    } catch (Exception $e) {
        error_log("Erreur récupération correspondants : " . $e->getMessage());
        return [];
    }
}

// Fonction pour obtenir une visite par ID
function get_visite_by_id($visite_id) {
    try {
        $pdo = get_db_connection();
        
        $stmt = $pdo->prepare("
            SELECT v.*, 
                   vi.nom, vi.prenoms, vi.numero_identite, vi.type_identite, vi.telephone,
                   m.libelle as motif,
                   c.nom as correspondant_nom, c.prenoms as correspondant_prenoms, 
                   c.departement, c.fonction
            FROM visites v
            JOIN visiteurs vi ON v.visiteur_id = vi.id
            JOIN motifs_visite m ON v.motif_id = m.id
            LEFT JOIN correspondants c ON v.correspondant_id = c.id
            WHERE v.id = ?
        ");
        
        $stmt->execute([$visite_id]);
        return $stmt->fetch(PDO::FETCH_ASSOC);
        
    } catch (Exception $e) {
        error_log("Erreur récupération visite : " . $e->getMessage());
        return null;
    }
}

// Fonction pour modifier une visite
function update_visite($visite_id, $data) {
    try {
        $pdo = get_db_connection();
        
        $stmt = $pdo->prepare("
            UPDATE visites 
            SET motif_id = ?, correspondant_id = ?, observations = ?
            WHERE id = ?
        ");
        
        $stmt->execute([
            $data['motif_id'],
            $data['correspondant_id'] ?: null,
            $data['observations'],
            $visite_id
        ]);
        
        return ['success' => true, 'message' => 'Visite modifiée avec succès'];
        
    } catch (Exception $e) {
        error_log("Erreur modification visite : " . $e->getMessage());
        return ['success' => false, 'message' => 'Erreur lors de la modification'];
    }
}

// Fonction pour annuler une visite
function cancel_visite($visite_id, $raison) {
    try {
        $pdo = get_db_connection();
        
        $stmt = $pdo->prepare("
            UPDATE visites 
            SET statut = 'annulee', 
                observations = CONCAT(COALESCE(observations, ''), '\n--- ANNULÉE ---\nRaison: ', ?)
            WHERE id = ? AND statut = 'en_cours'
        ");
        
        $stmt->execute([$raison, $visite_id]);
        
        if ($stmt->rowCount() > 0) {
            return ['success' => true, 'message' => 'Visite annulée avec succès'];
        } else {
            return ['success' => false, 'message' => 'Impossible d\'annuler cette visite'];
        }
        
    } catch (Exception $e) {
        error_log("Erreur annulation visite : " . $e->getMessage());
        return ['success' => false, 'message' => 'Erreur lors de l\'annulation'];
    }
}

// Fonction pour calculer la durée d'une visite
function calculate_duree_visite($heure_entree, $heure_sortie) {
    if (!$heure_sortie) {
        return 'En cours';
    }
    
    $entree = new DateTime($heure_entree);
    $sortie = new DateTime($heure_sortie);
    $diff = $entree->diff($sortie);
    
    $heures = $diff->h;
    $minutes = $diff->i;
    
    if ($heures > 0) {
        return $heures . 'h ' . $minutes . 'min';
    } else {
        return $minutes . 'min';
    }
}

// 🔹 Fonction corrigée pour le rapport journalier
function get_daily_report() {
    try {
        $pdo = get_db_connection();
        
        $stmt = $pdo->prepare("
            SELECT 
                v.id, 
                v.heure_entree, 
                v.heure_sortie, 
                vis.prenoms, 
                vis.nom, 
                vis.telephone,
                m.libelle AS motif_libelle,
                c.prenoms AS correspondant_prenoms,
                c.nom AS correspondant_nom
            FROM visites v
            JOIN visiteurs vis ON v.visiteur_id = vis.id
            JOIN motifs_visite m ON v.motif_id = m.id
            LEFT JOIN correspondants c ON v.correspondant_id = c.id
            WHERE DATE(v.heure_entree) = CURDATE()
            ORDER BY v.heure_entree DESC
        ");
        
        $stmt->execute();
        
        return $stmt->fetchAll(PDO::FETCH_ASSOC);
        
    } catch (Exception $e) {
        error_log("Erreur lors de la récupération du rapport quotidien : " . $e->getMessage());
        return [];
    }
}
?>
