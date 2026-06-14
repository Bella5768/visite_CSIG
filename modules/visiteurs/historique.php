<?php
require_once __DIR__ . '/../../config/config.php';
require_once __DIR__ . '/visiteurs_functions.php';
require_once __DIR__ . '/../visites/visites_functions.php';

// Vérifier la session
// Vérifier la session
if (!is_logged_in()) {
    redirect('../../modules/auth/login.php');
}

// Récupérer l'ID du visiteur
$visiteur_id = isset($_GET['id']) ? (int)$_GET['id'] : 0;

if (empty($visiteur_id)) {
    set_flash_message('danger', 'Visiteur non spécifié');
    redirect('index.php');
}

// Récupérer les informations du visiteur
$visiteur = get_visiteur_by_id($visiteur_id);
if (!$visiteur) {
    set_flash_message('danger', 'Visiteur introuvable');
    redirect('index.php');
}

// Récupérer l'historique et les statistiques
$historique = get_visiteur_historique($visiteur_id, 50);
$stats = get_visiteur_stats($visiteur_id);

$page_title = 'Historique de ' . $visiteur['prenoms'] . ' ' . $visiteur['nom'];

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
            <i class="bi bi-clock-history"></i> Historique des visites
        </h1>
        <p class="text-muted mb-0">
            Historique complet des visites de ce visiteur
        </p>
    </div>
    <div class="col-md-4 text-md-end">
        <div class="btn-group">
            <a href="index.php" class="btn btn-outline-secondary">
                <i class="bi bi-arrow-left"></i> Retour à la liste
            </a>
            <a href="../visites/nouvelle_visite.php?visiteur_id=<?php echo $visiteur['id']; ?>" class="btn btn-success">
                <i class="bi bi-plus-circle"></i> Nouvelle visite
            </a>
        </div>
    </div>
</div>

<div class="row">
    <div class="col-lg-4">
        <!-- Profil du visiteur -->
        <div class="card">
            <div class="card-header bg-primary text-white">
                <h5 class="card-title mb-0">
                    <i class="bi bi-person-circle"></i> Profil du visiteur
                </h5>
            </div>
            <div class="card-body">
                <div class="text-center mb-3">
                    <div class="avatar-circle mx-auto mb-2" style="width: 80px; height: 80px; font-size: 1.5rem;">
                        <?php echo strtoupper(substr($visiteur['prenoms'], 0, 1) . substr($visiteur['nom'], 0, 1)); ?>
                    </div>
                    <h5 class="mb-1"><?php echo htmlspecialchars($visiteur['prenoms'] . ' ' . $visiteur['nom']); ?></h5>
                    <span class="badge badge-primary">
                        <?php echo strtoupper($visiteur['type_identite']); ?>
                    </span>
                </div>
                
                <div class="mb-3">
                    <label class="text-muted small">Numéro d'identité</label>
                    <div class="font-monospace fw-bold"><?php echo htmlspecialchars($visiteur['numero_identite']); ?></div>
                </div>
                
                <?php if ($visiteur['telephone']): ?>
                <div class="mb-3">
                    <label class="text-muted small">Téléphone</label>
                    <div>
                        <i class="bi bi-telephone text-primary"></i>
                        <a href="tel:<?php echo $visiteur['telephone']; ?>" class="text-decoration-none">
                            <?php echo htmlspecialchars($visiteur['telephone']); ?>
                        </a>
                    </div>
                </div>
                <?php endif; ?>
                
                <?php if ($visiteur['email']): ?>
                <div class="mb-3">
                    <label class="text-muted small">Email</label>
                    <div>
                        <i class="bi bi-envelope text-primary"></i>
                        <a href="mailto:<?php echo $visiteur['email']; ?>" class="text-decoration-none">
                            <?php echo htmlspecialchars($visiteur['email']); ?>
                        </a>
                    </div>
                </div>
                <?php endif; ?>
                
                <?php if ($visiteur['adresse']): ?>
                <div class="mb-3">
                    <label class="text-muted small">Adresse</label>
                    <div><?php echo nl2br(htmlspecialchars($visiteur['adresse'])); ?></div>
                </div>
                <?php endif; ?>
                
                <div class="mb-3">
                    <label class="text-muted small">Enregistré le</label>
                    <div><?php echo date('d/m/Y à H:i', strtotime($visiteur['date_creation'])); ?></div>
                </div>
                
                <div class="d-grid gap-2">
                    <a href="modifier.php?id=<?php echo $visiteur['id']; ?>" class="btn btn-outline-primary">
                        <i class="bi bi-pencil"></i> Modifier
                    </a>
                    <a href="../visites/nouvelle_visite.php?visiteur_id=<?php echo $visiteur['id']; ?>" class="btn btn-success">
                        <i class="bi bi-plus-circle"></i> Nouvelle visite
                    </a>
                </div>
            </div>
        </div>
        
        <!-- Statistiques -->
        <div class="card mt-3">
            <div class="card-header">
                <h6 class="card-title mb-0">
                    <i class="bi bi-graph-up"></i> Statistiques
                </h6>
            </div>
            <div class="card-body">
                <?php $stats_gen = $stats['generales']; ?>
                
                <div class="row text-center mb-3">
                    <div class="col-6">
                        <div class="text-primary h3 mb-1"><?php echo $stats_gen['total_visites'] ?? 0; ?></div>
                        <small class="text-muted">Total visites</small>
                    </div>
                    <div class="col-6">
                        <div class="text-success h3 mb-1"><?php echo $stats_gen['visites_terminees'] ?? 0; ?></div>
                        <small class="text-muted">Terminées</small>
                    </div>
                </div>
                
                <?php if (!empty($stats_gen['premiere_visite'])): ?>
                <div class="mb-3">
                    <label class="text-muted small">Première visite</label>
                    <div><?php echo date('d/m/Y', strtotime($stats_gen['premiere_visite'])); ?></div>
                </div>
                <?php endif; ?>
                
                <?php if (!empty($stats_gen['derniere_visite'])): ?>
                <div class="mb-3">
                    <label class="text-muted small">Dernière visite</label>
                    <div><?php echo date('d/m/Y', strtotime($stats_gen['derniere_visite'])); ?></div>
                </div>
                <?php endif; ?>
                
                <?php if (!empty($stats_gen['duree_moyenne_minutes'])): ?>
                <div class="mb-3">
                    <label class="text-muted small">Durée moyenne</label>
                    <div>
                        <?php 
                        $duree_moy = round($stats_gen['duree_moyenne_minutes']);
                        echo floor($duree_moy / 60) . 'h ' . ($duree_moy % 60) . 'min';
                        ?>
                    </div>
                </div>
                <?php endif; ?>
                
                <?php if ($stats_gen['visites_en_cours'] > 0): ?>
                <div class="alert alert-warning">
                    <i class="bi bi-exclamation-triangle"></i>
                    <strong><?php echo $stats_gen['visites_en_cours']; ?></strong> visite(s) en cours
                </div>
                <?php endif; ?>
            </div>
        </div>
        
        <!-- Motifs les plus fréquents -->
        <?php if (!empty($stats['motifs_frequents'])): ?>
        <div class="card mt-3">
            <div class="card-header">
                <h6 class="card-title mb-0">
                    <i class="bi bi-pie-chart"></i> Motifs fréquents
                </h6>
            </div>
            <div class="card-body">
                <?php foreach ($stats['motifs_frequents'] as $motif): ?>
                <div class="d-flex justify-content-between align-items-center mb-2">
                    <div class="small"><?php echo htmlspecialchars($motif['libelle']); ?></div>
                    <span class="badge badge-info"><?php echo $motif['nb_visites']; ?></span>
                </div>
                <?php endforeach; ?>
            </div>
        </div>
        <?php endif; ?>
        
        <!-- Correspondants fréquents -->
        <?php if (!empty($stats['correspondants_frequents'])): ?>
        <div class="card mt-3">
            <div class="card-header">
                <h6 class="card-title mb-0">
                    <i class="bi bi-person-badge"></i> Correspondants fréquents
                </h6>
            </div>
            <div class="card-body">
                <?php foreach ($stats['correspondants_frequents'] as $correspondant): ?>
                <div class="d-flex justify-content-between align-items-center mb-2">
                    <div class="small">
                        <?php echo htmlspecialchars($correspondant['prenoms'] . ' ' . $correspondant['nom']); ?>
                        <?php if ($correspondant['departement']): ?>
                            <br><span class="text-muted" style="font-size: 0.75rem;">
                                <?php echo htmlspecialchars($correspondant['departement']); ?>
                            </span>
                        <?php endif; ?>
                    </div>
                    <span class="badge badge-secondary"><?php echo $correspondant['nb_visites']; ?></span>
                </div>
                <?php endforeach; ?>
            </div>
        </div>
        <?php endif; ?>
    </div>
    
    <div class="col-lg-8">
        <!-- Historique des visites -->
        <div class="card">
            <div class="card-header d-flex justify-content-between align-items-center">
                <h5 class="card-title mb-0">
                    <i class="bi bi-list-ul"></i> Historique des visites
                    <span class="badge badge-primary ms-2"><?php echo count($historique); ?></span>
                </h5>
                <div>
                    <a href="export_historique.php?visiteur_id=<?php echo $visiteur['id']; ?>" 
                       class="btn btn-sm btn-outline-success">
                        <i class="bi bi-download"></i> Exporter
                    </a>
                </div>
            </div>
            <div class="card-body p-0">
                <?php if (empty($historique)): ?>
                    <div class="p-5 text-center text-muted">
                        <i class="bi bi-calendar-x h1"></i>
                        <h5>Aucune visite enregistrée</h5>
                        <p>Ce visiteur n'a encore effectué aucune visite.</p>
                        <a href="../visites/nouvelle_visite.php?visiteur_id=<?php echo $visiteur['id']; ?>" 
                           class="btn btn-success">
                            <i class="bi bi-plus-circle"></i> Enregistrer sa première visite
                        </a>
                    </div>
                <?php else: ?>
                    <!-- Timeline des visites -->
                    <div class="timeline p-3">
                        <?php foreach ($historique as $index => $visite): ?>
                            <div class="timeline-item">
                                <div class="timeline-marker">
                                    <?php if ($visite['statut'] == 'en_cours'): ?>
                                        <i class="bi bi-clock text-warning"></i>
                                    <?php elseif ($visite['statut'] == 'terminee'): ?>
                                        <i class="bi bi-check-circle text-success"></i>
                                    <?php else: ?>
                                        <i class="bi bi-x-circle text-danger"></i>
                                    <?php endif; ?>
                                </div>
                                <div class="timeline-content">
                                    <div class="card mb-3">
                                        <div class="card-body">
                                            <div class="row">
                                                <div class="col-md-8">
                                                    <h6 class="card-title mb-2">
                                                        <i class="bi bi-calendar3"></i>
                                                        <?php echo date('d/m/Y', strtotime($visite['date_visite'])); ?>
                                                        
                                                        <!-- Statut -->
                                                        <?php
                                                        $status_class = $status_text = $status_icon = '';
                                                        switch ($visite['statut']) {
                                                            case 'en_cours':
                                                                $status_class = 'badge-warning';
                                                                $status_text = 'En cours';
                                                                $status_icon = 'bi-clock';
                                                                break;
                                                            case 'terminee':
                                                                $status_class = 'badge-success';
                                                                $status_text = 'Terminée';
                                                                $status_icon = 'bi-check-circle';
                                                                break;
                                                            case 'annulee':
                                                                $status_class = 'badge-danger';
                                                                $status_text = 'Annulée';
                                                                $status_icon = 'bi-x-circle';
                                                                break;
                                                        }
                                                        ?>
                                                        <span class="badge <?php echo $status_class; ?> ms-2">
                                                            <i class="<?php echo $status_icon; ?>"></i> <?php echo $status_text; ?>
                                                        </span>
                                                    </h6>
                                                    
                                                    <p class="mb-2">
                                                        <strong>Motif :</strong> <?php echo htmlspecialchars($visite['motif']); ?>
                                                        
                                                        <?php if ($visite['type_visite'] == 'avec_rdv'): ?>
                                                            <span class="badge badge-info ms-2">
                                                                <i class="bi bi-calendar-check"></i> Avec RDV
                                                            </span>
                                                        <?php endif; ?>
                                                    </p>
                                                    
                                                    <?php if ($visite['correspondant_nom']): ?>
                                                        <p class="mb-2">
                                                            <i class="bi bi-person-badge"></i>
                                                            <strong>Correspondant :</strong>
                                                            <?php echo htmlspecialchars($visite['correspondant_prenoms'] . ' ' . $visite['correspondant_nom']); ?>
                                                            <?php if ($visite['departement']): ?>
                                                                <br><small class="text-muted ms-3">
                                                                    <?php echo htmlspecialchars($visite['departement']); ?>
                                                                </small>
                                                            <?php endif; ?>
                                                        </p>
                                                    <?php else: ?>
                                                        <p class="mb-2 text-muted">
                                                            <i class="bi bi-unlock"></i> Visite libre
                                                        </p>
                                                    <?php endif; ?>
                                                    
                                                    <?php if ($visite['observations']): ?>
                                                        <div class="mt-2">
                                                            <small class="text-muted">Observations :</small>
                                                            <div class="border-start border-primary ps-2 small">
                                                                <?php echo nl2br(htmlspecialchars($visite['observations'])); ?>
                                                            </div>
                                                        </div>
                                                    <?php endif; ?>
                                                </div>
                                                
                                                <div class="col-md-4">
                                                    <!-- Horaires -->
                                                    <div class="mb-3">
                                                        <div class="d-flex justify-content-between align-items-center mb-1">
                                                            <small class="text-muted">Entrée</small>
                                                            <span class="badge badge-success">
                                                                <?php echo date('H:i', strtotime($visite['heure_entree'])); ?>
                                                            </span>
                                                        </div>
                                                        
                                                        <div class="d-flex justify-content-between align-items-center mb-1">
                                                            <small class="text-muted">Sortie</small>
                                                            <?php if ($visite['heure_sortie']): ?>
                                                                <span class="badge badge-secondary">
                                                                    <?php echo date('H:i', strtotime($visite['heure_sortie'])); ?>
                                                                </span>
                                                            <?php else: ?>
                                                                <span class="text-muted small">En cours</span>
                                                            <?php endif; ?>
                                                        </div>
                                                        
                                                        <div class="d-flex justify-content-between align-items-center">
                                                            <small class="text-muted">Durée</small>
                                                            <span class="font-monospace small">
                                                                <?php echo calculate_duree_visite(
                                                                    $visite['date_visite'] . ' ' . $visite['heure_entree'], 
                                                                    $visite['heure_sortie'] ? $visite['date_visite'] . ' ' . $visite['heure_sortie'] : null
                                                                ); ?>
                                                            </span>
                                                        </div>
                                                    </div>
                                                    
                                                    <!-- Agents -->
                                                    <?php if ($visite['agent_entree']): ?>
                                                        <div class="mb-1">
                                                            <small class="text-muted">Agent entrée :</small>
                                                            <br><small><?php echo htmlspecialchars($visite['agent_entree']); ?></small>
                                                        </div>
                                                    <?php endif; ?>
                                                    
                                                    <?php if ($visite['agent_sortie']): ?>
                                                        <div class="mb-1">
                                                            <small class="text-muted">Agent sortie :</small>
                                                            <br><small><?php echo htmlspecialchars($visite['agent_sortie']); ?></small>
                                                        </div>
                                                    <?php endif; ?>
                                                    
                                                    <!-- Actions -->
                                                    <div class="mt-3">
                                                        <?php if ($visite['statut'] == 'en_cours'): ?>
                                                            <a href="../visites/sortie.php?visite_id=<?php echo $visite['id']; ?>" 
                                                               class="btn btn-success btn-sm">
                                                                <i class="bi bi-box-arrow-right"></i> Sortie
                                                            </a>
                                                        <?php endif; ?>
                                                        
                                                        <button class="btn btn-outline-info btn-sm" 
                                                                onclick="voirDetailsVisite(<?php echo $visite['id']; ?>)">
                                                            <i class="bi bi-eye"></i> Détails
                                                        </button>
                                                    </div>
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        <?php endforeach; ?>
                    </div>
                    
                    <?php if (count($historique) >= 50): ?>
                        <div class="card-footer">
                            <div class="alert alert-info mb-0">
                                <i class="bi bi-info-circle"></i>
                                Seules les 50 dernières visites sont affichées.
                                <a href="export_historique.php?visiteur_id=<?php echo $visiteur['id']; ?>" class="alert-link">
                                    Exporter l'historique complet
                                </a>
                            </div>
                        </div>
                    <?php endif; ?>
                <?php endif; ?>
            </div>
        </div>
        
        <!-- Graphique des visites par mois (si données disponibles) -->
        <?php if (!empty($stats['visites_par_mois'])): ?>
        <div class="card mt-3">
            <div class="card-header">
                <h6 class="card-title mb-0">
                    <i class="bi bi-bar-chart"></i> Évolution des visites (12 derniers mois)
                </h6>
            </div>
            <div class="card-body">
                <canvas id="visitsChart" height="100"></canvas>
            </div>
        </div>
        <?php endif; ?>
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

<?php // include '../../includes/footer.php'; ?>

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

.timeline {
    position: relative;
}

.timeline-item {
    position: relative;
    padding-left: 50px;
    margin-bottom: 30px;
}

.timeline-item:not(:last-child):before {
    content: '';
    position: absolute;
    left: 20px;
    top: 30px;
    bottom: -30px;
    width: 2px;
    background: var(--gray-300);
}

.timeline-marker {
    position: absolute;
    left: 0;
    top: 8px;
    width: 40px;
    height: 40px;
    background: white;
    border: 2px solid var(--gray-300);
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1.1rem;
}

.timeline-content {
    flex: 1;
}

.timeline-item:hover .timeline-marker {
    border-color: var(--primary-color);
    background: var(--light-blue);
}
</style>

<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>

<script>
// Fonction pour voir les détails d'une visite
function voirDetailsVisite(visiteId) {
    fetch('../visites/get_visite_details.php?id=' + visiteId)
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

// Graphique des visites par mois
<?php if (!empty($stats['visites_par_mois'])): ?>
document.addEventListener('DOMContentLoaded', function() {
    const ctx = document.getElementById('visitsChart').getContext('2d');
    
    const data = {
        labels: <?php echo json_encode(array_map(function($item) {
            return date('M Y', strtotime($item['mois'] . '-01'));
        }, $stats['visites_par_mois'])); ?>,
        datasets: [{
            label: 'Nombre de visites',
            data: <?php echo json_encode(array_column($stats['visites_par_mois'], 'nb_visites')); ?>,
            backgroundColor: 'rgba(30, 58, 138, 0.1)',
            borderColor: 'rgba(30, 58, 138, 1)',
            borderWidth: 2,
            fill: true,
            tension: 0.4
        }]
    };
    
    const config = {
        type: 'line',
        data: data,
        options: {
            responsive: true,
            plugins: {
                legend: {
                    display: false
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        stepSize: 1
                    }
                }
            }
        }
    };
    
    new Chart(ctx, config);
});
<?php endif; ?>

// Animation au scroll pour la timeline
document.addEventListener('DOMContentLoaded', function() {
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.style.opacity = '1';
                entry.target.style.transform = 'translateX(0)';
            }
        });
    }, { threshold: 0.1 });
    
    document.querySelectorAll('.timeline-item').forEach((item, index) => {
        item.style.opacity = '0';
        item.style.transform = 'translateX(-20px)';
        item.style.transition = `all 0.5s ease ${index * 0.1}s`;
        observer.observe(item);
    });
});

// Raccourcis clavier
document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape') {
        // Fermer les modals ouvertes
        const modals = document.querySelectorAll('.modal.show');
        modals.forEach(modal => {
            bootstrap.Modal.getInstance(modal).hide();
        });
    } else if (e.ctrlKey && e.key === 'n') {
        e.preventDefault();
        window.location.href = '../visites/nouvelle_visite.php?visiteur_id=<?php echo $visiteur['id']; ?>';
    }
});

// Impression de la page
function printHistory() {
    window.print();
}

// Fonction pour exporter l'historique
function exportHistory(format) {
    window.location.href = `export_historique.php?visiteur_id=<?php echo $visiteur['id']; ?>&format=${format}`;
}
</script>

<style media="print">
@media print {
    .btn, .card-header, .timeline-marker {
        display: none !important;
    }
    
    .timeline-item {
        break-inside: avoid;
        page-break-inside: avoid;
    }
    
    .card {
        border: 1px solid #ddd !important;
        box-shadow: none !important;
    }
}
</style>