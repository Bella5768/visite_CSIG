<?php
require_once 'config/config.php';

// Si non connecté, rediriger vers la page de connexion
if (!is_logged_in()) {
    redirect('modules/auth/login.php');
}

$page_title = 'Tableau de bord';
$user = get_current_user2();

// Récupérer les statistiques du jour
try {
    $pdo = get_db_connection();
    
    // Visites du jour
    $stmt = $pdo->prepare("
        SELECT COUNT(*) as total_visites_jour 
        FROM visites 
        WHERE DATE(date_visite) = CURDATE()
    ");
    $stmt->execute();
    $visites_jour = $stmt->fetch(PDO::FETCH_ASSOC)['total_visites_jour'];
    
    // Visites en cours (non sorties)
    $stmt = $pdo->prepare("
        SELECT COUNT(*) as visites_en_cours 
        FROM visites 
        WHERE DATE(date_visite) = CURDATE() AND heure_sortie IS NULL
    ");
    $stmt->execute();
    $visites_en_cours = $stmt->fetch(PDO::FETCH_ASSOC)['visites_en_cours'];
    
    // Total visiteurs enregistrés
    $stmt = $pdo->prepare("SELECT COUNT(*) as total_visiteurs FROM visiteurs");
    $stmt->execute();
    $total_visiteurs = $stmt->fetch(PDO::FETCH_ASSOC)['total_visiteurs'];
    
    // Visites du mois
    $stmt = $pdo->prepare("
        SELECT COUNT(*) as visites_mois 
        FROM visites 
        WHERE YEAR(date_visite) = YEAR(CURDATE()) 
        AND MONTH(date_visite) = MONTH(CURDATE())
    ");
    $stmt->execute();
    $visites_mois = $stmt->fetch(PDO::FETCH_ASSOC)['visites_mois'];
    
    // Dernières visites
    $stmt = $pdo->prepare("
        SELECT v.id, vi.nom, vi.prenoms, v.heure_entree, v.heure_sortie,
               m.libelle as motif, c.nom as correspondant_nom, c.prenoms as correspondant_prenoms,
               v.type_visite, v.statut
        FROM visites v
        JOIN visiteurs vi ON v.visiteur_id = vi.id
        JOIN motifs_visite m ON v.motif_id = m.id
        LEFT JOIN correspondants c ON v.correspondant_id = c.id
        WHERE DATE(v.date_visite) = CURDATE()
        ORDER BY v.heure_entree DESC
        LIMIT 10
    ");
    $stmt->execute();
    $dernieres_visites = $stmt->fetchAll(PDO::FETCH_ASSOC);
    
} catch (Exception $e) {
    error_log("Erreur récupération statistiques : " . $e->getMessage());
    $visites_jour = $visites_en_cours = $total_visiteurs = $visites_mois = 0;
    $dernieres_visites = [];
}

include 'includes/header.php';
?>

<div class="row mb-4">
    <div class="col-12">
        <div class="d-flex justify-content-between align-items-center">
            <div class="d-flex align-items-center gap-3">
                <h2 class="h3 mb-2 text-primary mb-0">
                    <i class="bi bi-speedometer2"></i> CITÉ DES SCIENCES ET DE L'INNOVATION DE GUINÉE
                </h2>
                <!-- Bouton Prendre rendez-vous -->
                <a href="https://outlook.office.com/book/RencontrezPrAbdoulayeBanirDIALLO@csig.edu.gn/" 
                   target="_blank" 
                   class="btn btn-success btn-sm">
                    <i class="bi bi-calendar-check"></i> Prendre rendez-vous
                </a>
            </div>
            <div class="text-end">
                <div class="text-primary h4 mb-1 current-time">
                    <?php echo date('d/m/Y H:i:s'); ?>
                </div>
                <small class="text-muted">Heure locale</small>
            </div>
        </div>
        <p class="text-muted mt-2 mb-0">
            Bienvenue, <strong><?php echo $user['prenoms'] . ' ' . $user['nom']; ?></strong> 
            - <?php echo ucfirst($user['role']); ?> - <?php echo $user['poste']; ?>
        </p>
    </div>
</div>

<!-- Statistiques du jour -->
<div class="row mb-4 dashboard-stats">
    <div class="col-xl-3 col-md-6 mb-4">
        <div class="card">
            <div class="card-body">
                <div class="stat-number"><?php echo $visites_jour; ?></div>
                <div class="stat-label">
                    <i class="bi bi-calendar-day"></i> Visites aujourd'hui
                </div>
            </div>
        </div>
    </div>
    
    <div class="col-xl-3 col-md-6 mb-4">
        <div class="card">
            <div class="card-body">
                <div class="stat-number"><?php echo $visites_en_cours; ?></div>
                <div class="stat-label">
                    <i class="bi bi-clock"></i> Visites en cours
                </div>
            </div>
        </div>
    </div>
    
    <div class="col-xl-3 col-md-6 mb-4">
        <div class="card">
            <div class="card-body">
                <div class="stat-number"><?php echo $total_visiteurs; ?></div>
                <div class="stat-label">
                    <i class="bi bi-people"></i> Visiteurs enregistrés
                </div>
            </div>
        </div>
    </div>
    
    <div class="col-xl-3 col-md-6 mb-4">
        <div class="card">
            <div class="card-body">
                <div class="stat-number"><?php echo $visites_mois; ?></div>
                <div class="stat-label">
                    <i class="bi bi-calendar-month"></i> Visites ce mois
                </div>
            </div>
        </div>
    </div>
</div>

<div class="row">
    <!-- Actions rapides -->
    <div class="col-lg-4 mb-4">
        <div class="card">
            <div class="card-header">
                <h5 class="card-title mb-0">
                    <i class="bi bi-lightning"></i> Actions rapides
                </h5>
            </div>
            <div class="card-body">
                <div class="d-grid gap-2">
                    <a href="modules/visites/nouvelle_visite.php" class="btn btn-primary">
                        <i class="bi bi-plus-circle"></i> Nouvelle visite
                    </a>
                    <a href="modules/visiteurs/rechercher.php" class="btn btn-outline-primary">
                        <i class="bi bi-search"></i> Rechercher visiteur
                    </a>
                    <a href="modules/visites/sortie.php" class="btn btn-success">
                        <i class="bi bi-box-arrow-right"></i> Enregistrer sortie
                    </a>
                    <a href="modules/rapports/rapport_journalier.php" class="btn btn-outline-secondary">
                        <i class="bi bi-file-earmark-text"></i> Rapport du jour
                    </a>
                </div>
            </div>
        </div>
        
        <!-- Météo du système -->
        <div class="card mt-3">
            <div class="card-header">
                <h6 class="card-title mb-0">
                    <i class="bi bi-info-circle"></i> État du système
                </h6>
            </div>
            <div class="card-body">
                <div class="row text-center">
                    <div class="col-6">
                        <div class="text-success h2">
                            <i class="bi bi-check-circle"></i>
                        </div>
                        <small>Système OK</small>
                    </div>
                    <div class="col-6">
                        <div class="text-primary h2">
                            <i class="bi bi-database"></i>
                        </div>
                        <small>Base de données</small>
                    </div>
                </div>
            </div>
        </div>
    </div>
    
    <!-- Dernières visites -->
    <div class="col-lg-8 mb-4">
        <div class="card">
            <div class="card-header d-flex justify-content-between align-items-center">
                <h5 class="card-title mb-0">
                    <i class="bi bi-clock-history"></i> Dernières visites du jour
                </h5>
                <a href="modules/visites/index.php" class="btn btn-sm btn-outline-primary">
                    Voir toutes <i class="bi bi-arrow-right"></i>
                </a>
            </div>
            <div class="card-body p-0">
                <?php if (empty($dernieres_visites)): ?>
                    <div class="p-4 text-center text-muted">
                        <i class="bi bi-calendar-x h1"></i>
                        <p class="mb-0">Aucune visite enregistrée aujourd'hui</p>
                    </div>
                <?php else: ?>
                    <div class="table-responsive">
                        <table class="table table-hover mb-0">
                            <thead class="table-light">
                                <tr>
                                    <th>Visiteur</th>
                                    <th>Motif</th>
                                    <th>Correspondant</th>
                                    <th>Entrée</th>
                                    <th>Sortie</th>
                                    <th>Statut</th>
                                </tr>
                            </thead>
                            <tbody>
                                <?php foreach ($dernieres_visites as $visite): ?>
                                <tr>
                                    <td>
                                        <strong><?php echo htmlspecialchars($visite['prenoms'] . ' ' . $visite['nom']); ?></strong>
                                    </td>
                                    <td>
                                        <small class="text-muted"><?php echo htmlspecialchars($visite['motif']); ?></small>
                                    </td>
                                    <td>
                                        <?php if ($visite['correspondant_nom']): ?>
                                            <small><?php echo htmlspecialchars($visite['correspondant_prenoms'] . ' ' . $visite['correspondant_nom']); ?></small>
                                        <?php else: ?>
                                            <span class="text-muted">Visite libre</span>
                                        <?php endif; ?>
                                    </td>
                                    <td>
                                        <span class="badge badge-primary"><?php echo date('H:i', strtotime($visite['heure_entree'])); ?></span>
                                    </td>
                                    <td>
                                        <?php if ($visite['heure_sortie']): ?>
                                            <span class="badge badge-success"><?php echo date('H:i', strtotime($visite['heure_sortie'])); ?></span>
                                        <?php else: ?>
                                            <span class="text-muted">-</span>
                                        <?php endif; ?>
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

<?php include 'includes/footer.php'; ?>
