<?php
require_once __DIR__.'/../../config/config.php';
require_once __DIR__.'/visiteurs_functions.php';

// Vérifier la session
if (!is_logged_in()) {
    redirect('../../modules/auth/login.php');
}

$page_title = 'Nouveau visiteur';

// Variable pour redirection après création
$redirect_to = isset($_GET['redirect']) ? sanitize_input($_GET['redirect']) : 'index';

// Traitement du formulaire
if ($_SERVER['REQUEST_METHOD'] == 'POST') {
    $data = [
        'type_identite' => sanitize_input($_POST['type_identite']),
        'numero_identite' => sanitize_input($_POST['numero_identite']),
        'nom' => sanitize_input($_POST['nom']),
        'prenoms' => sanitize_input($_POST['prenoms']),
        'telephone' => sanitize_input($_POST['telephone']),
        'email' => sanitize_input($_POST['email']),
        'adresse' => sanitize_input($_POST['adresse'])
    ];
    
    // Validation des données
    $errors = validate_visiteur_data($data);

    // Forcer téléphone obligatoire
    if (empty($data['telephone'])) {
        $errors[] = "Le numéro de téléphone est obligatoire.";
    }
    
    if (empty($errors)) {
        $result = create_visiteur($data);
        
        if ($result['success']) {
            set_flash_message('success', $result['message']);
            
            // Redirection selon le contexte
            if ($redirect_to === 'nouvelle_visite') {
                redirect('../visites/nouvelle_visite.php?visiteur_id=' . $result['visiteur_id']);
            } else {
                redirect('index.php');
            }
        } else {
            set_flash_message('danger', $result['message']);
        }
    } else {
        foreach ($errors as $error) {
            set_flash_message('danger', $error);
        }
    }
}

// Variables de navigation
$css_path = '../../assets/css/';
$js_path = '../../assets/js/';
$base_url = '../../';
$modules_path = '../';

include '../../includes/header.php';
?>

<div class="row mb-4">
    <div class="col-md-8">
        <h1 class="h3 mb-2 text-primary">
            <i class="bi bi-person-plus"></i> Nouveau visiteur
        </h1>
        <p class="text-muted mb-0">
            Ajouter un nouveau visiteur au système
        </p>
    </div>
    <div class="col-md-4 text-md-end">
        <a href="<?php echo $redirect_to === 'nouvelle_visite' ? '../visites/nouvelle_visite.php' : 'index.php'; ?>" 
           class="btn btn-outline-secondary">
            <i class="bi bi-arrow-left"></i> 
            <?php echo $redirect_to === 'nouvelle_visite' ? 'Retour à la visite' : 'Retour à la liste'; ?>
        </a>
    </div>
</div>

<div class="row">
    <div class="col-lg-8">
        <div class="card">
            <div class="card-header">
                <h5 class="card-title mb-0">
                    <i class="bi bi-person-badge"></i> Informations du visiteur
                </h5>
            </div>
            <div class="card-body">
                <form method="POST" action="" id="visiteurForm" novalidate>
                    
                    <!-- Nom et prénoms -->
                    <div class="row mb-3">
                        <div class="col-md-6">
                            <label for="nom" class="form-label">
                                <i class="bi bi-person"></i> Nom de famille *
                            </label>
                            <input type="text" class="form-control" id="nom" name="nom" 
                                   value="<?php echo htmlspecialchars($_POST['nom'] ?? ''); ?>"
                                   required maxlength="100" autocomplete="family-name">
                            <div class="invalid-feedback">
                                Le nom est obligatoire (minimum 2 caractères).
                            </div>
                        </div>
                        <div class="col-md-6">
                            <label for="prenoms" class="form-label">
                                <i class="bi bi-person"></i> Prénoms *
                            </label>
                            <input type="text" class="form-control" id="prenoms" name="prenoms" 
                                   value="<?php echo htmlspecialchars($_POST['prenoms'] ?? ''); ?>"
                                   required maxlength="100" autocomplete="given-name">
                            <div class="invalid-feedback">
                                Le prénom est obligatoire (minimum 2 caractères).
                            </div>
                        </div>
                    </div>
                    
                    <!-- Type et numéro d'identité (facultatifs) -->
                    <div class="row mb-3">
                        <div class="col-md-6">
                            <label for="type_identite" class="form-label">
                                <i class="bi bi-card-text"></i> Type de pièce d'identité
                            </label>
                            <select class="form-select" id="type_identite" name="type_identite">
                                <option value="">Sélectionnez un type</option>
                                <?php foreach (TYPES_IDENTITE as $type => $label): ?>
                                <option value="<?php echo $type; ?>" 
                                        <?php echo (($_POST['type_identite'] ?? '') === $type) ? 'selected' : ''; ?>>
                                    <?php echo $label; ?>
                                </option>
                                <?php endforeach; ?>
                            </select>
                        </div>
                        <div class="col-md-6">
                            <label for="numero_identite" class="form-label">
                                <i class="bi bi-hash"></i> Numéro de la pièce
                            </label>
                            <input type="text" class="form-control" id="numero_identite" name="numero_identite" 
                                   value="<?php echo htmlspecialchars($_POST['numero_identite'] ?? ''); ?>"
                                   maxlength="50" style="font-family: monospace;">
                            <small class="form-text text-muted">
                                Ce numéro doit être unique dans le système (si renseigné).
                            </small>
                        </div>
                    </div>
                    
                    <!-- Contact -->
                    <div class="row mb-3">
                        <div class="col-md-6">
                            <label for="telephone" class="form-label">
                                <i class="bi bi-telephone"></i> Téléphone *
                            </label>
                            <input type="tel" class="form-control" id="telephone" name="telephone" 
                                   value="<?php echo htmlspecialchars($_POST['telephone'] ?? ''); ?>"
                                   required maxlength="20" autocomplete="tel">
                            <div class="invalid-feedback">
                                Le numéro de téléphone est obligatoire et doit être valide.
                            </div>
                            <small class="form-text text-muted">
                                Format: +224 XXX XXX XXX ou équivalent
                            </small>
                        </div>
                        <div class="col-md-6">
                            <label for="email" class="form-label">
                                <i class="bi bi-envelope"></i> Email
                            </label>
                            <input type="email" class="form-control" id="email" name="email" 
                                   value="<?php echo htmlspecialchars($_POST['email'] ?? ''); ?>"
                                   maxlength="100" autocomplete="email">
                            <div class="invalid-feedback">
                                Format de l'email invalide.
                            </div>
                        </div>
                    </div>
                    
                    <!-- Adresse -->
                    <div class="row mb-4">
                        <div class="col-12">
                            <label for="adresse" class="form-label">
                                <i class="bi bi-geo-alt"></i> Adresse complète
                            </label>
                            <textarea class="form-control" id="adresse" name="adresse" 
                                      rows="3" maxlength="255"><?php echo htmlspecialchars($_POST['adresse'] ?? ''); ?></textarea>
                            <small class="form-text text-muted">
                                Adresse complète du visiteur (quartier, commune, ville)
                            </small>
                        </div>
                    </div>
                    
                    <!-- Actions -->
                    <div class="row">
                        <div class="col-12">
                            <div class="d-flex justify-content-between">
                                <a href="<?php echo $redirect_to === 'nouvelle_visite' ? '../visites/nouvelle_visite.php' : 'index.php'; ?>" 
                                   class="btn btn-secondary">
                                    <i class="bi bi-x"></i> Annuler
                                </a>
                                <div>
                                    <?php if ($redirect_to === 'nouvelle_visite'): ?>
                                        <button type="button" class="btn btn-outline-primary me-2" onclick="previewAndContinue()">
                                            <i class="bi bi-eye"></i> Aperçu
                                        </button>
                                    <?php endif; ?>
                                    <button type="submit" class="btn btn-primary btn-lg" id="submitBtn">
                                        <i class="bi bi-check-circle"></i> 
                                        <?php echo $redirect_to === 'nouvelle_visite' ? 'Créer et continuer la visite' : 'Créer le visiteur'; ?>
                                    </button>
                                </div>
                            </div>
                        </div>
                    </div>
                    
                    <!-- Champ caché pour la redirection -->
                    <input type="hidden" name="redirect_to" value="<?php echo $redirect_to; ?>">
                </form>
            </div>
        </div>
    </div>
    
    <div class="col-lg-4">
        <!-- Aide et conseils -->
        <div class="card">
            <div class="card-header">
                <h6 class="card-title mb-0">
                    <i class="bi bi-info-circle"></i> Informations importantes
                </h6>
            </div>
            <div class="card-body">
                <div class="alert alert-info">
                    <h6><i class="bi bi-exclamation-circle"></i> Champs obligatoires</h6>
                    <ul class="mb-0 small">
                        <li>Nom et prénoms</li>
                        <li>Numéro de téléphone</li>
                    </ul>
                </div>
                
                <div class="alert alert-warning">
                    <h6><i class="bi bi-shield-exclamation"></i> Vérification d'unicité</h6>
                    <p class="mb-0 small">
                        Si vous renseignez un numéro d'identité, le système vérifiera automatiquement 
                        qu'aucun autre visiteur n'utilise le même numéro.
                    </p>
                </div>
            </div>
        </div>
        
        <!-- Conseils de saisie -->
        <div class="card mt-3">
            <div class="card-header">
                <h6 class="card-title mb-0">
                    <i class="bi bi-lightbulb"></i> Conseils de saisie
                </h6>
            </div>
            <div class="card-body">
                <ul class="list-unstyled mb-0 small">
                    <li class="mb-2">
                        <i class="bi bi-check text-success"></i>
                        <strong>Nom/Prénoms :</strong> Respectez l'orthographe de la pièce d'identité
                    </li>
                    <li class="mb-2">
                        <i class="bi bi-check text-success"></i>
                        <strong>Numéro :</strong> Saisissez exactement comme sur le document (si disponible)
                    </li>
                    <li class="mb-2">
                        <i class="bi bi-check text-success"></i>
                        <strong>Téléphone :</strong> Format recommandé : +224 XXX XXX XXX
                    </li>
                    <li class="mb-0">
                        <i class="bi bi-check text-success"></i>
                        <strong>Email :</strong> Vérifiez la syntaxe avant validation
                    </li>
                </ul>
            </div>
        </div>
        
        <!-- Aperçu en temps réel -->
        <div class="card mt-3" id="previewCard" style="display: none;">
            <div class="card-header bg-success text-white">
                <h6 class="card-title mb-0">
                    <i class="bi bi-eye"></i> Aperçu
                </h6>
            </div>
            <div class="card-body" id="previewContent"></div>
        </div>
        
        <!-- Visiteurs similaires -->
        <div class="card mt-3" id="similarCard" style="display: none;">
            <div class="card-header bg-warning text-dark">
                <h6 class="card-title mb-0">
                    <i class="bi bi-exclamation-triangle"></i> Visiteurs similaires détectés
                </h6>
            </div>
            <div class="card-body" id="similarContent"></div>
        </div>
    </div>
</div>

<script>
// Validation d'un champ
function validateField(field) {
    const value = field.value.trim();
    let isValid = true;
    let errorMessage = '';
    
    field.classList.remove('is-valid', 'is-invalid');
    
    switch(field.name) {
        case 'nom':
        case 'prenoms':
            if (value.length < 2) {
                isValid = false;
                errorMessage = 'Minimum 2 caractères requis';
            } else if (!/^[a-zA-ZÀ-ÿ\s\-']+$/.test(value)) {
                isValid = false;
                errorMessage = 'Seules les lettres sont autorisées';
            }
            break;
            
        case 'telephone':
            if (!value) {
                isValid = false;
                errorMessage = 'Le numéro de téléphone est obligatoire';
            } else if (!/^[\+]?[0-9\s\-\(\)]{8,}$/.test(value)) {
                isValid = false;
                errorMessage = 'Format de téléphone invalide';
            }
            break;
            
        case 'email':
            if (value && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value)) {
                isValid = false;
                errorMessage = 'Format email invalide';
            }
            break;
    }
    
    if (field.hasAttribute('required') || value) {
        field.classList.add(isValid ? 'is-valid' : 'is-invalid');
        if (!isValid && errorMessage) {
            const feedback = field.nextElementSibling;
            if (feedback && feedback.classList.contains('invalid-feedback')) {
                feedback.textContent = errorMessage;
            }
        }
    }
    return isValid;
}
</script>

<style>
.avatar-circle {
    background: linear-gradient(135deg, var(--primary-color), var(--secondary-color));
    color: white;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: bold;
}
.is-valid { border-color: var(--success-color) !important; }
.is-invalid { border-color: var(--danger-color) !important; }
</style>
