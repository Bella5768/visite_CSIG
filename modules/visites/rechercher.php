<?php
require_once __DIR__.'/../../config/config.php';
require_once __DIR__.'/visites_functions.php';

// Vérification connexion
if (!is_logged_in()) {
    redirect('../../modules/auth/login.php');
}

$page_title = 'Recherche de visites';
$results = [];
$search_performed = false;

// Récupérer les données pour les filtres
$motifs = get_motifs_visite();
$correspondants = get_correspondants();

// Critères par défaut
$criteria = [
    'numero_identite'  => '',
    'nom'              => '',
    'date_debut'       => '',
    'date_fin'         => '',
    'motif_id'         => 0,
    'correspondant_id' => 0,
    'statut'           => ''
];

// Traitement de la recherche
if ($_SERVER['REQUEST_METHOD'] === 'POST' || !empty($_GET)) {
    $search_performed = true;
    
    $criteria = [
        'numero_identite'  => sanitize_input($_POST['numero_identite'] ?? $_GET['numero_identite'] ?? ''),
        'nom'              => sanitize_input($_POST['nom'] ?? $_GET['nom'] ?? ''),
        'date_debut'       => sanitize_input($_POST['date_debut'] ?? $_GET['date_debut'] ?? ''),
        'date_fin'         => sanitize_input($_POST['date_fin'] ?? $_GET['date_fin'] ?? ''),
        'motif_id'         => (int)($_POST['motif_id'] ?? $_GET['motif_id'] ?? 0),
        'correspondant_id' => (int)($_POST['correspondant_id'] ?? $_GET['correspondant_id'] ?? 0),
        'statut'           => sanitize_input($_POST['statut'] ?? $_GET['statut'] ?? '')
    ];
    
    $results = search_visites($criteria);
}

// Variables de navigation
$css_path     = '../../assets/css/';
$js_path      = '../../assets/js/';
$base_url     = '../../';
$modules_path = '../';

include '../../includes/header.php';
?>

<div class="row mb-4">
    <div class="col-md-8">
        <h1 class="h3 mb-2 text-primary">
            <i class="bi bi-search"></i> Recherche de visites
        </h1>
        <p class="text-muted mb-0">Recherchez des visites selon différents critères</p>
    </div>
    <div class="col-md-4 text-md-end">
        <a href="index.php" class="btn btn-outline-secondary">
            <i class="bi bi-arrow-left"></i> Retour aux visites
        </a>
    </div>
</div>

<div class="row">
    <div class="col-lg-3">
        <!-- Formulaire de recherche -->
        <div class="card sticky-top" style="top: 1rem;">
            <div class="card-header">
                <h5 class="card-title mb-0">
                    <i class="bi bi-funnel"></i> Critères de recherche
                </h5>
            </div>
            <div class="card-body">
                <form method="POST" action="" id="searchForm">
                    <!-- Nom/Prénom -->
                    <div class="mb-3">
                        <label for="nom" class="form-label">
                            <i class="bi bi-person"></i> Nom/Prénom du visiteur
                        </label>
                        <input type="text" class="form-control" id="nom" name="nom"
                               value="<?php echo htmlspecialchars($criteria['nom']); ?>"
                               placeholder="Nom ou prénom">
                    </div>
                    
                    <!-- Numéro identité -->
                    <div class="mb-3">
                        <label for="numero_identite" class="form-label">
                            <i class="bi bi-card-text"></i> Numéro d'identité
                        </label>
                        <input type="text" class="form-control" id="numero_identite" name="numero_identite"
                               value="<?php echo htmlspecialchars($criteria['numero_identite']); ?>"
                               placeholder="Numéro de pièce d'identité">
                    </div>
                    
                    <!-- Période -->
                    <div class="mb-3">
                        <label class="form-label">
                            <i class="bi bi-calendar-range"></i> Période
                        </label>
                        <div class="row g-2">
                            <div class="col-6">
                                <input type="date" class="form-control form-control-sm"
                                       id="date_debut" name="date_debut"
                                       value="<?php echo $criteria['date_debut']; ?>">
                                <small class="text-muted">Du</small>
                            </div>
                            <div class="col-6">
                                <input type="date" class="form-control form-control-sm"
                                       id="date_fin" name="date_fin"
                                       value="<?php echo $criteria['date_fin']; ?>">
                                <small class="text-muted">Au</small>
                            </div>
                        </div>
                    </div>
                    
                    <!-- Motif -->
                    <div class="mb-3">
                        <label for="motif_id" class="form-label">
                            <i class="bi bi-clipboard-check"></i> Motif de visite
                        </label>
                        <select class="form-select form-select-sm" id="motif_id" name="motif_id">
                            <option value="">Tous les motifs</option>
                            <?php foreach ($motifs as $motif): ?>
                                <option value="<?php echo $motif['id']; ?>"
                                    <?php echo ($criteria['motif_id'] == $motif['id']) ? 'selected' : ''; ?>>
                                    <?php echo htmlspecialchars($motif['libelle']); ?>
                                </option>
                            <?php endforeach; ?>
                        </select>
                    </div>
                    
                    <!-- Correspondant -->
                    <div class="mb-3">
                        <label for="correspondant_id" class="form-label">
                            <i class="bi bi-person-badge"></i> Correspondant
                        </label>
                        <select class="form-select form-select-sm" id="correspondant_id" name="correspondant_id">
                            <option value="">Tous les correspondants</option>
                            <option value="-1" <?php echo ($criteria['correspondant_id'] == -1) ? 'selected' : ''; ?>>
                                Visites libres uniquement
                            </option>
                            <?php foreach ($correspondants as $correspondant): ?>
                                <option value="<?php echo $correspondant['id']; ?>"
                                    <?php echo ($criteria['correspondant_id'] == $correspondant['id']) ? 'selected' : ''; ?>>
                                    <?php echo htmlspecialchars($correspondant['prenoms'] . ' ' . $correspondant['nom']); ?>
                                </option>
                            <?php endforeach; ?>
                        </select>
                    </div>
                    
                    <!-- Statut -->
                    <div class="mb-3">
                        <label for="statut" class="form-label">
                            <i class="bi bi-flag"></i> Statut
                        </label>
                        <select class="form-select form-select-sm" id="statut" name="statut">
                            <option value="">Tous les statuts</option>
                            <option value="en_cours"  <?php echo ($criteria['statut'] == 'en_cours') ? 'selected' : ''; ?>>En cours</option>
                            <option value="terminee"  <?php echo ($criteria['statut'] == 'terminee') ? 'selected' : ''; ?>>Terminée</option>
                            <option value="annulee"   <?php echo ($criteria['statut'] == 'annulee') ? 'selected' : ''; ?>>Annulée</option>
                        </select>
                    </div>
                    
                    <div class="d-grid gap-2">
                        <button type="submit" class="btn btn-primary">
                            <i class="bi bi-search"></i> Rechercher
                        </button>
                        <a href="rechercher.php" class="btn btn-outline-secondary btn-sm">
                            <i class="bi bi-arrow-clockwise"></i> Réinitialiser
                        </a>
                    </div>
                </form>
            </div>
        </div>
    </div>
    
    <div class="col-lg-9">
        <!-- Résultats -->
        <?php if ($search_performed): ?>
            <div class="card">
                <div class="card-header d-flex justify-content-between align-items-center">
                    <h5 class="card-title mb-0">
                        <i class="bi bi-list-ul"></i> Résultats de recherche
                        <span class="badge badge-primary ms-2"><?php echo count($results); ?></span>
                    </h5>
                    <?php if (!empty($results)): ?>
                        <div>
                            <a href="../statistiques/export.php?<?php echo http_build_query(array_merge($criteria, ['type' => 'search_results'])); ?>"
                               class="btn btn-sm btn-outline-success">
                                <i class="bi bi-download"></i> Exporter
                            </a>
                        </div>
                    <?php endif; ?>
                </div>
                <div class="card-body p-0">
                    <?php if (empty($results)): ?>
                        <div class="p-5 text-center text-muted">
                            <i class="bi bi-search h1"></i>
                            <h5>Aucun résultat trouvé</h5>
                        </div>
                    <?php else: ?>
                        <div class="table-responsive">
                            <table class="table table-hover mb-0">
                                <thead class="table-light">
                                    <tr>
                                        <th>Date</th>
                                        <th>Visiteur</th>
                                        <th>Identité</th>
                                        <th>Motif</th>
                                        <th>Correspondant</th>
                                        <th>Horaires</th>
                                        <th>Durée</th>
                                        <th>Statut</th>
                                        <th>Actions</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    <?php foreach ($results as $visite): ?>
                                        <tr>
                                            <td><?php echo date('d/m/Y', strtotime($visite['date_visite'])); ?></td>
                                            <td><strong><?php echo htmlspecialchars($visite['prenoms'].' '.$visite['nom']); ?></strong></td>
                                            <td>
                                                <span class="badge badge-primary"><?php echo strtoupper($visite['type_identite']); ?></span>
                                                <br><small><?php echo htmlspecialchars($visite['numero_identite']); ?></small>
                                            </td>
                                            <td><?php echo htmlspecialchars($visite['motif']); ?></td>
                                            <td>
                                                <?php if (!empty($visite['correspondant_nom'])): ?>
                                                    <strong><?php echo htmlspecialchars($visite['correspondant_prenoms'].' '.$visite['correspondant_nom']); ?></strong>
                                                <?php else: ?>
                                                    <span class="text-muted">Visite libre</span>
                                                <?php endif; ?>
                                            </td>
                                            <td>
                                                <span class="badge badge-success">
                                                    <?php echo date('H:i', strtotime($visite['heure_entree'])); ?>
                                                </span>
                                                <?php if ($visite['heure_sortie']): ?>
                                                    <span class="badge badge-secondary">
                                                        <?php echo date('H:i', strtotime($visite['heure_sortie'])); ?>
                                                    </span>
                                                <?php endif; ?>
                                            </td>
                                            <td><?php echo calculate_duree_visite($visite['date_visite'].' '.$visite['heure_entree'], $visite['heure_sortie'] ? $visite['date_visite'].' '.$visite['heure_sortie'] : null); ?></td>
                                            <td><?php echo htmlspecialchars($visite['statut']); ?></td>
                                            <td>
                                                <div class="btn-group btn-group-sm">
                                                    <button class="btn btn-outline-info" onclick="voirDetails(<?php echo $visite['id']; ?>)">
                                                        <i class="bi bi-eye"></i>
                                                    </button>
                                                    <?php if (!empty($visite['visiteur_id'])): ?>
                                                        <a href="../visiteurs/historique.php?id=<?php echo $visite['visiteur_id']; ?>"
                                                           class="btn btn-outline-secondary" target="_blank">
                                                            <i class="bi bi-clock-history"></i>
                                                        </a>
                                                    <?php endif; ?>
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
        <?php endif; ?>
    </div>
</div>
<?php
$additional_js = ['../../assets/js/visites.js'];
include '../../includes/footer.php';
?>