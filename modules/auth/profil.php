<?php
// On inclut les fichiers de configuration et les fonctions
require_once '../../config/config.php';

// Vérifier si l'utilisateur est connecté
if (!is_logged_in()) {
    redirect('login.php');
}

$page_title = 'Mon Profil';
$errors = [];
$success_message = '';

// Récupérer l'utilisateur actuellement connecté
$user = get_current_user2();

// Traiter la soumission du formulaire de mise à jour du profil
if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    // Collecter et nettoyer les données du formulaire
    $nom = trim($_POST['nom'] ?? '');
    $prenoms = trim($_POST['prenoms'] ?? '');
    $poste = trim($_POST['poste'] ?? '');

    // Validation
    if (empty($nom) || empty($prenoms) || empty($poste)) {
        $errors[] = "Le nom, les prénoms et le poste sont obligatoires.";
    }

    // Gérer le téléchargement de la photo de profil
    $photo_de_profil = $user['photo_de_profil'] ?? null;

    if (isset($_FILES['photo']) && $_FILES['photo']['error'] === UPLOAD_ERR_OK) {
        $file_tmp_path = $_FILES['photo']['tmp_name'];
        $file_name = $_FILES['photo']['name'];
        $file_size = $_FILES['photo']['size'];
        $file_extension = strtolower(pathinfo($file_name, PATHINFO_EXTENSION));

        // Extensions autorisées
        $allowed_extensions = ['jpg', 'jpeg', 'png', 'gif'];
        if (!in_array($file_extension, $allowed_extensions)) {
            $errors[] = "Le format de fichier n'est pas autorisé. (JPG, JPEG, PNG, GIF)";
        }
        if ($file_size > 5000000) { // 5 Mo
            $errors[] = "La taille de l'image ne doit pas dépasser 5 Mo.";
        }

        if (empty($errors)) {
            $upload_dir = __DIR__ . '/../../assets/uploads/profils/';
            if (!is_dir($upload_dir)) {
                mkdir($upload_dir, 0777, true);
            }

            $new_file_name = uniqid('profil_', true) . '.' . $file_extension;
            $upload_path = $upload_dir . $new_file_name;

            if (move_uploaded_file($file_tmp_path, $upload_path)) {
                // Supprimer l’ancienne photo si elle existe
                if (!empty($user['photo_de_profil'])) {
                    $old_photo_path = __DIR__ . '/../../' . $user['photo_de_profil'];
                    if (file_exists($old_photo_path) && is_file($old_photo_path)) {
                        unlink($old_photo_path);
                    }
                }
                // Sauvegarder le chemin relatif pour affichage
                $photo_de_profil = 'assets/uploads/profils/' . $new_file_name;
            } else {
                $errors[] = "Erreur lors du téléchargement de l'image.";
            }
        }
    }

    // Si aucune erreur → mise à jour en base
    if (empty($errors)) {
        try {
            $db_conn = get_db_connection();
            $stmt = $db_conn->prepare("
                UPDATE utilisateurs
                SET nom = ?, prenoms = ?, poste = ?, photo_de_profil = ?
                WHERE id = ?
            ");
            $stmt->execute([
                $nom,
                $prenoms,
                $poste,
                $photo_de_profil,
                $user['id']
            ]);

            // Mettre à jour la session
            $_SESSION['user_data']['nom'] = $nom;
            $_SESSION['user_data']['prenoms'] = $prenoms;
            $_SESSION['user_data']['poste'] = $poste;
            $_SESSION['user_data']['photo_de_profil'] = $photo_de_profil;

            set_flash_message('success', 'Votre profil a été mis à jour avec succès !');
            redirect('profil.php');
        } catch (PDOException $e) {
            $errors[] = "Erreur base de données : " . $e->getMessage();
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
            <i class="bi bi-person"></i> <?php echo $page_title; ?>
        </h1>
        <p class="text-muted mb-0">
            Affichez et mettez à jour les informations de votre profil.
        </p>
    </div>
</div>

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

<div class="card shadow-sm">
    <div class="card-header bg-primary text-white">
        <h5 class="card-title mb-0">Détails du profil</h5>
    </div>
    <div class="card-body">
        <div class="d-flex flex-column align-items-center text-center mb-4">
            <?php 
            $photo_path = !empty($user['photo_de_profil']) 
                ? '../../' . ltrim($user['photo_de_profil'], '/') 
                : '../../assets/images/user.png';
            ?>
            <img id="profile-image" src="<?php echo $photo_path; ?>" alt="Photo de profil" class="rounded-circle" width="150" height="150">
            <div class="mt-3">
                <h4><?php echo htmlspecialchars($user['prenoms'] . ' ' . $user['nom']); ?></h4>
                <p class="text-secondary mb-1"><?php echo htmlspecialchars($user['poste']); ?></p>
                <p class="text-muted font-size-sm"><?php echo htmlspecialchars(ucfirst($user['role'])); ?></p>
            </div>
        </div>

        <form action="" method="POST" enctype="multipart/form-data">
            <div class="row g-3">
                <div class="col-md-6">
                    <label for="nom" class="form-label">Nom de famille</label>
                    <input type="text" class="form-control" id="nom" name="nom" value="<?php echo htmlspecialchars($user['nom'] ?? ''); ?>" required>
                </div>
                <div class="col-md-6">
                    <label for="prenoms" class="form-label">Prénoms</label>
                    <input type="text" class="form-control" id="prenoms" name="prenoms" value="<?php echo htmlspecialchars($user['prenoms'] ?? ''); ?>" required>
                </div>
                <div class="col-md-6">
                    <label for="nom_utilisateur" class="form-label">Nom d'utilisateur</label>
                    <input type="text" class="form-control" id="nom_utilisateur" value="<?php echo htmlspecialchars($user['nom_utilisateur'] ?? ''); ?>" disabled>
                </div>
                <div class="col-md-6">
                    <label for="role" class="form-label">Rôle (Privilèges)</label>
                    <input type="text" class="form-control" id="role" value="<?php echo htmlspecialchars(ucfirst($user['role'] ?? '')); ?>" disabled>
                </div>
                <div class="col-md-6">
                    <label for="poste" class="form-label">Poste</label>
                    <input type="text" class="form-control" id="poste" name="poste" value="<?php echo htmlspecialchars($user['poste'] ?? ''); ?>" required>
                </div>
                <div class="col-md-12">
                    <label for="photo" class="form-label">Changer de photo de profil</label>
                    <input type="file" class="form-control" id="photo" name="photo">
                </div>
            </div>
            <div class="mt-4 text-center">
                <button type="submit" class="btn btn-primary">
                    <i class="bi bi-save"></i> Enregistrer les modifications
                </button>
            </div>
        </form>
    </div>
</div>

<?php include '../../includes/footer.php'; ?>
<script>
    document.getElementById('photo').addEventListener('change', function(event) {
        const file = event.target.files[0];
        if (file) {
            const reader = new FileReader();
            reader.onload = function(e) {
                document.getElementById('profile-image').src = e.target.result;
            }
            reader.readAsDataURL(file);
        }
    });
</script>
