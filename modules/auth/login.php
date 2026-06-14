<?php
require_once '../../config/config.php';
require_once 'auth_functions.php';

// Rediriger si déjà connecté
if (is_logged_in()) {
    redirect('../../index.php');
}

$error_message = '';

// Traitement du formulaire de connexion
if ($_SERVER['REQUEST_METHOD'] == 'POST') {
    $nom_utilisateur = sanitize_input($_POST['nom_utilisateur']);
    $mot_de_passe = $_POST['mot_de_passe'];
    
    if (empty($nom_utilisateur) || empty($mot_de_passe)) {
        $error_message = 'Veuillez remplir tous les champs';
    } else {
        if (authenticate_user($nom_utilisateur, $mot_de_passe)) {
            set_flash_message('success', 'Connexion réussie ! Bienvenue dans le système de gestion des visites.');
            redirect('../../index.php');
        } else {
            $error_message = 'Nom d\'utilisateur ou mot de passe incorrect';
        }
    }
}

$page_title = 'Connexion';
?>

<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title><?php echo $page_title . ' - ' . APP_NAME; ?></title>
    
    <!-- Bootstrap CSS -->
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css" rel="stylesheet">
    
    <!-- Bootstrap Icons -->
    <link href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.1/font/bootstrap-icons.css" rel="stylesheet">
    
    <!-- Custom CSS -->
    <style>
        :root {
            --primary-color: #4361ee;
            --secondary-color: #1e3a8a;
            --accent-color: #4cc9f0;
            --light-color: #f8f9fa;
            --dark-color: #212529;
            --success-color: #4bb543;
        }
        
        body {
            background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            padding: 20px;
        }
        
        .login-container {
            width: 100%;
            max-width: 420px;
        }
        
        .login-card {
            background: white;
            border-radius: 16px;
            box-shadow: 0 15px 35px rgba(50, 50, 93, 0.1), 0 5px 15px rgba(0, 0, 0, 0.07);
            overflow: hidden;
            transition: transform 0.3s ease, box-shadow 0.3s ease;
        }
        
        .login-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 18px 40px rgba(50, 50, 93, 0.15), 0 8px 20px rgba(0, 0, 0, 0.1);
        }
        
        .login-header {
            background: linear-gradient(to right, var(--primary-color), var(--secondary-color));
            color: white;
            padding: 2.5rem 2rem;
            text-align: center;
        }
        
        .logo-container {
            margin-bottom: 1.5rem;
        }
        
        .logo {
            width: 70px;
            height: 70px;
            background: rgba(255, 255, 255, 0.2);
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            margin: 0 auto;
            font-size: 2rem;
        }
        
        .login-header h2 {
            font-weight: 600;
            margin-bottom: 0.5rem;
        }
        
        .login-header p {
            opacity: 0.9;
            font-size: 0.9rem;
            margin-bottom: 0;
        }
        
        .login-body {
            padding: 2.5rem 2rem;
        }
        
        .form-label {
            font-weight: 500;
            margin-bottom: 0.5rem;
            color: var(--dark-color);
        }
        
        .input-group {
            position: relative;
            margin-bottom: 1.5rem;
        }
        
        .input-icon {
            position: absolute;
            left: 15px;
            top: 50%;
            transform: translateY(-50%);
            color: #6c757d;
            z-index: 5;
        }
        
        .form-control {
            padding-left: 45px;
            height: 50px;
            border-radius: 8px;
            border: 1px solid #dee2e6;
            transition: all 0.3s;
        }
        
        .form-control:focus {
            border-color: var(--primary-color);
            box-shadow: 0 0 0 0.25rem rgba(67, 97, 238, 0.15);
        }
        
        .password-toggle {
            position: absolute;
            right: 15px;
            top: 50%;
            transform: translateY(-50%);
            background: none;
            border: none;
            color: #6c757d;
            cursor: pointer;
            z-index: 5;
        }
        
        .btn-login {
            background: linear-gradient(to right, var(--primary-color), var(--secondary-color));
            color: white;
            border: none;
            height: 50px;
            border-radius: 8px;
            font-weight: 600;
            margin-top: 0.5rem;
            transition: all 0.3s;
        }
        
        .btn-login:hover {
            background: linear-gradient(to right, var(--secondary-color), var(--primary-color));
            transform: translateY(-2px);
        }
        
        .footer {
            text-align: center;
            margin-top: 2rem;
            padding-top: 1.5rem;
            border-top: 1px solid #e9ecef;
            color: #6c757d;
            font-size: 0.85rem;
        }
        
        .alert {
            border-radius: 8px;
            margin-bottom: 1.5rem;
        }
        
        .fade-in {
            animation: fadeIn 0.6s ease forwards;
        }
        
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(20px); }
            to { opacity: 1; transform: translateY(0); }
        }
        
        .floating-label {
            position: relative;
            margin-bottom: 1.5rem;
        }
        
        .floating-input {
            width: 100%;
            padding: 1rem 1rem 1rem 3rem;
            border: 1px solid #ddd;
            border-radius: 8px;
            font-size: 1rem;
            transition: all 0.3s;
        }
        
        .floating-input:focus {
            outline: none;
            border-color: var(--primary-color);
            box-shadow: 0 0 0 3px rgba(67, 97, 238, 0.2);
        }
        
        .floating-label i {
            position: absolute;
            left: 1rem;
            top: 50%;
            transform: translateY(-50%);
            color: #6c757d;
        }
        
        /* Responsive adjustments */
        @media (max-width: 576px) {
            .login-card {
                border-radius: 12px;
            }
            
            .login-header, .login-body {
                padding: 1.5rem;
            }
        }
    </style>
</head>
<body>
    <div class="login-container fade-in">
        <div class="login-card">
            <div class="login-header">
                <div class="logo-container">
                    <div class="logo">
                        <i class="bi bi-shield-lock"></i>
                    </div>
                </div>
                <h2>Accès sécurisé</h2>
                <p>Système de Gestion des Visites<br>Cité des Sciences et de l'Innovation</p>
            </div>
            
            <div class="login-body">
                <?php if (!empty($error_message)): ?>
                    <div class="alert alert-danger d-flex align-items-center" role="alert">
                        <i class="bi bi-exclamation-triangle-fill me-2"></i>
                        <div><?php echo $error_message; ?></div>
                    </div>
                <?php endif; ?>
                
                <form method="POST" action="" id="loginForm">
                    <div class="floating-label">
                        <i class="bi bi-person"></i>
                        <input type="text" 
                               class="form-control floating-input" 
                               id="nom_utilisateur" 
                               name="nom_utilisateur" 
                               placeholder="Nom d'utilisateur"
                               value="<?php echo isset($_POST['nom_utilisateur']) ? htmlspecialchars($_POST['nom_utilisateur']) : ''; ?>"
                               required 
                               autocomplete="username"
                               autofocus>
                    </div>
                    
                    <div class="floating-label">
                        <i class="bi bi-lock"></i>
                        <input type="password" 
                               class="form-control floating-input" 
                               id="mot_de_passe" 
                               name="mot_de_passe" 
                               placeholder="Mot de passe"
                               required 
                               autocomplete="current-password">
                        <button type="button" 
                                class="password-toggle" 
                                onclick="togglePassword()">
                            <i class="bi bi-eye" id="toggleIcon"></i>
                        </button>
                    </div>
                    
                    <div class="d-grid gap-2">
                        <button type="submit" class="btn btn-login">
                            <i class="bi bi-box-arrow-in-right me-2"></i>
                            Se connecter
                        </button>
                    </div>
                </form>
                
                <div class="footer">
                    <small>
                        <i class="bi bi-info-circle me-1"></i>
                        Accès réservé au personnel autorisé<br>
                        Version <?php echo APP_VERSION; ?> - &copy; <?php echo date('Y'); ?>
                    </small>
                </div>
            </div>
        </div>
    </div>
    
    <!-- Bootstrap JS -->
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/js/bootstrap.bundle.min.js"></script>
    
    <script>
        // Fonction pour afficher/masquer le mot de passe
        function togglePassword() {
            const passwordField = document.getElementById('mot_de_passe');
            const toggleIcon = document.getElementById('toggleIcon');
            
            if (passwordField.type === 'password') {
                passwordField.type = 'text';
                toggleIcon.classList.remove('bi-eye');
                toggleIcon.classList.add('bi-eye-slash');
            } else {
                passwordField.type = 'password';
                toggleIcon.classList.remove('bi-eye-slash');
                toggleIcon.classList.add('bi-eye');
            }
        }
        
        // Focus sur le premier champ vide
        document.addEventListener('DOMContentLoaded', function() {
            const usernameField = document.getElementById('nom_utilisateur');
            const passwordField = document.getElementById('mot_de_passe');
            
            if (!usernameField.value) {
                usernameField.focus();
            } else if (!passwordField.value) {
                passwordField.focus();
            }
        });
        
        // Validation côté client
        document.getElementById('loginForm').addEventListener('submit', function(e) {
            const username = document.getElementById('nom_utilisateur').value.trim();
            const password = document.getElementById('mot_de_passe').value;
            
            if (!username || !password) {
                e.preventDefault();
                alert('Veuillez remplir tous les champs');
                return false;
            }
            
            // Afficher un indicateur de chargement
            const submitBtn = document.querySelector('button[type="submit"]');
            submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span> Connexion...';
            submitBtn.disabled = true;
        });
    </script>
</body>
</html>