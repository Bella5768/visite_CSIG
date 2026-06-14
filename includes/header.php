<?php
if (!defined('APP_NAME')) {
    require_once 'config/config.php';
}
?>
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="description" content="Système de gestion des visites - Cité des Sciences et de l'Innovation de Guinée CSIG">
    <title><?php echo isset($page_title) ? $page_title . ' - ' . APP_NAME : APP_NAME; ?></title>
    
    <!-- Bootstrap CSS -->
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css" rel="stylesheet">
    
    <!-- Bootstrap Icons -->
    <link href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.1/font/bootstrap-icons.css" rel="stylesheet">
    
    <!-- Custom CSS -->
    <link href="<?php echo isset($css_path) ? $css_path : 'assets/css/'; ?>style.css" rel="stylesheet">
    
    <!-- Favicon -->
    <link rel="icon" type="image/x-icon" href="<?php echo isset($assets_path) ? $assets_path : 'assets/'; ?>images/favicon.ico">
    
    <?php if (isset($additional_css)): ?>
        <?php foreach ($additional_css as $css): ?>
            <link href="<?php echo $css; ?>" rel="stylesheet">
        <?php endforeach; ?>
    <?php endif; ?>
</head>
<body>
    <?php if (is_logged_in()): ?>
        <!-- Navigation Bar -->
        <nav class="navbar navbar-expand-lg navbar-dark">
            <div class="container">
                <a class="navbar-brand d-flex align-items-center" href="<?php echo isset($base_url) ? $base_url : '/'; ?>index.php">
                    <!-- ✅ Logo CSIG -->
                    <img src="/visite%20CSIG/assets/images/logocsig.png" alt="Logo CSIG" style="height:40px; margin-right:10px;">
                    <?php echo APP_NAME; ?>
                </a>
                
                <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarNav">
                    <span class="navbar-toggler-icon"></span>
                </button>
                
                <div class="collapse navbar-collapse" id="navbarNav">
                    <ul class="navbar-nav me-auto">
                        <li class="nav-item">
                            <a class="nav-link <?php echo (basename($_SERVER['PHP_SELF']) == 'index.php') ? 'active' : ''; ?>" 
                               href="<?php echo isset($base_url) ? $base_url : '/'; ?>index.php">
                                <i class="bi bi-house-door"></i> Accueil
                            </a>
                        </li>
                        
                        <li class="nav-item">
                            <a class="nav-link <?php echo (strpos($_SERVER['REQUEST_URI'], '/visites/') !== false) ? 'active' : ''; ?>" 
                               href="<?php echo isset($modules_path) ? $modules_path : 'modules/'; ?>visites/index.php">
                                <i class="bi bi-calendar-check"></i> Visites
                            </a>
                        </li>
                        
                        <li class="nav-item">
                            <a class="nav-link <?php echo (strpos($_SERVER['REQUEST_URI'], '/visiteurs/') !== false) ? 'active' : ''; ?>" 
                               href="<?php echo isset($modules_path) ? $modules_path : 'modules/'; ?>visiteurs/index.php">
                                <i class="bi bi-people"></i> Visiteurs
                            </a>
                        </li>
                        
                        <li class="nav-item">
                            <a class="nav-link" href="<?php echo isset($modules_path) ? $modules_path : 'modules/'; ?>auth/logout.php">
                                <i class="bi bi-box-arrow-right"></i> Déconnexion
                            </a>
                        </li>
                        
                        <?php if (has_permission('admin')): ?>
                        <li class="nav-item dropdown">
                            <a class="nav-link dropdown-toggle <?php echo (strpos($_SERVER['REQUEST_URI'], '/administration/') !== false) ? 'active' : ''; ?>" 
                               href="#" role="button" data-bs-toggle="dropdown">
                                <i class="bi bi-gear"></i> Administration
                            </a>
                            <ul class="dropdown-menu">
                                <li>
                                    <a class="dropdown-item" href="<?php echo isset($modules_path) ? $modules_path : 'modules/'; ?>administration/utilisateurs.php">
                                        <i class="bi bi-person-gear"></i> Utilisateurs
                                    </a>
                                </li>
                            </ul>
                        </li>
                        <?php endif; ?>
                    </ul>
                    
                    <ul class="navbar-nav">
                        <li class="nav-item dropdown">
                            <a class="nav-link dropdown-toggle" href="#" role="button" data-bs-toggle="dropdown">
                                <i class="bi bi-person-circle"></i> 
                                <?php 
                                $user = get_current_user2();
                                echo $user['prenoms'] . ' ' . $user['nom'];
                                ?>
                            </a>
                            <ul class="dropdown-menu dropdown-menu-end">
                                <li>
                                    <h6 class="dropdown-header">
                                        <?php echo $user['nom_utilisateur']; ?><br>
                                        <small class="text-muted"><?php echo ucfirst($user['role']); ?> - <?php echo $user['poste']; ?></small>
                                    </h6>
                                </li>
                                <li><hr class="dropdown-divider"></li>
                                <li>
                                    <a class="dropdown-item" href="<?php echo isset($modules_path) ? $modules_path : 'modules/'; ?>auth/profil.php">
                                        <i class="bi bi-person"></i> Mon profil
                                    </a>
                                </li>
                                <li>
                                    <a class="dropdown-item" href="<?php echo isset($modules_path) ? $modules_path : 'modules/'; ?>auth/logout.php">
                                        <i class="bi bi-box-arrow-right"></i> Déconnexion
                                    </a>
                                </li>
                            </ul>
                        </li>
                    </ul>
                </div>
            </div>
        </nav>
    <?php endif; ?>
    
    <!-- Flash Messages -->
    <?php 
    $flash = get_flash_message();
    if ($flash): 
    ?>
    <div class="container mt-3">
        <div class="alert alert-<?php echo $flash['type']; ?> alert-dismissible fade show" role="alert">
            <?php echo $flash['message']; ?>
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        </div>
    </div>
    <?php endif; ?>
    
    <!-- Main Content -->
    <main class="<?php echo is_logged_in() ? 'container my-4' : ''; ?>">
        <?php /* Le contenu sera inséré ici */ ?>
