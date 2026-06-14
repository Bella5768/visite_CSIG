<?php
require_once __DIR__ . '/../../config/config.php';

// Vérifier la session
if (!is_logged_in()) {
    redirect('../../modules/auth/login.php');
}

header("Content-Type: application/vnd.ms-excel");
header("Content-Disposition: attachment; filename=visites_" . date("Y-m-d") . ".xls");
header("Pragma: no-cache");
header("Expires: 0");

$pdo = get_db_connection();

$sql = "
    SELECT v.nom, v.prenoms, v.type_identite, v.numero_identite,
           v.telephone, v.email, vi.date_visite, vi.objet_visite, vi.statut
    FROM visites vi
    JOIN visiteurs v ON vi.visiteur_id = v.id
    ORDER BY vi.date_visite DESC
";
$stmt = $pdo->prepare($sql);
$stmt->execute();
$visites = $stmt->fetchAll(PDO::FETCH_ASSOC);

echo "<table border='1'>";
echo "<tr>
        <th>Nom</th>
        <th>Prénoms</th>
        <th>Type pièce</th>
        <th>N° pièce</th>
        <th>Téléphone</th>
        <th>Email</th>
        <th>Date visite</th>
        <th>Objet visite</th>
        <th>Statut</th>
      </tr>";

foreach ($visites as $v) {
    echo "<tr>";
    echo "<td>" . htmlspecialchars($v['nom']) . "</td>";
    echo "<td>" . htmlspecialchars($v['prenoms']) . "</td>";
    echo "<td>" . htmlspecialchars($v['type_identite']) . "</td>";
    echo "<td>" . htmlspecialchars($v['numero_identite']) . "</td>";
    echo "<td>" . htmlspecialchars($v['telephone']) . "</td>";
    echo "<td>" . htmlspecialchars($v['email']) . "</td>";
    echo "<td>" . date('d/m/Y H:i', strtotime($v['date_visite'])) . "</td>";
    echo "<td>" . htmlspecialchars($v['objet_visite']) . "</td>";
    echo "<td>" . htmlspecialchars($v['statut']) . "</td>";
    echo "</tr>";
}
echo "</table>";
