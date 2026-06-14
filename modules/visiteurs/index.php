<?php
require_once __DIR__ . '/../../config/config.php';
require_once __DIR__ . '/visiteurs_functions.php';

// Vérifier la session
if (!is_logged_in()) {
    redirect('../../modules/auth/login.php');
}

$page_title = 'Gestion des visiteurs';

// Paramètres de pagination et tri
$page = isset($_GET['page']) ? max(1, (int)$_GET['page']) : 1;
$per_page = 20;
$order_by = isset($_GET['order']) && in_array($_GET['order'], ['nom', 'prenoms', 'date_creation', 'numero_identite']) 
            ? $_GET['order'] : 'nom';

// Récupérer les visiteurs
$result = get_all_visiteurs($page, $per_page, $order_by);
$visiteurs = $result['visiteurs'];
$total = $result['total'];
$total_pages = $result['pages'];

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
            <i class="bi bi-people"></i> Gestion des visiteurs
        </h1>
        <p class="text-muted mb-0">
            <?php echo number_format($total, 0, ',', ' '); ?> visiteur<?php echo $total > 1 ? 's' : ''; ?> enregistré<?php echo $total > 1 ? 's' : ''; ?>
        </p>
    </div>
    <div class="col-md-4 text-md-end">
        <div class="btn-group" role="group">
            <a href="ajouter.php" class="btn btn-primary">
                <i class="bi bi-person-plus"></i> Nouveau visiteur
            </a>
            <a href="rechercher.php" class="btn btn-outline-primary">
                <i class="bi bi-search"></i> Rechercher
            </a>
        </div>
    </div>
</div>

---

<div class="row mb-4">
    <div class="col-md-8">
        <div class="card">
            <div class="card-body py-2">
                <div class="row g-3 align-items-center">
                    <div class="col-md-4">
                        <div class="input-group input-group-sm">
                            <input type="text" class="form-control" id="quickSearch" 
                                   placeholder="Recherche rapide..." autocomplete="off">
                            <button class="btn btn-outline-secondary" type="button" id="btnQuickSearch">
                                <i class="bi bi-search"></i>
                            </button>
                        </div>
                    </div>
                    <div class="col-md-3">
                        <select class="form-select form-select-sm" onchange="changeOrder(this.value)">
                            <option value="nom" <?php echo $order_by == 'nom' ? 'selected' : ''; ?>>
                                Trier par nom
                            </option>
                            <option value="prenoms" <?php echo $order_by == 'prenoms' ? 'selected' : ''; ?>>
                                Trier par prénom
                            </option>
                            <option value="date_creation" <?php echo $order_by == 'date_creation' ? 'selected' : ''; ?>>
                                Plus récents
                            </option>
                            <option value="numero_identite" <?php echo $order_by == 'numero_identite' ? 'selected' : ''; ?>>
                                Par n° identité
                            </option>
                        </select>
                    </div>
                    <div class="col-md-5 text-end">
                        <small class="text-muted">
                            <?php 
                            $start = ($page - 1) * $per_page + 1;
                            $end = min($page * $per_page, $total);
                            echo "{$start}-{$end} sur {$total}";
                            ?>
                        </small>
                    </div>
                </div>
            </div>
        </div>
    </div>
    <div class="col-md-4">
        <div class="card">
            <div class="card-body py-2 text-center">
                <div class="row">
                    <div class="col-4">
                        <div class="text-primary h5 mb-0">
                            <?php
                            $pdo = get_db_connection();
                            $stmt = $pdo->prepare("
                                SELECT COUNT(DISTINCT v.id) 
                                FROM visiteurs v
                                JOIN visites vi ON v.id = vi.visiteur_id
                                WHERE DATE(vi.date_visite) = CURDATE()
                            ");
                            $stmt->execute();
                            echo $stmt->fetchColumn();
                            ?>
                        </div>
                        <small class="text-muted">Aujourd'hui</small>
                    </div>
                    <div class="col-4">
                        <div class="text-success h5 mb-0">
                            <?php
                            $stmt = $pdo->prepare("
                                SELECT COUNT(DISTINCT v.id) 
                                FROM visiteurs v
                                JOIN visites vi ON v.id = vi.visiteur_id
                                WHERE vi.date_visite >= DATE_SUB(CURDATE(), INTERVAL 7 DAY)
                            ");
                            $stmt->execute();
                            echo $stmt->fetchColumn();
                            ?>
                        </div>
                        <small class="text-muted">7 jours</small>
                    </div>
                    <div class="col-4">
                        <div class="text-info h5 mb-0">
                            <?php
                            $stmt = $pdo->prepare("
                                SELECT COUNT(DISTINCT v.id) 
                                FROM visiteurs v
                                JOIN visites vi ON v.id = vi.visiteur_id
                                WHERE vi.date_visite >= DATE_SUB(CURDATE(), INTERVAL 30 DAY)
                            ");
                            $stmt->execute();
                            echo $stmt->fetchColumn();
                            ?>
                        </div>
                        <small class="text-muted">30 jours</small>
                    </div>
                </div>
            </div>
        </div>
    </div>
</div>

---

<div class="card">
    <div class="card-header d-flex justify-content-between align-items-center">
        <h5 class="card-title mb-0">
            <i class="bi bi-list"></i> Liste des visiteurs
        </h5>
        <div>
            <a href="export_visiteurs_excel.php" class="btn btn-sm btn-outline-success">
                <i class="bi bi-file-earmark-excel"></i> Export Excel
            </a>
        </div>
    </div>
    <div class="card-body p-0">
        <?php if (empty($visiteurs)): ?>
            <div class="p-5 text-center text-muted">
                <i class="bi bi-people h1"></i>
                <h5>Aucun visiteur enregistré</h5>
                <p>Commencez par ajouter des visiteurs au système.</p>
                <a href="ajouter.php" class="btn btn-primary">
                    <i class="bi bi-person-plus"></i> Ajouter un visiteur
                </a>
            </div>
        <?php else: ?>
            <div class="table-responsive">
                <table class="table table-hover mb-0">
                    <thead class="table-light">
                        <tr>
                            <th>
                                <a href="?order=nom&page=<?php echo $page; ?>" class="text-decoration-none">
                                    Nom et prénom
                                    <?php if ($order_by == 'nom'): ?>
                                        <i class="bi bi-sort-alpha-down text-primary"></i>
                                    <?php endif; ?>
                                </a>
                            </th>
                            <th>
                                <a href="?order=numero_identite&page=<?php echo $page; ?>" class="text-decoration-none">
                                    Identité
                                    <?php if ($order_by == 'numero_identite'): ?>
                                        <i class="bi bi-sort-alpha-down text-primary"></i>
                                    <?php endif; ?>
                                </a>
                            </th>
                            <th>Contact</th>
                            <th>Visites</th>
                            <th>Dernière visite</th>
                            <th>Statut</th>
                            <th width="120">Actions</th>
                        </tr>
                    </thead>
                    <tbody>
                        <?php foreach ($visiteurs as $visiteur): ?>
                        <tr>
                            <td>
                                <div class="d-flex align-items-center">
                                    <div class="avatar-circle me-2">
                                        <?php echo strtoupper(substr($visiteur['prenoms'], 0, 1) . substr($visiteur['nom'], 0, 1)); ?>
                                    </div>
                                    <div>
                                        <strong><?php echo htmlspecialchars($visiteur['prenoms'] . ' ' . $visiteur['nom']); ?></strong>
                                        <br><small class="text-muted">
                                            Créé le <?php echo date('d/m/Y', strtotime($visiteur['date_creation'])); ?>
                                        </small>
                                    </div>
                                </div>
                            </td>
                            <td>
                                <span class="badge badge-primary">
                                    <?php echo strtoupper($visiteur['type_identite']); ?>
                                </span>
                                <br><small class="font-monospace">
                                    <?php echo htmlspecialchars($visiteur['numero_identite']); ?>
                                </small>
                            </td>
                            <td>
                                <?php if ($visiteur['telephone']): ?>
                                    <div class="mb-1">
                                        <i class="bi bi-telephone text-primary"></i>
                                        <a href="tel:<?php echo $visiteur['telephone']; ?>" class="text-decoration-none">
                                            <?php echo htmlspecialchars($visiteur['telephone']); ?>
                                        </a>
                                    </div>
                                <?php endif; ?>
                                <?php if ($visiteur['email']): ?>
                                    <div>
                                        <i class="bi bi-envelope text-primary"></i>
                                        <a href="mailto:<?php echo $visiteur['email']; ?>" class="text-decoration-none">
                                            <?php echo htmlspecialchars($visiteur['email']); ?>
                                        </a>
                                    </div>
                                <?php endif; ?>
                                <?php if (!$visiteur['telephone'] && !$visiteur['email']): ?>
                                    <span class="text-muted">Aucun contact</span>
                                <?php endif; ?>
                            </td>
                            <td>
                                <div class="d-flex flex-column">
                                    <span class="badge badge-info mb-1">
                                        <?php echo $visiteur['nb_visites']; ?> visite<?php echo $visiteur['nb_visites'] > 1 ? 's' : ''; ?>
                                    </span>
                                    <?php if ($visiteur['visites_en_cours'] > 0): ?>
                                        <span class="badge badge-warning">
                                            <i class="bi bi-clock"></i> En cours
                                        </span>
                                    <?php endif; ?>
                                </div>
                            </td>
                            <td>
                                <?php if ($visiteur['derniere_visite']): ?>
                                    <?php
                                    $date_visite = new DateTime($visiteur['derniere_visite']);
                                    $aujourd_hui = new DateTime();
                                    $diff = $aujourd_hui->diff($date_visite);
                                    
                                    if ($diff->days == 0) {
                                        echo '<span class="text-success fw-bold">Aujourd\'hui</span>';
                                    } elseif ($diff->days == 1) {
                                        echo '<span class="text-warning">Hier</span>';
                                    } elseif ($diff->days <= 7) {
                                        echo '<span class="text-info">Il y a ' . $diff->days . ' jours</span>';
                                    } else {
                                        echo '<span class="text-muted">' . date('d/m/Y', strtotime($visiteur['derniere_visite'])) . '</span>';
                                    }
                                    ?>
                                <?php else: ?>
                                    <span class="text-muted">Jamais</span>
                                <?php endif; ?>
                            </td>
                            <td>
                                <?php if ($visiteur['visites_en_cours'] > 0): ?>
                                    <span class="badge badge-warning">
                                        <i class="bi bi-person-check"></i> Présent
                                    </span>
                                <?php elseif ($visiteur['nb_visites'] > 0): ?>
                                    <span class="badge badge-success">
                                        <i class="bi bi-check-circle"></i> Actif
                                    </span>
                                <?php else: ?>
                                    <span class="badge badge-secondary">
                                        <i class="bi bi-person"></i> Nouveau
                                    </span>
                                <?php endif; ?>
                            </td>
                            <td>
                                <div class="btn-group btn-group-sm">
                                    <button class="btn btn-outline-info" 
                                            onclick="voirProfil(<?php echo $visiteur['id']; ?>)" 
                                            title="Voir le profil">
                                        <i class="bi bi-eye"></i>
                                    </button>
                                    <a href="modifier.php?id=<?php echo $visiteur['id']; ?>" 
                                       class="btn btn-outline-primary" title="Modifier">
                                        <i class="bi bi-pencil"></i>
                                    </a>
                                    <a href="historique.php?id=<?php echo $visiteur['id']; ?>" 
                                       class="btn btn-outline-secondary" title="Historique">
                                        <i class="bi bi-clock-history"></i>
                                    </a>
                                    <div class="btn-group btn-group-sm">
                                        <button class="btn btn-outline-secondary dropdown-toggle dropdown-toggle-split" 
                                                data-bs-toggle="dropdown" title="Plus d'actions">
                                            <i class="bi bi-three-dots"></i>
                                        </button>
                                        <ul class="dropdown-menu">
                                            <li>
                                                <a class="dropdown-item" 
                                                   href="../visites/nouvelle_visite.php?visiteur_id=<?php echo $visiteur['id']; ?>">
                                                    <i class="bi bi-plus-circle text-success"></i> Nouvelle visite
                                                </a>
                                            </li>
                                            <li>
                                                <button class="dropdown-item" 
                                                        onclick="dupliquerVisiteur(<?php echo $visiteur['id']; ?>)">
                                                    <i class="bi bi-files text-info"></i> Dupliquer
                                                </button>
                                            </li>
                                            <li><hr class="dropdown-divider"></li>
                                            <li>
                                                <button class="dropdown-item text-danger" 
                                                        onclick="supprimerVisiteur(<?php echo $visiteur['id']; ?>, '<?php echo htmlspecialchars($visiteur['prenoms'] . ' ' . $visiteur['nom'], ENT_QUOTES); ?>')">
                                                    <i class="bi bi-trash"></i> Supprimer
                                                </button>
                                            </li>
                                        </ul>
                                    </div>
                                </div>
                            </td>
                        </tr>
                        <?php endforeach; ?>
                    </tbody>
                </table>
            </div>
            
            <?php if ($total_pages > 1): ?>
            <div class="card-footer">
                <nav aria-label="Pagination des visiteurs">
                    <ul class="pagination pagination-sm justify-content-center mb-0">
                        <?php if ($page > 1): ?>
                            <li class="page-item">
                                <a class="page-link" href="?page=<?php echo $page - 1; ?>&order=<?php echo $order_by; ?>">
                                    <i class="bi bi-chevron-left"></i> Précédent
                                </a>
                            </li>
                        <?php endif; ?>
                        
                        <?php
                        $start_page = max(1, $page - 2);
                        $end_page = min($total_pages, $page + 2);
                        
                        if ($start_page > 1): ?>
                            <li class="page-item">
                                <a class="page-link" href="?page=1&order=<?php echo $order_by; ?>">1</a>
                            </li>
                            <?php if ($start_page > 2): ?>
                                <li class="page-item disabled">
                                    <span class="page-link">...</span>
                                </li>
                            <?php endif;
                        endif;
                        
                        for ($i = $start_page; $i <= $end_page; $i++): ?>
                            <li class="page-item <?php echo $i == $page ? 'active' : ''; ?>">
                                <a class="page-link" href="?page=<?php echo $i; ?>&order=<?php echo $order_by; ?>">
                                    <?php echo $i; ?>
                                </a>
                            </li>
                        <?php endfor;
                        
                        if ($end_page < $total_pages): ?>
                            <?php if ($end_page < $total_pages - 1): ?>
                                <li class="page-item disabled">
                                    <span class="page-link">...</span>
                                </li>
                            <?php endif; ?>
                            <li class="page-item">
                                <a class="page-link" href="?page=<?php echo $total_pages; ?>&order=<?php echo $order_by; ?>">
                                    <?php echo $total_pages; ?>
                                </a>
                            </li>
                        <?php endif;
                        
                        if ($page < $total_pages): ?>
                            <li class="page-item">
                                <a class="page-link" href="?page=<?php echo $page + 1; ?>&order=<?php echo $order_by; ?>">
                                    Suivant <i class="bi bi-chevron-right"></i>
                                </a>
                            </li>
                        <?php endif; ?>
                    </ul>
                </nav>
            </div>
            <?php endif; ?>
        <?php endif; ?>
    </div>
</div>

<div class="modal fade" id="profilModal" tabindex="-1">
    <div class="modal-dialog modal-lg">
        <div class="modal-content">
            <div class="modal-header">
                <h5 class="modal-title">
                    <i class="bi bi-person-circle"></i> Profil du visiteur
                </h5>
                <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
            </div>
            <div class="modal-body" id="profilContent">
                </div>
            <div class="modal-footer">
                <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Fermer</button>
            </div>
        </div>
    </div>
</div>

<div id="quickSearchResults" class="position-fixed bg-white border rounded shadow-lg p-3" 
     style="display: none; top: 70px; right: 20px; width: 400px; z-index: 1050; max-height: 400px; overflow-y: auto;">
    </div>

<?php
$additional_css = ['visiteurs.css'];
$additional_js = ['visiteurs.js'];
// include '../../includes/footer.php';
?>

<style>
.avatar-circle {
    width: 40px;
    height: 40px;
    background: linear-gradient(135deg, var(--primary-color), var(--secondary-color));
    color: white;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: bold;
    font-size: 0.8rem;
}

.table-hover tbody tr:hover {
    background-color: var(--light-blue) !important;
}

#quickSearchResults .search-item {
    padding: 0.5rem;
    border-bottom: 1px solid var(--gray-200);
    cursor: pointer;
    transition: background-color 0.2s;
}

#quickSearchResults .search-item:hover {
    background-color: var(--light-blue);
}

#quickSearchResults .search-item:last-child {
    border-bottom: none;
}
</style>

<script>
// Variables globales
let searchTimeout;

// Fonction pour recherche rapide
function quickSearch(query) {
    const resultsDiv = document.getElementById('quickSearchResults');
    if (query.length < 2) {
        resultsDiv.style.display = 'none';
        return;
    }
    
    fetch('search_ajax.php?q=' + encodeURIComponent(query))
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => {
            displayQuickResults(data);
        })
        .catch(error => {
            console.error('Erreur recherche:', error);
            resultsDiv.innerHTML = '<div class="text-danger text-center">Erreur de recherche</div>';
            resultsDiv.style.display = 'block';
        });
}

// Fonction pour afficher les résultats rapides
function displayQuickResults(visiteurs) {
    const resultsDiv = document.getElementById('quickSearchResults');
    
    if (visiteurs.length === 0) {
        resultsDiv.innerHTML = '<div class="text-muted text-center">Aucun résultat</div>';
        resultsDiv.style.display = 'block';
        return;
    }
    
    let html = '';
    visiteurs.forEach(function(visiteur) {
        html += `
            <div class="search-item" onclick="voirProfil(${visiteur.id})">
                <div class="d-flex align-items-center">
                    <div class="avatar-circle me-2">
                        ${visiteur.prenoms.charAt(0).toUpperCase()}${visiteur.nom.charAt(0).toUpperCase()}
                    </div>
                    <div>
                        <div class="fw-bold">${visiteur.prenoms} ${visiteur.nom}</div>
                        <small class="text-muted">
                            <span class="badge bg-primary text-white">${visiteur.type_identite.toUpperCase()}</span>
                            ${visiteur.numero_identite}
                        </small>
                        ${visiteur.telephone ? `<br><small class="text-muted"><i class="bi bi-telephone"></i> ${visiteur.telephone}</small>` : ''}
                    </div>
                </div>
            </div>`;
    });
    
    resultsDiv.innerHTML = html;
    resultsDiv.style.display = 'block';
}

// Fonction pour voir le profil d'un visiteur
function voirProfil(visiteurId) {
    fetch('get_profil.php?id=' + visiteurId)
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => {
            if (data.success) {
                document.getElementById('profilContent').innerHTML = data.html;
                new bootstrap.Modal(document.getElementById('profilModal')).show();
            } else {
                alert('Erreur lors du chargement du profil: ' + data.message);
            }
        })
        .catch(error => {
            console.error('Erreur:', error);
            alert('Erreur lors du chargement du profil.');
        });
}

// Fonction pour dupliquer un visiteur
function dupliquerVisiteur(visiteurId) {
    if (confirm('Voulez-vous dupliquer ce visiteur ?')) {
        fetch('duplicate_visiteur.php', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({visiteur_id: visiteurId})
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => {
            if (data.success) {
                alert('Visiteur dupliqué avec succès.');
                location.reload();
            } else {
                alert('Erreur: ' + data.message);
            }
        })
        .catch(error => {
            console.error('Erreur:', error);
            alert('Erreur lors de la duplication du visiteur.');
        });
    }
}

// Fonction pour supprimer un visiteur
function supprimerVisiteur(visiteurId, nomComplet) {
    if (confirm(`Êtes-vous sûr de vouloir supprimer le visiteur "${nomComplet}" ?\n\nCette action est irréversible et supprimera toutes ses visites.`)) {
        fetch('delete_visiteur.php', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({visiteur_id: visiteurId})
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => {
            if (data.success) {
                alert('Visiteur supprimé avec succès.');
                location.reload();
            } else {
                alert('Erreur: ' + data.message);
            }
        })
        .catch(error => {
            console.error('Erreur:', error);
            alert('Erreur lors de la suppression du visiteur.');
        });
    }
}

// Fonction pour changer l'ordre de tri
function changeOrder(order) {
    window.location.href = `?page=1&order=${order}`;
}

// Event listeners
document.addEventListener('DOMContentLoaded', function() {
    const quickSearchInput = document.getElementById('quickSearch');
    const quickSearchBtn = document.getElementById('btnQuickSearch');
    
    // Recherche rapide
    quickSearchInput.addEventListener('input', function() {
        clearTimeout(searchTimeout);
        searchTimeout = setTimeout(() => {
            quickSearch(this.value);
        }, 300);
    });
    
    quickSearchBtn.addEventListener('click', function() {
        quickSearch(quickSearchInput.value);
    });
    
    // Fermer les résultats quand on clique ailleurs
    document.addEventListener('click', function(e) {
        if (!e.target.closest('#quickSearch') && !e.target.closest('#quickSearchResults')) {
            document.getElementById('quickSearchResults').style.display = 'none';
        }
    });
    
    // Raccourcis clavier
    document.addEventListener('keydown', function(e) {
        if (e.ctrlKey) {
            switch(e.key) {
                case 'f':
                    e.preventDefault();
                    quickSearchInput.focus();
                    break;
                case 'n':
                    e.preventDefault();
                    window.location.href = 'ajouter.php';
                    break;
            }
        }
        
        if (e.key === 'Escape') {
            document.getElementById('quickSearchResults').style.display = 'none';
        }
    });
});

// Animation des lignes au chargement
document.addEventListener('DOMContentLoaded', function() {
    const rows = document.querySelectorAll('tbody tr');
    rows.forEach((row, index) => {
        row.style.opacity = '0';
        row.style.transform = 'translateY(20px)';
        row.style.transition = 'all 0.3s ease';
        
        setTimeout(() => {
            row.style.opacity = '1';
            row.style.transform = 'translateY(0)';
        }, index * 50);
    });
});
</script>