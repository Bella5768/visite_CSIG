<?php 
require_once __DIR__ . '/../../config/config.php';

// Vérifier la session
if (!is_logged_in()) {
    redirect('../../modules/auth/login.php');
}

$page_title = 'Recherche simple visiteurs';
$results = [];
$search_performed = false;
$search_term = '';

/**
 * Fonction locale pour rechercher un visiteur
 */
function search_visiteurs($criteria, $limit = 50) {
    try {
        $pdo = get_db_connection();
        
        $where_conditions = [];
        $params = [];
        
        if (!empty($criteria['search_term'])) {
            $search_term = '%' . $criteria['search_term'] . '%';
            $where_conditions[] = "(v.nom LIKE :search 
                                   OR v.prenoms LIKE :search 
                                   OR v.telephone LIKE :search
                                   OR v.numero_identite LIKE :search
                                   OR v.email LIKE :search
                                   OR v.adresse LIKE :search)";
            $params[':search'] = $search_term;
        }
        
        $where_clause = empty($where_conditions) ? '' : 'WHERE ' . implode(' AND ', $where_conditions);
        
        // ⚠️ On injecte directement la limite (après cast en entier)
        $limit = (int)$limit;

        $sql = "
            SELECT v.id, v.nom, v.prenoms, v.telephone, v.date_creation,
                   COUNT(vi.id) as nb_visites,
                   MAX(vi.date_visite) as derniere_visite
            FROM visiteurs v
            LEFT JOIN visites vi ON v.id = vi.visiteur_id
            {$where_clause}
            GROUP BY v.id, v.nom, v.prenoms, v.telephone, v.date_creation
            ORDER BY v.nom, v.prenoms
            LIMIT {$limit}
        ";
        
        $stmt = $pdo->prepare($sql);
        $stmt->execute($params);
        
        return $stmt->fetchAll(PDO::FETCH_ASSOC);
        
    } catch (Exception $e) {
        error_log("Erreur recherche visiteurs : " . $e->getMessage());
        return [];
    }
}

// Traitement de la recherche
if ($_SERVER['REQUEST_METHOD'] == 'POST' || !empty($_GET)) {
    $search_performed = true;
    $search_term = trim($_POST['search_term'] ?? $_GET['search_term'] ?? '');

    if (!empty($search_term)) {
        $results = search_visiteurs(['search_term' => $search_term], 100);
    }
}

// Chemins
$css_path     = '../../assets/css/';
$js_path      = '../../assets/js/';
$base_url     = '../../';
$modules_path = '../';

include '../../includes/header.php';
?>

<div class="row mb-4">
    <div class="col-md-8">
        <h1 class="h3 mb-2 text-primary">
            <i class="bi bi-search"></i> Recherche simple
        </h1>
        <p class="text-muted mb-0">
            Recherchez un visiteur par son <strong>nom</strong>, <strong>prénom</strong>, <strong>téléphone</strong>, <strong>pièce</strong> ou <strong>email</strong>.
        </p>
    </div>
    <div class="col-md-4 text-md-end">
        <a href="index.php" class="btn btn-outline-secondary">
            <i class="bi bi-arrow-left"></i> Retour à la liste
        </a>
    </div>
</div>

<div class="card">
    <div class="card-body">
        <form method="POST" action="">
            <div class="row g-3 align-items-center">
                <div class="col-md-10">
                    <label for="search_term" class="form-label">Recherche</label>
                    <input type="text" class="form-control" id="search_term" name="search_term"
                           value="<?php echo htmlspecialchars($search_term); ?>"/>
                </div>
                <div class="col-md-2 d-flex align-items-end">
                    <button type="submit" class="btn btn-primary w-100">
                        <i class="bi bi-search"></i> Rechercher
                    </button>
                </div>
            </div>
            <div class="mt-2">
                <a href="rechercher.php" class="btn btn-outline-secondary btn-sm">
                    Réinitialiser
                </a>
            </div>
        </form>
    </div>
</div>

<?php if ($search_performed): ?>
    <div class="card mt-4">
        <div class="card-header d-flex justify-content-between align-items-center">
            <h5 class="card-title mb-0">
                <i class="bi bi-list-ul"></i> Résultats de recherche
                <span class="badge bg-primary ms-2"><?php echo count($results); ?></span>
            </h5>
        </div>
        <div class="card-body p-0">
            <?php if (empty($results)): ?>
                <div class="p-5 text-center text-muted">
                    <i class="bi bi-search h1"></i>
                    <h5>Aucun visiteur trouvé</h5>
                </div>
            <?php else: ?>
                <div class="table-responsive">
                    <table class="table table-hover mb-0">
                        <thead class="table-light">
                            <tr>
                                <th>Nom</th>
                                <th>Prénoms</th>
                                <th>Téléphone</th>
                                <th>Date création</th>
                                <th>Actions</th>
                            </tr>
                        </thead>
                        <tbody>
                            <?php foreach ($results as $v): ?>
                                <tr>
                                    <td><?php echo htmlspecialchars($v['nom']); ?></td>
                                    <td><?php echo htmlspecialchars($v['prenoms']); ?></td>
                                    <td><?php echo htmlspecialchars($v['telephone']); ?></td>
                                    <td><?php echo !empty($v['date_creation']) ? date('d/m/Y', strtotime($v['date_creation'])) : '-'; ?></td>
                                    <td>
                                        <div class="btn-group btn-group-sm">
                                            <a href="modifier.php?id=<?php echo $v['id']; ?>" class="btn btn-outline-primary">
                                                <i class="bi bi-pencil"></i>
                                            </a>
                                            <a href="../visites/nouvelle_visite.php?visiteur_id=<?php echo $v['id']; ?>" 
                                               class="btn btn-outline-success">
                                                <i class="bi bi-plus-circle"></i>
                                            </a>
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

<?php include '../../includes/footer.php'; ?>
