<?php
require_once __DIR__ . '/../../config/config.php';
require_once __DIR__ . '/visiteurs_functions.php';

// Vérifier la session
if (!is_logged_in()) {
    redirect('../../modules/auth/login.php');
}

$page_title = 'Modifier un visiteur';
$errors = [];
$success_message = '';
$visiteur = null;

// Vérifier si un ID de visiteur est fourni
if (!isset($_GET['id']) || !is_numeric($_GET['id'])) {
    // Si la requête est une soumission de formulaire, l'ID est dans $_POST
    $visiteur_id = isset($_POST['visiteur_id']) ? (int)$_POST['visiteur_id'] : 0;
} else {
    // Sinon, l'ID est dans l'URL
    $visiteur_id = (int)$_GET['id'];
}

// Récupérer les données du visiteur pour pré-remplir le formulaire
if ($visiteur_id > 0) {
    $visiteur = get_visiteur_by_id($visiteur_id);
    if (!$visiteur) {
        $errors[] = "Visiteur non trouvé.";
        $visiteur_id = 0; // Réinitialiser pour ne pas tenter de mettre à jour un visiteur inexistant
    }
} else {
    $errors[] = "ID de visiteur manquant ou invalide.";
}

// Traiter la soumission du formulaire
if ($_SERVER['REQUEST_METHOD'] === 'POST' && $visiteur_id > 0) {
    // Collecter les données du formulaire et utiliser l'opérateur de coalescence pour éviter les valeurs nulles
    $nom = trim($_POST['nom'] ?? '');
    $prenoms = trim($_POST['prenoms'] ?? '');
    $type_identite = trim($_POST['type_identite'] ?? '');
    $numero_identite = trim($_POST['numero_identite'] ?? '');
    $telephone = trim($_POST['telephone'] ?? '');
    $email = trim($_POST['email'] ?? '');
    $adresse = trim($_POST['adresse'] ?? ''); // <-- LIGNE AJOUTÉE

    // Validation des données
    if (empty($nom)) {
        $errors[] = "Le champ 'Nom de famille' est obligatoire.";
    }
    if (empty($prenoms)) {
        $errors[] = "Le champ 'Prénoms' est obligatoire.";
    }
    if (empty($telephone)) {
        $errors[] = "Le champ 'Téléphone' est obligatoire.";
    }
    if (!empty($email) && !filter_var($email, FILTER_VALIDATE_EMAIL)) {
        $errors[] = "L'adresse email n'est pas valide.";
    }
    // Validation de l'adresse est facultative, mais vous pouvez l'ajouter ici si besoin

    // Si aucune erreur de validation
    if (empty($errors)) {
        try {
            $updated = update_visiteur(
                $visiteur_id,
                $nom,
                $prenoms,
                $type_identite,
                $numero_identite,
                $telephone,
                $email,
                $adresse // <-- VARIABLE AJOUTÉE
            );

            if ($updated) {
                $success_message = "Les informations du visiteur ont été mises à jour avec succès.";
                // Recharger les données du visiteur après la mise à jour
                $visiteur = get_visiteur_by_id($visiteur_id);
            } else {
                $errors[] = "Une erreur est survenue lors de la mise à jour des informations.";
            }
        } catch (PDOException $e) {
            $errors[] = "Erreur de base de données : " . $e->getMessage();
        }
    }
}

$css_path = '../../assets/css/';
$js_path = '../../assets/js/';
$base_url = '../../';
$modules_path = '../';

include '../../includes/header.php';
?>

<div class="row mb-4">
    <div class="col-md-8">
        <h1 class="h3 mb-2 text-primary">
            <i class="bi bi-pencil"></i> <?php echo $page_title; ?>
        </h1>
        <p class="text-muted mb-0">
            Modifier les informations d'un visiteur existant.
        </p>
    </div>
    <div class="col-md-4 text-md-end">
        <a href="index.php" class="btn btn-outline-secondary">
            <i class="bi bi-arrow-left"></i> Retour à la liste
        </a>
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

<?php if ($visiteur): ?>
<div class="card">
    <div class="card-header bg-primary text-white">
        <h5 class="card-title mb-0">
            <i class="bi bi-person-fill"></i> Informations du visiteur
        </h5>
    </div>
    <div class="card-body">
        <form action="modifier.php?id=<?php echo $visiteur_id; ?>" method="POST">
            <input type="hidden" name="visiteur_id" value="<?php echo $visiteur_id; ?>">
            <div class="row g-3">
                <div class="col-md-6">
                    <label for="nom" class="form-label">Nom de famille <span class="text-danger">*</span></label>
                    <div class="input-group">
                        <span class="input-group-text"><i class="bi bi-person"></i></span>
                        <input type="text" class="form-control" id="nom" name="nom"
                               value="<?php echo htmlspecialchars($visiteur['nom']); ?>" required>
                    </div>
                </div>
                <div class="col-md-6">
                    <label for="prenoms" class="form-label">Prénoms <span class="text-danger">*</span></label>
                    <div class="input-group">
                        <span class="input-group-text"><i class="bi bi-person"></i></span>
                        <input type="text" class="form-control" id="prenoms" name="prenoms"
                               value="<?php echo htmlspecialchars($visiteur['prenoms']); ?>" required>
                    </div>
                </div>
                <div class="col-md-6">
                    <label for="type_identite" class="form-label">Type de pièce d'identité</label>
                    <div class="input-group">
                        <span class="input-group-text"><i class="bi bi-id-card"></i></span>
                        <select class="form-select" id="type_identite" name="type_identite">
                            <option value="">-- Facultatif --</option>
                            <option value="CNI" <?php echo ($visiteur['type_identite'] ?? '') == 'CNI' ? 'selected' : ''; ?>>CNI</option>
                            <option value="PASSPORT" <?php echo ($visiteur['type_identite'] ?? '') == 'PASSPORT' ? 'selected' : ''; ?>>Passeport</option>
                            <option value="PERMIS" <?php echo ($visiteur['type_identite'] ?? '') == 'PERMIS' ? 'selected' : ''; ?>>Permis de conduire</option>
                            <option value="AUTRE" <?php echo ($visiteur['type_identite'] ?? '') == 'AUTRE' ? 'selected' : ''; ?>>Autre</option>
                        </select>
                    </div>
                </div>
                <div class="col-md-6">
                    <label for="numero_identite" class="form-label">Numéro de la pièce</label>
                    <div class="input-group">
                        <span class="input-group-text"><i class="bi bi-hash"></i></span>
                        <input type="text" class="form-control" id="numero_identite" name="numero_identite"
                               value="<?php echo htmlspecialchars($visiteur['numero_identite'] ?? ''); ?>">
                    </div>
                </div>
                <div class="col-md-6">
                    <label for="telephone" class="form-label">Téléphone <span class="text-danger">*</span></label>
                    <div class="input-group">
                        <span class="input-group-text"><i class="bi bi-telephone"></i></span>
                        <input type="tel" class="form-control" id="telephone" name="telephone"
                               value="<?php echo htmlspecialchars($visiteur['telephone'] ?? ''); ?>" required>
                    </div>
                </div>
                <div class="col-md-6">
                    <label for="email" class="form-label">Email</label>
                    <div class="input-group">
                        <span class="input-group-text"><i class="bi bi-envelope"></i></span>
                        <input type="email" class="form-control" id="email" name="email"
                               value="<?php echo htmlspecialchars($visiteur['email'] ?? ''); ?>">
                    </div>
                </div>
                <div class="col-md-12">
                    <label for="adresse" class="form-label">Adresse</label>
                    <div class="input-group">
                        <span class="input-group-text"><i class="bi bi-geo-alt"></i></span>
                        <textarea class="form-control" id="adresse" name="adresse" rows="3"><?php echo htmlspecialchars($visiteur['adresse'] ?? ''); ?></textarea>
                    </div>
                </div>
            </div>
            <div class="mt-4 d-flex justify-content-between">
                <a href="index.php" class="btn btn-secondary">
                    <i class="bi bi-x"></i> Annuler
                </a>
                <button type="submit" class="btn btn-primary">
                    <i class="bi bi-check-circle"></i> Enregistrer les modifications
                </button>
            </div>
        </form>
    </div>
</div>
<?php endif; ?>

<?php include '../../includes/footer.php'; ?>
