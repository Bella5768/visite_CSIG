<?php
require_once __DIR__.'/../../config/config.php';
require_once __DIR__.'/visites_functions.php';

// MÊME LOGIQUE QUE LA PAGE D'ACCUEIL
// Si non connecté, rediriger vers la page de connexion
if (!is_logged_in()) {
    redirect('../../modules/auth/login.php');
}

$page_title = 'Visites du jour';
$date_selected = isset($_GET['date']) ? $_GET['date'] : date('Y-m-d');

// Récupérer les visites du jour sélectionné
$visites = get_visites_jour($date_selected);
$visites_en_cours = get_visites_en_cours($date_selected);

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
            <i class="bi bi-calendar-check"></i> Gestion des Visites
        </h1>
        <p class="text-muted mb-0">
            Suivi des entrées et sorties - <?php echo date('d/m/Y', strtotime($date_selected)); ?>
        </p>
    </div>
    <div class="col-md-4 text-md-end">
        <div class="btn-group" role="group">
            <a href="nouvelle_visite.php" class="btn btn-primary">
                <i class="bi bi-plus-circle"></i> Nouvelle visite
            </a>
            <a href="sortie.php" class="btn btn-success">
                <i class="bi bi-box-arrow-right"></i> Enregistrer sortie
            </a>
        </div>
    </div>
</div>

<!-- Filtres et statistiques -->
<div class="row mb-4">
    <div class="col-md-8">
        <div class="card">
            <div class="card-body">
                <form method="GET" class="row g-3">
                    <div class="col-md-4">
                        <label for="date" class="form-label">Date</label>
                        <input type="date" class="form-control" id="date" name="date" 
                               value="<?php echo $date_selected; ?>" onchange="this.form.submit()">
                    </div>
                    <div class="col-md-4 d-flex align-items-end">
                        <button type="submit" class="btn btn-outline-primary me-2">
                            <i class="bi bi-search"></i> Filtrer
                        </button>
                        <a href="rechercher.php" class="btn btn-outline-secondary">
                            <i class="bi bi-funnel"></i> Recherche avancée
                        </a>
                    </div>
                </form>
            </div>
        </div>
    </div>
    <div class="col-md-4">
        <div class="card text-center">
            <div class="card-body">
                <div class="row">
                    <div class="col-6">
                        <div class="text-primary h3 mb-1"><?php echo count($visites); ?></div>
                        <small class="text-muted">Total visites</small>
                    </div>
                    <div class="col-6">
                        <div class="text-warning h3 mb-1"><?php echo count($visites_en_cours); ?></div>
                        <small class="text-muted">En cours</small>
                    </div>
                </div>
            </div>
        </div>
    </div>
</div>

<!-- Visites en cours -->
<?php if (!empty($visites_en_cours)): ?>
<div class="row mb-4">
    <div class="col-12">
        <div class="card border-warning">
            <div class="card-header bg-warning text-dark">
                <h5 class="card-title mb-0">
                    <i class="bi bi-clock"></i> Visites en cours (<?php echo count($visites_en_cours); ?>)
                </h5>
            </div>
            <div class="card-body p-0">
                <div class="table-responsive">
                    <table class="table table-hover mb-0">
                        <thead class="table-light">
                            <tr>
                                <th>Visiteur</th>
                                <th>Identité</th>
                                <th>Motif</th>
                                <th>Correspondant</th>
                                <th>Entrée</th>
                                <th>Durée</th>
                                <th>Actions</th>
                            </tr>
                        </thead>
                        <tbody>
                            <?php foreach ($visites_en_cours as $visite): ?>
                            <tr>
                                <td>
                                    <strong><?php echo htmlspecialchars($visite['prenoms'] . ' ' . $visite['nom']); ?></strong>
                                    <?php if ($visite['telephone']): ?>
                                        <br><small class="text-muted">
                                            <i class="bi bi-telephone"></i> <?php echo htmlspecialchars($visite['telephone']); ?>
                                        </small>
                                    <?php endif; ?>
                                </td>
                                <td>
                                    <span class="badge badge-primary"><?php echo strtoupper($visite['type_identite']); ?></span>
                                    <br><small class="font-monospace"><?php echo htmlspecialchars($visite['numero_identite']); ?></small>
                                </td>
                                <td><?php echo htmlspecialchars($visite['motif']); ?></td>
                                <td>
                                    <?php if ($visite['correspondant_nom']): ?>
                                        <strong><?php echo htmlspecialchars($visite['correspondant_prenoms'] . ' ' . $visite['correspondant_nom']); ?></strong>
                                        <?php if ($visite['departement']): ?>
                                            <br><small class="text-muted"><?php echo htmlspecialchars($visite['departement']); ?></small>
                                        <?php endif; ?>
                                    <?php else: ?>
                                        <span class="text-muted">Visite libre</span>
                                    <?php endif; ?>
                                </td>
                                <td>
                                    <span class="badge badge-success"><?php echo date('H:i', strtotime($visite['heure_entree'])); ?></span>
                                </td>
                                <td>
                                    <?php
                                    $entree = new DateTime($visite['date_visite'] . ' ' . $visite['heure_entree']);
                                    $maintenant = new DateTime();
                                    $diff = $entree->diff($maintenant);
                                    $duree = $diff->h . 'h ' . $diff->i . 'min';
                                    ?>
                                    <span class="text-primary font-monospace"><?php echo $duree; ?></span>
                                </td>
                                <td>
                                    <div class="btn-group btn-group-sm">
                                        <a href="sortie.php?visite_id=<?php echo $visite['id']; ?>" 
                                           class="btn btn-success" title="Enregistrer sortie">
                                            <i class="bi bi-box-arrow-right"></i>
                                        </a>
                                    </div>
                                </td>
                            </tr>
                            <?php endforeach; ?>
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    </div>
</div>
<?php endif; ?>

<!-- Toutes les visites du jour -->
<div class="row">
    <div class="col-12">
        <div class="card">
            <div class="card-header d-flex justify-content-between align-items-center">
                <h5 class="card-title mb-0">
                    <i class="bi bi-list"></i> Toutes les visites du <?php echo date('d/m/Y', strtotime($date_selected)); ?>
                </h5>
                <div>
                    <a href="export_visites_excel.php" class="btn btn-sm btn-outline-success">
                        <i class="bi bi-file-earmark-excel"></i> Export Excel
                    </a>
                </div>
            </div>
            <div class="card-body p-0">
                <?php if (empty($visites)): ?>
                    <div class="p-5 text-center text-muted">
                        <i class="bi bi-calendar-x h1"></i>
                        <h5>Aucune visite enregistrée</h5>
                        <p>Aucune visite n'a été enregistrée pour cette date.</p>
                        <a href="nouvelle_visite.php" class="btn btn-primary">
                            <i class="bi bi-plus-circle"></i> Enregistrer une visite
                        </a>
                    </div>
                <?php else: ?>
                    <div class="table-responsive">
                        <table class="table table-hover mb-0">
                            <thead class="table-light">
                                <tr>
                                    <th>Visiteur</th>
                                    <th>Identité</th>
                                    <th>Motif</th>
                                    <th>Correspondant</th>
                                    <th>Entrée</th>
                                    <th>Sortie</th>
                                    <th>Durée</th>
                                    <th>Statut</th>
                                    <th>Actions</th>
                                </tr>
                            </thead>
                            <tbody>
                                <?php foreach ($visites as $visite): ?>
                                <tr>
                                    <td>
                                        <strong><?php echo htmlspecialchars($visite['prenoms'] . ' ' . $visite['nom']); ?></strong>
                                        <?php if ($visite['telephone']): ?>
                                            <br><small class="text-muted">
                                                <i class="bi bi-telephone"></i> <?php echo htmlspecialchars($visite['telephone']); ?>
                                            </small>
                                        <?php endif; ?>
                                    </td>
                                    <td>
                                        <span class="badge badge-primary"><?php echo strtoupper($visite['type_identite']); ?></span>
                                        <br><small class="font-monospace"><?php echo htmlspecialchars($visite['numero_identite']); ?></small>
                                    </td>
                                    <td><?php echo htmlspecialchars($visite['motif']); ?></td>
                                    <td>
                                        <?php if ($visite['correspondant_nom']): ?>
                                            <strong><?php echo htmlspecialchars($visite['correspondant_prenoms'] . ' ' . $visite['correspondant_nom']); ?></strong>
                                            <?php if ($visite['departement']): ?>
                                                <br><small class="text-muted"><?php echo htmlspecialchars($visite['departement']); ?></small>
                                            <?php endif; ?>
                                        <?php else: ?>
                                            <span class="text-muted">Visite libre</span>
                                        <?php endif; ?>
                                    </td>
                                    <td>
                                        <span class="badge badge-success"><?php echo date('H:i', strtotime($visite['heure_entree'])); ?></span>
                                        <?php if ($visite['agent_entree']): ?>
                                            <br><small class="text-muted"><?php echo htmlspecialchars($visite['agent_entree']); ?></small>
                                        <?php endif; ?>
                                    </td>
                                    <td>
                                        <?php if ($visite['heure_sortie']): ?>
                                            <span class="badge badge-secondary"><?php echo date('H:i', strtotime($visite['heure_sortie'])); ?></span>
                                            <?php if ($visite['agent_sortie']): ?>
                                                <br><small class="text-muted"><?php echo htmlspecialchars($visite['agent_sortie']); ?></small>
                                            <?php endif; ?>
                                        <?php else: ?>
                                            <span class="text-muted">-</span>
                                        <?php endif; ?>
                                    </td>
                                    <td>
                                        <span class="font-monospace">
                                            <?php echo calculate_duree_visite($visite['date_visite'] . ' ' . $visite['heure_entree'], 
                                                                            $visite['heure_sortie'] ? $visite['date_visite'] . ' ' . $visite['heure_sortie'] : null); ?>
                                        </span>
                                    </td>
                                    <td>
                                        <?php
                                        $status_class = '';
                                        $status_text = '';
                                        switch ($visite['statut']) {
                                            case 'en_cours':
                                                $status_class = 'badge-warning';
                                                $status_text = 'En cours';
                                                break;
                                            case 'terminee':
                                                $status_class = 'badge-success';
                                                $status_text = 'Terminée';
                                                break;
                                            case 'annulee':
                                                $status_class = 'badge-danger';
                                                $status_text = 'Annulée';
                                                break;
                                        }
                                        ?>
                                        <span class="badge <?php echo $status_class; ?>"><?php echo $status_text; ?></span>
                                    </td>
                                    <td>
                                        <div class="btn-group btn-group-sm">
                                            <?php if ($visite['statut'] == 'en_cours' && !$visite['heure_sortie']): ?>
                                                <a href="sortie.php?visite_id=<?php echo $visite['id']; ?>" 
                                                   class="btn btn-success" title="Enregistrer sortie">
                                                    <i class="bi bi-box-arrow-right"></i>
                                                </a>
                                            <?php endif; ?>
                                            <button class="btn btn-outline-info" 
                                                    onclick="voirDetails(<?php echo $visite['id']; ?>)" title="Détails">
                                                <i class="bi bi-eye"></i>
                                            </button>
                                        </div>
                                    </td>
                                </tr>
                                <?php endforeach; ?>
                            </tbody>
                        </table>
                    </div>
                <?php endif; ?>
            </div>
        </div>
    </div>
</div>

<!-- Modal pour les détails de visite -->
<div class="modal fade" id="detailsModal" tabindex="-1">
    <div class="modal-dialog modal-lg">
        <div class="modal-content">
            <div class="modal-header">
                <h5 class="modal-title">
                    <i class="bi bi-info-circle"></i> Détails de la visite
                </h5>
                <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
            </div>
            <div class="modal-body" id="detailsContent">
                <!-- Contenu chargé dynamiquement -->
            </div>
            <div class="modal-footer">
                <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Fermer</button>
            </div>
        </div>
    </div>
</div>

<?php
$additional_js = ['../../assets/js/visites.js'];
// include '../../includes/footer.php';
?>

<script>
// Fonction pour afficher les détails d'une visite
function voirDetails(visiteId) {
    fetch('get_visite_details.php?id=' + visiteId)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                document.getElementById('detailsContent').innerHTML = data.html;
                new bootstrap.Modal(document.getElementById('detailsModal')).show();
            } else {
                alert('Erreur lors du chargement des détails');
            }
        })
        .catch(error => {
            console.error('Erreur:', error);
            alert('Erreur lors du chargement des détails');
        });
}

// Auto-refresh toutes les 30 secondes pour les visites en cours
setInterval(function() {
    if (document.querySelector('.card.border-warning')) {
        location.reload();
    }
}, 30000);

// Navigation rapide par clavier
document.addEventListener('keydown', function(e) {
    if (e.ctrlKey) {
        switch(e.key) {
            case 'n':
                e.preventDefault();
                window.location.href = 'nouvelle_visite.php';
                break;
            case 's':
                e.preventDefault();
                window.location.href = 'sortie.php';
                break;
            case 'f':
                e.preventDefault();
                document.getElementById('date').focus();
                break;
        }
    }
});
</script>
