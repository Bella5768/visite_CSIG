<?php
require_once __DIR__ . '/../../config/config.php';
require_once __DIR__ . '/../visites/visites_functions.php';

// Si l'utilisateur n'est pas connecté, le rediriger
if (!is_logged_in()) {
    redirect('../../modules/auth/login.php');
}

$page_title = 'Rapport du jour';
$rapport_visites = get_daily_report();

$css_path = '../../assets/css/';
$js_path = '../../assets/js/';
$base_url = '../../';
$modules_path = '../';

include '../../includes/header.php';
?>

<div class="row mb-4">
    <div class="col-md-12">
        <h1 class="h3 mb-2 text-primary">
            <i class="bi bi-file-earmark-text"></i> Rapport du jour
        </h1>
        <p class="text-muted mb-0">
            Liste des visites enregistrées le <?php echo date('d/m/Y'); ?>
        </p>
    </div>
</div>

<div class="row">
    <div class="col-12">
        <div class="card shadow-sm">
            
            <!-- En-tête avec fond bleu comme tes autres cartes -->
            <div class="card-header bg-primary text-white">
                <i class="bi bi-journal-text"></i> Rapport du jour (<?php echo count($rapport_visites); ?> visites)
            </div>

            <div class="card-body">
                <?php if (empty($rapport_visites)): ?>
                    <div class="alert alert-info" role="alert">
                        <i class="bi bi-info-circle"></i> Aucune visite n'a été enregistrée pour cette journée.
                    </div>
                <?php else: ?>
                    <div class="table-responsive">
                        <table class="table table-striped table-hover">
                            <thead class="table-primary">
                                <tr>
                                    <th>#</th>
                                    <th>Visiteur</th>
                                    <th>Téléphone</th>
                                    <th>Motif</th>
                                    <th>Correspondant</th>
                                    <th>Heure d'entrée</th>
                                    <th>Heure de sortie</th>
                                </tr>
                            </thead>
                            <tbody>
                                <?php foreach ($rapport_visites as $visite): ?>
                                    <tr>
                                        <td><?php echo htmlspecialchars($visite['id']); ?></td>
                                        <td><?php echo htmlspecialchars($visite['prenoms'] . ' ' . $visite['nom']); ?></td>
                                        <td><?php echo htmlspecialchars($visite['telephone']); ?></td>
                                        <td><?php echo htmlspecialchars($visite['motif_libelle']); ?></td>
                                        <td>
                                            <?php 
                                            echo ($visite['correspondant_prenoms']) 
                                                ? htmlspecialchars($visite['correspondant_prenoms'] . ' ' . $visite['correspondant_nom']) 
                                                : 'Visite libre'; 
                                            ?>
                                        </td>
                                        <td><?php echo date('H:i', strtotime($visite['heure_entree'])); ?></td>
                                        <td>
                                            <?php 
                                            echo ($visite['heure_sortie']) 
                                                ? date('H:i', strtotime($visite['heure_sortie'])) 
                                                : 'En cours'; 
                                            ?>
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

<?php include '../../includes/footer.php'; ?>
