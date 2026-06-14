<?php
require_once '../../config/config.php';

// Fonction pour authentifier un utilisateur
function authenticate_user($nom_utilisateur, $mot_de_passe) {
    try {
        $pdo = get_db_connection();
        
        $stmt = $pdo->prepare("
            SELECT id, nom_utilisateur, mot_de_passe, nom, prenoms, role, poste, actif 
            FROM utilisateurs 
            WHERE nom_utilisateur = ? AND actif = 1
        ");
        $stmt->execute([$nom_utilisateur]);
        $user = $stmt->fetch(PDO::FETCH_ASSOC);
        
        if ($user && password_verify($mot_de_passe, $user['mot_de_passe'])) {
            // Mettre à jour la dernière connexion
            $update_stmt = $pdo->prepare("
                UPDATE utilisateurs 
                SET derniere_connexion = NOW() 
                WHERE id = ?
            ");
            $update_stmt->execute([$user['id']]);
            
            // Créer la session
            $_SESSION['user_id'] = $user['id'];
            $_SESSION['nom_utilisateur'] = $user['nom_utilisateur'];
            $_SESSION['nom'] = $user['nom'];
            $_SESSION['prenoms'] = $user['prenoms'];
            $_SESSION['role'] = $user['role'];
            $_SESSION['poste'] = $user['poste'];
            $_SESSION['login_time'] = time();
            
            return true;
        }
        
        return false;
        
    } catch (Exception $e) {
        error_log("Erreur d'authentification : " . $e->getMessage());
        return false;
    }
}

// Fonction pour créer un utilisateur (pour l'admin)
function create_user($data) {
    try {
        $pdo = get_db_connection();
        
        // Vérifier si le nom d'utilisateur existe déjà
        $check_stmt = $pdo->prepare("SELECT id FROM utilisateurs WHERE nom_utilisateur = ?");
        $check_stmt->execute([$data['nom_utilisateur']]);
        
        if ($check_stmt->fetch()) {
            return ['success' => false, 'message' => 'Ce nom d\'utilisateur existe déjà'];
        }
        
        $stmt = $pdo->prepare("
            INSERT INTO utilisateurs (nom_utilisateur, mot_de_passe, nom, prenoms, role, poste)
            VALUES (?, ?, ?, ?, ?, ?)
        ");
        
        $hashed_password = password_hash($data['mot_de_passe'], PASSWORD_DEFAULT);
        
        $stmt->execute([
            $data['nom_utilisateur'],
            $hashed_password,
            $data['nom'],
            $data['prenoms'],
            $data['role'],
            $data['poste']
        ]);
        
        return ['success' => true, 'message' => 'Utilisateur créé avec succès'];
        
    } catch (Exception $e) {
        error_log("Erreur création utilisateur : " . $e->getMessage());
        return ['success' => false, 'message' => 'Erreur lors de la création de l\'utilisateur'];
    }
}

// Fonction pour déconnecter l'utilisateur
function logout_user() {
    session_destroy();
    redirect('../../index.php');
}

// Fonction pour vérifier la validité de la session
function check_session_validity() {
    if (!is_logged_in()) {
        return false;
    }
    
    // Vérifier le timeout de session
    if (isset($_SESSION['login_time']) && (time() - $_SESSION['login_time']) > SESSION_TIMEOUT) {
        session_destroy();
        return false;
    }
    
    return true;
}

// Fonction pour obtenir tous les utilisateurs (pour l'admin)
function get_all_users() {
    try {
        $pdo = get_db_connection();
        $stmt = $pdo->prepare("
            SELECT id, nom_utilisateur, nom, prenoms, role, poste, actif, 
                   derniere_connexion, date_creation
            FROM utilisateurs 
            ORDER BY nom, prenoms
        ");
        $stmt->execute();
        return $stmt->fetchAll(PDO::FETCH_ASSOC);
        
    } catch (Exception $e) {
        error_log("Erreur récupération utilisateurs : " . $e->getMessage());
        return [];
    }
}
?>