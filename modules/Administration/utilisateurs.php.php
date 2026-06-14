<?php
// On inclut les fichiers de configuration et les fonctions
require_once '../../config/config.php';

// Vérifier si l'utilisateur est connecté et a les privilèges d'administrateur
if (!is_logged_in() || !has_permission('admin')) {
    redirect('../auth/login.php');
}

$page_title = 'Gestion des Utilisateurs';
$errors = [];
$success_message = '';

// Traiter la soumission du formulaire
if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    // Collecter et nettoyer les données du formulaire
    $nom = trim($_POST['nom'] ?? '');
    $prenoms = trim($_POST['prenoms'] ?? '');
    $nom_utilisateur = trim($_POST['nom_utilisateur'] ?? '');
    $mot_de_passe = $_POST['mot_de_passe'] ?? '';
    $mot_de_passe_confirm = $_POST['mot_de_passe_confirm'] ?? '';
    $role = trim($_POST['role'] ?? '');
    $poste = trim($_POST['poste'] ?? '');

    // Validation
    if (empty($nom) || empty($prenoms) || empty($nom_utilisateur) || empty($mot_de_passe) || empty($role) || empty($poste)) {
        $errors[] = "Tous les champs sont obligatoires.";
    }
    if ($mot_de_passe !== $mot_de_passe_confirm) {
        $errors[] = "Les mots de passe ne correspondent pas.";
    }
    if (strlen($mot_de_passe) < 6) {
        $errors[] = "Le mot de passe doit contenir au moins 6 caractères.";
    }

    // S'il n'y a pas d'erreurs, insérer l'utilisateur dans la base de données
    if (empty($errors)) {
        // Hacher le mot de passe
        $hashed_password = password_hash($mot_de_passe, PASSWORD_DEFAULT);

        try {
            // Insérer l'utilisateur
            $db_conn = get_db_connection();
            $stmt = $db_conn->prepare("
                INSERT INTO utilisateurs (nom, prenoms, nom_utilisateur, mot_de_passe, role, poste)
                VALUES (?, ?, ?, ?, ?, ?)
            ");
            $stmt->execute([
                $nom,
                $prenoms,
                $nom_utilisateur,
                $hashed_password,
                $role,
                $poste
            ]);

            set_flash_message('success', 'Utilisateur créé avec succès !');
            redirect('utilisateurs.php');
        } catch (PDOException $e) {
            $errors[] = "Erreur de base de données : " . $e->getMessage();
        }
    }
}

$css_path = '../../assets/css/';
$base_url = '../../';
$modules_path = '../';

include '../../includes/header.php';
?>

<div class="row mb-4">
    <div class="col-md-8">
        <h1 class="h3 mb-2 text-primary">
            <i class="bi bi-person-plus-fill"></i> <?php echo $page_title; ?>
        </h1>
        <p class="text-muted mb-0">
            Créez de nouveaux comptes utilisateurs et gérez leurs privilèges.
        </p>
    </div>
</div>

---

<?php if (!empty($errors)): ?>
<div class="alert alert-danger" role="alert">
    <i class="bi bi-exclamation-triangle-fill me-2"></i>
    <strong>Erreur !</strong>
    <ul>
        <?php foreach ($errors as $error): ?>
            <li><?php echo htmlspecialchars($error); ?></li>
        <?php endforeach; ?>
    </ul>
</div>
<?php endif; ?>

<?php if ($success_message): ?>
<div class="alert alert-success alert-dismissible fade show" role="alert">
    <i class="bi bi-check-circle-fill me-2"></i>
    <?php echo htmlspecialchars($success_message); ?>
    <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
</div>
<?php endif; ?>

<div class="card shadow-sm">
    <div class="card-header bg-primary text-white">
        <h5 class="card-title mb-0">Créer un nouvel utilisateur</h5>
    </div>
    <div class="card-body">
        <form action="" method="POST">
            <div class="row g-3">
                <div class="col-md-6">
                    <label for="nom" class="form-label">Nom de famille</label>
                    <input type="text" class="form-control" id="nom" name="nom" required>
                </div>
                <div class="col-md-6">
                    <label for="prenoms" class="form-label">Prénoms</label>
                    <input type="text" class="form-control" id="prenoms" name="prenoms" required>
                </div>
                <div class="col-md-6">
                    <label for="nom_utilisateur" class="form-label">Nom d'utilisateur</label>
                    <input type="text" class="form-control" id="nom_utilisateur" name="nom_utilisateur" required>
                </div>
                <div class="col-md-6">
                    <label for="mot_de_passe" class="form-label">Mot de passe</label>
                    <input type="password" class="form-control" id="mot_de_passe" name="mot_de_passe" required>
                </div>
                <div class="col-md-6">
                    <label for="mot_de_passe_confirm" class="form-label">Confirmer le mot de passe</label>
                    <input type="password" class="form-control" id="mot_de_passe_confirm" name="mot_de_passe_confirm" required>
                </div>
                <div class="col-md-6">
                    <label for="role" class="form-label">Rôle (Privilèges)</label>
                    <select class="form-select" id="role" name="role" required>
                        <option value="visiteur">Visiteur</option>
                        <option value="admin">Administrateur</option>
                        <option value="super-admin">Super Administrateur</option>
                    </select>
                </div>
                <div class="col-md-6">
                    <label for="poste" class="form-label">Poste</label>
                    <input type="text" class="form-control" id="poste" name="poste" required>
                </div>
            </div>
            <div class="mt-4 text-center">
                <button type="submit" class="btn btn-primary">
                    <i class="bi bi-person-plus"></i> Créer l'utilisateur
                </button>
            </div>
        </form>
    </div>
</div>

<?php include '../../includes/footer.php'; ?>