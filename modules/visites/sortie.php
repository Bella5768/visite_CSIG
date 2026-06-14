<?php
require_once __DIR__.'/../../config/config.php';
require_once __DIR__.'/visites_functions.php';

// MÊME LOGIQUE QUE LA PAGE D'ACCUEIL
// Si non connecté, rediriger vers la page de connexion
if (!is_logged_in()) {
    redirect('../../modules/auth/login.php');
}


$page_title = 'Enregistrer une sortie';
$user = get_current_user2();

// Variables
$visite_preselected = null;
$visites_en_cours = get_visites_en_cours();

// Si une visite spécifique est sélectionnée
if (isset($_GET['visite_id'])) {
    $visite_id = (int)$_GET['visite_id'];
    $visite_preselected = get_visite_by_id($visite_id);
    
    if (!$visite_preselected || $visite_preselected['heure_sortie']) {
        set_flash_message('warning', 'Cette visite n\'est pas en cours ou est déjà terminée');
        redirect('index.php');
    }
}

// Traitement du formulaire
if ($_SERVER['REQUEST_METHOD'] == 'POST') {
    $visite_id = (int)$_POST['visite_id'];
    $observations_sortie = sanitize_input($_POST['observations_sortie']);
    $agent_sortie = $user['nom'] . ' ' . $user['prenoms'];
    
    if (empty($visite_id)) {
        set_flash_message('danger', 'Veuillez sélectionner une visite à terminer');
    } else {
        $result = record_sortie($visite_id, $agent_sortie, $observations_sortie);
        
        if ($result['success']) {
            set_flash_message('success', $result['message']);
            redirect('index.php');
        } else {
            set_flash_message('danger', $result['message']);
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
            <i class="bi bi-box-arrow-right"></i> Enregistrer une sortie
        </h1>
        <p class="text-muted mb-0">
            Terminer la visite d'un visiteur - <?php echo date('d/m/Y H:i'); ?>
        </p>
    </div>
    <div class="col-md-4 text-md-end">
        <a href="index.php" class="btn btn-outline-secondary">
            <i class="bi bi-arrow-left"></i> Retour aux visites
        </a>
    </div>
</div>

<?php if (empty($visites_en_cours) && !$visite_preselected): ?>
    <!-- Aucune visite en cours -->
    <div class="row">
        <div class="col-12">
            <div class="card">
                <div class="card-body text-center p-5">
                    <i class="bi bi-check-circle h1 text-success mb-3"></i>
                    <h4>Aucune visite en cours</h4>
                    <p class="text-muted mb-4">
                        Il n'y a actuellement aucune visite en cours à terminer.
                    </p>
                    <div class="d-flex justify-content-center gap-2">
                        <a href="nouvelle_visite.php" class="btn btn-primary">
                            <i class="bi bi-plus-circle"></i> Nouvelle visite
                        </a>
                        <a href="index.php" class="btn btn-outline-primary">
                            <i class="bi bi-list"></i> Voir toutes les visites
                        </a>
                    </div>
                </div>
            </div>
        </div>
    </div>

<?php else: ?>
    <div class="row">
        <div class="col-lg-8">
            <div class="card">
                <div class="card-header">
                    <h5 class="card-title mb-0">
                        <i class="bi bi-person-check"></i> Sélectionner la visite à terminer
                    </h5>
                </div>
                <div class="card-body">
                    <form method="POST" action="" id="sortieForm">
                        
                        <?php if ($visite_preselected): ?>
                            <!-- Visite pré-sélectionnée -->
                            <input type="hidden" name="visite_id" value="<?php echo $visite_preselected['id']; ?>">
                            
                            <div class="card bg-light border-success mb-4">
                                <div class="card-header bg-success text-white">
                                    <h6 class="mb-0">
                                        <i class="bi bi-person-circle"></i> Visite sélectionnée
                                    </h6>
                                </div>
                                <div class="card-body">
                                    <div class="row">
                                        <div class="col-md-6">
                                            <h5 class="mb-2">
                                                <?php echo htmlspecialchars($visite_preselected['prenoms'] . ' ' . $visite_preselected['nom']); ?>
                                            </h5>
                                            <p class="mb-1">
                                                <span class="badge badge-primary me-2">
                                                    <?php echo strtoupper($visite_preselected['type_identite']); ?>
                                                </span>
                                                <?php echo htmlspecialchars($visite_preselected['numero_identite']); ?>
                                            </p>
                                            <p class="mb-1">
                                                <i class="bi bi-clipboard-check"></i>
                                                <strong>Motif:</strong> <?php echo htmlspecialchars($visite_preselected['motif']); ?>
                                            </p>
                                        </div>
                                        <div class="col-md-6">
                                            <p class="mb-1">
                                                <i class="bi bi-clock"></i>
                                                <strong>Entrée:</strong> <?php echo date('H:i', strtotime($visite_preselected['heure_entree'])); ?>
                                            </p>
                                            <p class="mb-1">
                                                <i class="bi bi-calendar"></i>
                                                <strong>Date:</strong> <?php echo date('d/m/Y', strtotime($visite_preselected['date_visite'])); ?>
                                            </p>
                                            <?php if ($visite_preselected['correspondant_nom']): ?>
                                                <p class="mb-1">
                                                    <i class="bi bi-person-badge"></i>
                                                    <strong>Correspondant:</strong>
                                                    <?php echo htmlspecialchars($visite_preselected['correspondant_prenoms'] . ' ' . $visite_preselected['correspondant_nom']); ?>
                                                </p>
                                            <?php endif; ?>
                                            
                                            <!-- Durée de visite -->
                                            <?php
                                            $entree = new DateTime($visite_preselected['date_visite'] . ' ' . $visite_preselected['heure_entree']);
                                            $maintenant = new DateTime();
                                            $diff = $entree->diff($maintenant);
                                            $duree = $diff->h . 'h ' . $diff->i . 'min';
                                            ?>
                                            <p class="mb-0">
                                                <i class="bi bi-stopwatch"></i>
                                                <strong>Durée:</strong> 
                                                <span class="text-primary font-monospace"><?php echo $duree; ?></span>
                                            </p>
                                        </div>
                                    </div>
                                    
                                    <?php if ($visite_preselected['observations']): ?>
                                        <div class="mt-3 pt-3 border-top">
                                            <small class="text-muted">Observations d'entrée:</small>
                                            <p class="mb-0"><?php echo nl2br(htmlspecialchars($visite_preselected['observations'])); ?></p>
                                        </div>
                                    <?php endif; ?>
                                    
                                    <div class="mt-3">
                                        <a href="sortie.php" class="btn btn-sm btn-outline-primary">
                                            <i class="bi bi-arrow-repeat"></i> Changer de visite
                                        </a>
                                    </div>
                                </div>
                            </div>
                            
                        <?php else: ?>
                            <!-- Sélection de visite -->
                            <div class="mb-4">
                                <label class="form-label">
                                    <i class="bi bi-person"></i> Visiteur à faire sortir *
                                </label>
                                
                                <div class="row">
                                    <?php foreach ($visites_en_cours as $visite): ?>
                                    <div class="col-md-6 mb-3">
                                        <div class="card border" style="cursor: pointer;" onclick="selectVisite(<?php echo $visite['id']; ?>)">
                                            <div class="card-body">
                                                <div class="form-check">
                                                    <input class="form-check-input" type="radio" name="visite_id" 
                                                           id="visite_<?php echo $visite['id']; ?>" 
                                                           value="<?php echo $visite['id']; ?>" required>
                                                    <label class="form-check-label w-100" for="visite_<?php echo $visite['id']; ?>">
                                                        <h6 class="mb-2">
                                                            <?php echo htmlspecialchars($visite['prenoms'] . ' ' . $visite['nom']); ?>
                                                        </h6>
                                                        <p class="mb-1 small">
                                                            <span class="badge badge-primary me-1">
                                                                <?php echo strtoupper($visite['type_identite']); ?>
                                                            </span>
                                                            <?php echo htmlspecialchars($visite['numero_identite']); ?>
                                                        </p>
                                                        <p class="mb-1 small">
                                                            <i class="bi bi-clipboard-check"></i>
                                                            <?php echo htmlspecialchars($visite['motif']); ?>
                                                        </p>
                                                        <p class="mb-0 small">
                                                            <i class="bi bi-clock"></i>
                                                            Entrée: <?php echo date('H:i', strtotime($visite['heure_entree'])); ?>
                                                            
                                                            <?php
                                                            $entree = new DateTime($visite['date_visite'] . ' ' . $visite['heure_entree']);
                                                            $maintenant = new DateTime();
                                                            $diff = $entree->diff($maintenant);
                                                            $duree = $diff->h . 'h ' . $diff->i . 'min';
                                                            ?>
                                                            <span class="text-primary">
                                                                (<?php echo $duree; ?>)
                                                            </span>
                                                        </p>
                                                    </label>
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                    <?php endforeach; ?>
                                </div>
                            </div>
                        <?php endif; ?>

                        <!-- Observations de sortie -->
                        <div class="mb-4">
                            <label for="observations_sortie" class="form-label">
                                <i class="bi bi-chat-text"></i> Observations de sortie
                            </label>
                            <textarea class="form-control" id="observations_sortie" name="observations_sortie" 
                                      rows="3" placeholder="Observations concernant la sortie du visiteur (optionnel)"></textarea>
                            <small class="form-text text-muted">
                                Ces observations seront ajoutées à celles d'entrée.
                            </small>
                        </div>

                        <!-- Boutons d'action -->
                        <div class="d-flex justify-content-between">
                            <a href="index.php" class="btn btn-secondary">
                                <i class="bi bi-x"></i> Annuler
                            </a>
                            <button type="submit" class="btn btn-success btn-lg" id="submitBtn">
                                <i class="bi bi-check-circle"></i> Enregistrer la sortie
                            </button>
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
                        <label class="text-muted small">Heure de sortie</label>
                        <div class="fw-bold text-success"><?php echo date('H:i:s'); ?></div>
                    </div>
                    <div class="mb-3">
                        <label class="text-muted small">Date</label>
                        <div class="fw-bold"><?php echo date('d/m/Y'); ?></div>
                    </div>
                    <div class="mb-3">
                        <label class="text-muted small">Agent de sortie</label>
                        <div class="fw-bold"><?php echo $user['prenoms'] . ' ' . $user['nom']; ?></div>
                    </div>
                    <div class="mb-0">
                        <label class="text-muted small">Poste</label>
                        <div class="fw-bold"><?php echo $user['poste']; ?></div>
                    </div>
                </div>
            </div>

            <!-- Statistiques rapides -->
            <div class="card mt-3">
                <div class="card-header">
                    <h6 class="card-title mb-0">
                        <i class="bi bi-graph-up"></i> Statistiques du jour
                    </h6>
                </div>
                <div class="card-body">
                    <div class="row text-center">
                        <div class="col-6">
                            <div class="text-warning h3 mb-1"><?php echo count($visites_en_cours); ?></div>
                            <small class="text-muted">En cours</small>
                        </div>
                        <div class="col-6">
                            <?php
                            $pdo = get_db_connection();
                            $stmt = $pdo->prepare("SELECT COUNT(*) FROM visites WHERE DATE(date_visite) = CURDATE() AND heure_sortie IS NOT NULL");
                            $stmt->execute();
                            $sorties_jour = $stmt->fetchColumn();
                            ?>
                            <div class="text-success h3 mb-1"><?php echo $sorties_jour; ?></div>
                            <small class="text-muted">Sorties</small>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Aide -->
            <div class="card mt-3 border-info">
                <div class="card-body">
                    <h6 class="text-info">
                        <i class="bi bi-lightbulb"></i> Conseil
                    </h6>
                    <p class="mb-0 small">
                        Assurez-vous que le visiteur a bien récupéré tous ses effets personnels 
                        avant d'enregistrer sa sortie.
                    </p>
                </div>
            </div>
        </div>
    </div>
<?php endif; ?>

<?php // include '../../includes/footer.php'; ?>

<script>
// Fonction pour sélectionner une visite
function selectVisite(visiteId) {
    const radio = document.getElementById('visite_' + visiteId);
    radio.checked = true;
    
    // Mettre en évidence la carte sélectionnée
    document.querySelectorAll('.card.border').forEach(card => {
        card.classList.remove('border-success');
    });
    
    radio.closest('.card').classList.add('border-success');
}

// Event listeners
document.addEventListener('DOMContentLoaded', function() {
    // Gestion des clics sur les cartes
    document.querySelectorAll('.card[onclick]').forEach(card => {
        card.addEventListener('click', function() {
            const radio = this.querySelector('input[type="radio"]');
            if (radio) {
                radio.checked = true;
                selectVisite(radio.value);
            }
        });
    });
    
    // Validation du formulaire
    const form = document.getElementById('sortieForm');
    if (form) {
        form.addEventListener('submit', function(e) {
            const selectedVisite = document.querySelector('input[name="visite_id"]:checked');
            
            if (!selectedVisite) {
                e.preventDefault();
                alert('Veuillez sélectionner une visite à terminer');
                return;
            }
            
            if (!confirm('Êtes-vous sûr de vouloir enregistrer cette sortie ?')) {
                e.preventDefault();
                return;
            }
            
            // Désactiver le bouton et afficher un indicateur de chargement
            const submitBtn = document.getElementById('submitBtn');
            submitBtn.innerHTML = '<i class="bi bi-hourglass-split"></i> Enregistrement...';
            submitBtn.disabled = true;
        });
    }
    
    // Mise à jour de l'heure en temps réel
    function updateTime() {
        const now = new Date();
        const timeString = now.toTimeString().split(' ')[0];
        const timeElement = document.querySelector('.text-success');
        if (timeElement) {
            timeElement.textContent = timeString;
        }
    }
    
    setInterval(updateTime, 1000);
    
    // Raccourci clavier Échap pour annuler
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape') {
            if (confirm('Voulez-vous annuler et retourner à la liste des visites ?')) {
                window.location.href = 'index.php';
            }
        }
    });
});

// Auto-refresh des durées toutes les minutes
setInterval(function() {
    location.reload();
}, 60000);
</script>