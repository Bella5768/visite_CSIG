<?php
require_once __DIR__.'/../../config/config.php';
require_once __DIR__.'/visites_functions.php';
// Ajout de cette ligne manquante pour les fonctions visiteurs
require_once __DIR__.'/../visiteurs/visiteurs_functions.php';

// MÊME LOGIQUE QUE LA PAGE D'ACCUEIL
if (!is_logged_in()) {
    redirect('../../modules/auth/login.php');
}

$page_title = 'Nouvelle visite';
$user = get_current_user2();

// Variables pour le formulaire
$visiteur_id = null;
$visiteur = null;
$motifs = get_motifs_visite();
$correspondants = get_correspondants();

// Si un visiteur est sélectionné depuis la recherche
if (isset($_GET['visiteur_id'])) {
    $visiteur_id = (int)$_GET['visiteur_id'];
    $visiteur = get_visiteur_by_id($visiteur_id);
}

// Traitement du formulaire
if ($_SERVER['REQUEST_METHOD'] == 'POST') {
    $errors = [];
    
    // Validation des données
    $visiteur_id = (int)$_POST['visiteur_id'];
    $motif_id = (int)$_POST['motif_id'];
    $correspondant_id = !empty($_POST['correspondant_id']) ? (int)$_POST['correspondant_id'] : null;
    $type_visite = $correspondant_id ? 'avec_rdv' : 'sans_rdv';
    $observations = sanitize_input($_POST['observations']);
    
    if (empty($visiteur_id)) {
        $errors[] = 'Veuillez sélectionner un visiteur';
    }
    
    if (empty($motif_id)) {
        $errors[] = 'Veuillez sélectionner un motif de visite';
    }
    
    // Vérifier si le visiteur n'a pas déjà une visite en cours
    $pdo = get_db_connection();
    $stmt = $pdo->prepare("
        SELECT COUNT(*) 
        FROM visites 
        WHERE visiteur_id = ? AND DATE(date_visite) = CURDATE() 
        AND heure_sortie IS NULL AND statut = 'en_cours'
    ");
    $stmt->execute([$visiteur_id]);
    
    if ($stmt->fetchColumn() > 0) {
        $errors[] = 'Ce visiteur a déjà une visite en cours aujourd\'hui';
    }
    
    if (empty($errors)) {
        $visite_data = [
            'visiteur_id' => $visiteur_id,
            'motif_id' => $motif_id,
            'correspondant_id' => $correspondant_id,
            'type_visite' => $type_visite,
            'date_visite' => date('Y-m-d'),
            'heure_entree' => date('H:i:s'),
            'observations' => $observations,
            'agent_entree' => $user['nom'] . ' ' . $user['prenoms']
        ];
        
        $result = create_visite($visite_data);
        
        if ($result['success']) {
            set_flash_message('success', $result['message']);
            redirect('index.php');
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
            <i class="bi bi-plus-circle"></i> Nouvelle visite
        </h1>
        <p class="text-muted mb-0">
            Enregistrer l'entrée d'un visiteur - <?php echo date('d/m/Y H:i'); ?>
        </p>
    </div>
    <div class="col-md-4 text-md-end">
        <a href="index.php" class="btn btn-outline-secondary">
            <i class="bi bi-arrow-left"></i> Retour aux visites
        </a>
    </div>
</div>

<div class="row">
    <div class="col-lg-8">
        <div class="card">
            <div class="card-header">
                <h5 class="card-title mb-0">
                    <i class="bi bi-person-plus"></i> Informations de la visite
                </h5>
            </div>
            <div class="card-body">
                <form method="POST" action="" id="nouvelleVisiteForm">
                    
                    <!-- Sélection du visiteur -->
                    <div class="row mb-4">
                        <div class="col-12">
                            <label class="form-label">
                                <i class="bi bi-person"></i> Visiteur *
                            </label>
                            
                            <?php if ($visiteur): ?>
                                <!-- Visiteur déjà sélectionné -->
                                <div class="card bg-light">
                                    <div class="card-body">
                                        <input type="hidden" name="visiteur_id" value="<?php echo $visiteur['id']; ?>">
                                        <div class="row">
                                            <div class="col-md-6">
                                                <h6 class="mb-2">
                                                    <i class="bi bi-person-circle"></i>
                                                    <?php echo htmlspecialchars($visiteur['prenoms'] . ' ' . $visiteur['nom']); ?>
                                                </h6>
                                                <p class="mb-1">
                                                    <small class="text-muted">
                                                        <span class="badge badge-primary me-2"><?php echo strtoupper($visiteur['type_identite']); ?></span>
                                                        <?php echo htmlspecialchars($visiteur['numero_identite']); ?>
                                                    </small>
                                                </p>
                                            </div>
                                            <div class="col-md-6">
                                                <?php if ($visiteur['telephone']): ?>
                                                    <p class="mb-1">
                                                        <i class="bi bi-telephone"></i>
                                                        <?php echo htmlspecialchars($visiteur['telephone']); ?>
                                                    </p>
                                                <?php endif; ?>
                                                <?php if ($visiteur['email']): ?>
                                                    <p class="mb-1">
                                                        <i class="bi bi-envelope"></i>
                                                        <?php echo htmlspecialchars($visiteur['email']); ?>
                                                    </p>
                                                <?php endif; ?>
                                            </div>
                                        </div>
                                        <div class="mt-2">
                                            <a href="javascript:void(0)" onclick="changerVisiteur()" class="btn btn-sm btn-outline-primary">
                                                <i class="bi bi-arrow-repeat"></i> Changer de visiteur
                                            </a>
                                            <a href="../visiteurs/historique.php?id=<?php echo $visiteur['id']; ?>" 
                                               class="btn btn-sm btn-outline-info" target="_blank">
                                                <i class="bi bi-clock-history"></i> Voir l'historique
                                            </a>
                                        </div>
                                    </div>
                                </div>
                            <?php else: ?>
                                <!-- Recherche de visiteur -->
                                <div class="input-group mb-3">
                                    <input type="text" class="form-control" id="searchVisiteur" 
                                           placeholder="Rechercher par nom, prénom ou numéro d'identité..."
                                           autocomplete="off">
                                    <button class="btn btn-outline-secondary" type="button" id="btnSearchVisiteur">
                                        <i class="bi bi-search"></i>
                                    </button>
                                </div>
                                <div id="searchResults" class="border rounded p-2" style="display: none; max-height: 300px; overflow-y: auto;">
                                    <!-- Résultats de recherche -->
                                </div>
                                <input type="hidden" name="visiteur_id" id="selectedVisiteurId" required>
                                
                                <div class="text-center mt-3">
                                    <p class="text-muted">ou</p>
                                    <a href="../visiteurs/ajouter.php?redirect=nouvelle_visite" class="btn btn-success">
                                        <i class="bi bi-person-plus"></i> Créer un nouveau visiteur
                                    </a>
                                </div>
                            <?php endif; ?>
                        </div>
                    </div>

                    <!-- Motif de la visite -->
                    <div class="row mb-3">
                        <div class="col-md-6">
                            <label for="motif_id" class="form-label">
                                <i class="bi bi-clipboard-check"></i> Motif de la visite *
                            </label>
                            <select class="form-select" id="motif_id" name="motif_id" required>
                                <option value="">Sélectionnez un motif</option>
                                <?php foreach ($motifs as $motif): ?>
                                <option value="<?php echo $motif['id']; ?>">
                                    <?php echo htmlspecialchars($motif['libelle']); ?>
                                </option>
                                <?php endforeach; ?>
                            </select>
                        </div>
                        
                        <div class="col-md-6">
                            <label for="correspondant_id" class="form-label">
                                <i class="bi bi-person-badge"></i> Correspondant
                            </label>
                            <select class="form-select" id="correspondant_id" name="correspondant_id">
                                <option value="">Visite libre (sans correspondant)</option>
                                <?php foreach ($correspondants as $correspondant): ?>
                                <option value="<?php echo $correspondant['id']; ?>">
                                    <?php echo htmlspecialchars($correspondant['prenoms'] . ' ' . $correspondant['nom']); ?>
                                    - <?php echo htmlspecialchars($correspondant['fonction']); ?>
                                </option>
                                <?php endforeach; ?>
                            </select>
                            <small class="form-text text-muted">
                                Laissez vide pour une visite libre
                            </small>
                        </div>
                    </div>

                    <!-- Observations -->
                    <div class="row mb-4">
                        <div class="col-12">
                            <label for="observations" class="form-label">
                                <i class="bi bi-chat-text"></i> Observations
                            </label>
                            <textarea class="form-control" id="observations" name="observations" 
                                      rows="3" placeholder="Observations particulières, objets transportés, etc."></textarea>
                        </div>
                    </div>

                    <!-- Boutons d'action -->
                    <div class="row">
                        <div class="col-12">
                            <div class="d-flex justify-content-between">
                                <a href="index.php" class="btn btn-secondary">
                                    <i class="bi bi-x"></i> Annuler
                                </a>
                                <button type="submit" class="btn btn-primary btn-lg" id="submitBtn">
                                    <i class="bi bi-check-circle"></i> Enregistrer l'entrée
                                </button>
                            </div>
                        </div>
                    </div>
                </form>
            </div>
        </div>
    </div>
    
    <div class="col-lg-4">
        <!-- Informations -->
        <div class="card">
            <div class="card-header">
                <h6 class="card-title mb-0">
                    <i class="bi bi-info-circle"></i> Informations
                </h6>
            </div>
            <div class="card-body">
                <div class="mb-3">
                    <label class="text-muted small">Date et heure</label>
                    <div class="fw-bold"><?php echo date('d/m/Y H:i'); ?></div>
                </div>
                <div class="mb-3">
                    <label class="text-muted small">Agent d'accueil</label>
                    <div class="fw-bold"><?php echo $user['prenoms'] . ' ' . $user['nom']; ?></div>
                </div>
                <div class="mb-3">
                    <label class="text-muted small">Poste</label>
                    <div class="fw-bold"><?php echo $user['poste']; ?></div>
                </div>
            </div>
        </div>

        <!-- Raccourcis -->
        <div class="card mt-3">
            <div class="card-header">
                <h6 class="card-title mb-0">
                    <i class="bi bi-lightning"></i> Raccourcis
                </h6>
            </div>
            <div class="card-body">
                <div class="d-grid gap-2">
                    <a href="../visiteurs/rechercher.php" class="btn btn-outline-primary btn-sm">
                        <i class="bi bi-search"></i> Rechercher visiteur
                    </a>
                    <a href="../visiteurs/ajouter.php?redirect=nouvelle_visite" class="btn btn-outline-success btn-sm">
                        <i class="bi bi-person-plus"></i> Nouveau visiteur
                    </a>
                    <a href="index.php" class="btn btn-outline-info btn-sm">
                        <i class="bi bi-list"></i> Visites du jour
                    </a>
                </div>
            </div>
        </div>

        <!-- Aide -->
        <div class="card mt-3 border-info">
            <div class="card-body">
                <h6 class="text-info">
                    <i class="bi bi-question-circle"></i> Aide rapide
                </h6>
                <ul class="list-unstyled mb-0 small">
                    <li><i class="bi bi-dot"></i> Recherchez le visiteur par nom ou numéro d'identité</li>
                    <li><i class="bi bi-dot"></i> Créez un nouveau visiteur s'il n'existe pas</li>
                    <li><i class="bi bi-dot"></i> Sélectionnez le motif approprié</li>
                    <li><i class="bi bi-dot"></i> Indiquez le correspondant si nécessaire</li>
                </ul>
            </div>
        </div>
    </div>
</div>

<?php
$additional_js = ['../../assets/js/nouvelle_visite.js'];
// include '../../includes/footer.php';
?>

<script>
// Variables globales
let selectedVisiteur = null;

// Fonction pour rechercher des visiteurs
function searchVisiteurs(query) {
    if (query.length < 2) {
        document.getElementById('searchResults').style.display = 'none';
        return;
    }
    
    fetch('../visiteurs/search_ajax.php?q=' + encodeURIComponent(query))
        .then(response => response.json())
        .then(data => {
            displaySearchResults(data);
        })
        .catch(error => {
            console.error('Erreur:', error);
        });
}

// Fonction pour afficher les résultats de recherche
function displaySearchResults(visiteurs) {
    const resultsDiv = document.getElementById('searchResults');
    
    if (visiteurs.length === 0) {
        resultsDiv.innerHTML = '<p class="text-muted text-center p-3">Aucun visiteur trouvé</p>';
        resultsDiv.style.display = 'block';
        return;
    }
    
    let html = '<div class="list-group list-group-flush">';
    visiteurs.forEach(function(visiteur) {
        html += `
            <a href="javascript:void(0)" class="list-group-item list-group-item-action" 
               onclick="selectVisiteur(${visiteur.id}, '${visiteur.nom}', '${visiteur.prenoms}', '${visiteur.numero_identite}', '${visiteur.type_identite}')">
                <div class="d-flex justify-content-between align-items-start">
                    <div>
                        <h6 class="mb-1">${visiteur.prenoms} ${visiteur.nom}</h6>
                        <p class="mb-1">
                            <span class="badge badge-primary">${visiteur.type_identite.toUpperCase()}</span>
                            ${visiteur.numero_identite}
                        </p>
                        ${visiteur.telephone ? `<small class="text-muted"><i class="bi bi-telephone"></i> ${visiteur.telephone}</small>` : ''}
                    </div>
                </div>
            </a>`;
    });
    html += '</div>';
    
    resultsDiv.innerHTML = html;
    resultsDiv.style.display = 'block';
}

// Fonction pour sélectionner un visiteur
function selectVisiteur(id, nom, prenoms, numero, type) {
    selectedVisiteur = { id, nom, prenoms, numero, type };
    document.getElementById('selectedVisiteurId').value = id;
    document.getElementById('searchVisiteur').value = `${prenoms} ${nom} (${numero})`;
    document.getElementById('searchResults').style.display = 'none';
}

// Fonction pour changer de visiteur
function changerVisiteur() {
    if (confirm('Êtes-vous sûr de vouloir changer de visiteur ?')) {
        window.location.href = 'nouvelle_visite.php';
    }
}

// Event listeners
document.addEventListener('DOMContentLoaded', function() {
    const searchInput = document.getElementById('searchVisiteur');
    const searchBtn = document.getElementById('btnSearchVisiteur');
    
    if (searchInput) {
        let searchTimeout;
        
        searchInput.addEventListener('input', function() {
            clearTimeout(searchTimeout);
            searchTimeout = setTimeout(() => {
                searchVisiteurs(this.value);
            }, 300);
        });
        
        searchInput.addEventListener('focus', function() {
            if (this.value.length >= 2) {
                searchVisiteurs(this.value);
            }
        });
    }
    
    if (searchBtn) {
        searchBtn.addEventListener('click', function() {
            searchVisiteurs(searchInput.value);
        });
    }
    
    // Cacher les résultats quand on clique ailleurs
    document.addEventListener('click', function(e) {
        if (!e.target.closest('#searchVisiteur') && !e.target.closest('#searchResults')) {
            document.getElementById('searchResults').style.display = 'none';
        }
    });
    
    // Validation du formulaire
    document.getElementById('nouvelleVisiteForm').addEventListener('submit', function(e) {
        const visiteurId = document.getElementById('selectedVisiteurId').value;
        const motifId = document.getElementById('motif_id').value;
        
        if (!visiteurId) {
            e.preventDefault();
            alert('Veuillez sélectionner un visiteur');
            return;
        }
        
        if (!motifId) {
            e.preventDefault();
            alert('Veuillez sélectionner un motif de visite');
            return;
        }
        
        // Désactiver le bouton et afficher un indicateur de chargement
        const submitBtn = document.getElementById('submitBtn');
        submitBtn.innerHTML = '<i class="bi bi-hourglass-split"></i> Enregistrement...';
        submitBtn.disabled = true;
    });
});
</script>
