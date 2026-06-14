</main>
    
    <?php if (is_logged_in()): ?>
    <!-- Footer -->
    <footer class="footer mt-auto">
        <div class="container">
            <div class="row">
                <div class="col-md-6">
                    <h6 class="text-white mb-2">
                        <i class="bi bi-building"></i> Cité des Sciences et de l'Innovation de Guinée 
                    </h6>
                    <p class="mb-1">
                        Système de Gestion des Visites<br>
                        Version <?php echo APP_VERSION; ?>
                    </p>
                </div>
                <div class="col-md-6 text-md-end">
                    <p class="mb-1">
                        <i class="bi bi-calendar"></i> 
                        <?php echo date('d/m/Y H:i'); ?>
                    </p>
                    <p class="mb-1">
                        <i class="bi bi-person"></i> 
                        Connecté en tant que <strong><?php echo get_current_user2()['nom_utilisateur']; ?></strong>
                    </p>
                    <p class="mb-0">
                        <small>&copy; <?php echo date('Y'); ?> - Développé pour la CSIG</small>
                    </p>
                </div>
            </div>
        </div>
    </footer>
    <?php endif; ?>
    
    <!-- Bootstrap JS -->
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/js/bootstrap.bundle.min.js"></script>
    
    <!-- Custom JS -->
    <script src="<?php echo isset($js_path) ? $js_path : 'assets/js/'; ?>app.js"></script>
    
    <?php if (isset($additional_js)): ?>
        <?php foreach ($additional_js as $js): ?>
            <script src="<?php echo $js; ?>"></script>
        <?php endforeach; ?>
    <?php endif; ?>
    
    <script>
        // Auto-hide alerts after 5 seconds
        setTimeout(function() {
            var alerts = document.querySelectorAll('.alert');
            alerts.forEach(function(alert) {
                if (alert.classList.contains('alert-dismissible')) {
                    var bsAlert = new bootstrap.Alert(alert);
                    bsAlert.close();
                }
            });
        }, 5000);

        // Confirmation pour les suppressions
        document.addEventListener('DOMContentLoaded', function() {
            var deleteButtons = document.querySelectorAll('[data-confirm-delete]');
            deleteButtons.forEach(function(button) {
                button.addEventListener('click', function(e) {
                    if (!confirm('Êtes-vous sûr de vouloir supprimer cet élément ?')) {
                        e.preventDefault();
                    }
                });
            });
        });

        // Mise à jour de l'heure en temps réel
        function updateTime() {
            var now = new Date();
            var timeString = now.toLocaleString('fr-FR', {
                day: '2-digit',
                month: '2-digit',
                year: 'numeric',
                hour: '2-digit',
                minute: '2-digit',
                second: '2-digit'
            });
            var timeElement = document.querySelector('.current-time');
            if (timeElement) {
                timeElement.textContent = timeString;
            }
        }

        // Mettre à jour l'heure chaque seconde
        setInterval(updateTime, 1000);

        // Animation d'apparition des cartes
        document.addEventListener('DOMContentLoaded', function() {
            var cards = document.querySelectorAll('.card');
            cards.forEach(function(card, index) {
                setTimeout(function() {
                    card.classList.add('fade-in');
                }, index * 100);
            });
        });
    </script>
</body>
</html>