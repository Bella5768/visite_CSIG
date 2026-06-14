<?php
require_once __DIR__ . '/../../config/config.php';

// Vérifier la session
if (!is_logged_in()) {
    redirect('../../modules/auth/login.php');
}

header("Content-Type: application/vnd.ms-excel");
header("Content-Disposition: attachment; filename=visiteurs_" . date("Y-m-d") . ".xls");
header("Pragma: no-cache");
header("Expires: 0");

$pdo = get_db_connection();

$sql = "
    SELECT v.nom, v.prenoms, v.type_identite, v.numero_identite,
           v.telephone, v.email, v.date_creation
    FROM visiteurs v
    ORDER BY v.nom ASC
";
$stmt = $pdo->prepare($sql);
$stmt->execute();
$visiteurs = $stmt->fetchAll(PDO::FETCH_ASSOC);

echo "<table border='1'>";
echo "<tr>
        <th>Nom</th>
        <th>Prénoms</th>
        <th>Type pièce</th>
        <th>N° pièce</th>
        <th>Téléphone</th>
        <th>Email</th>
        <th>Date création</th>
      </tr>";

foreach ($visiteurs as $v) {
    echo "<tr>";
    echo "<td>" . htmlspecialchars($v['nom']) . "</td>";
    echo "<td>" . htmlspecialchars($v['prenoms']) . "</td>";
    echo "<td>" . htmlspecialchars($v['type_identite']) . "</td>";
    echo "<td>" . htmlspecialchars($v['numero_identite']) . "</td>";
    echo "<td>" . htmlspecialchars($v['telephone']) . "</td>";
    echo "<td>" . htmlspecialchars($v['email']) . "</td>";
    echo "<td>" . date('d/m/Y H:i', strtotime($v['date_creation'])) . "</td>";
    echo "</tr>";
}
echo "</table>";
