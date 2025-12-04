// Gestion de l'upload et du drag & drop

document.addEventListener('DOMContentLoaded', function() {

    // Éléments du DOM
    const form = document.getElementById('upload-form');
    const analyzeBtn = document.getElementById('analyze-btn');
    const loader = document.getElementById('loader');

    // Inputs de fichiers
    const image1Input = document.getElementById('image1-input');
    const image2Input = document.getElementById('image2-input');

    // Drop zones
    const dropZone1 = document.getElementById('drop-zone1');
    const dropZone2 = document.getElementById('drop-zone2');

    // Preview containers
    const preview1 = document.getElementById('preview1');
    const preview2 = document.getElementById('preview2');
    const previewImg1 = document.getElementById('preview-img1');
    const previewImg2 = document.getElementById('preview-img2');

    // État des fichiers
    let hasImage1 = false;
    let hasImage2 = false;

    // Fonction pour vérifier si le bouton doit être activé
    function checkFormValidity() {
        if (hasImage1 && hasImage2) {
            analyzeBtn.disabled = false;
            analyzeBtn.classList.remove('btn-disabled');
        } else {
            analyzeBtn.disabled = true;
            analyzeBtn.classList.add('btn-disabled');
        }
    }

    // Fonction pour afficher l'aperçu d'une image
    function showPreview(file, previewContainer, previewImg, imageNumber) {
        const reader = new FileReader();

        reader.onload = function(e) {
            previewImg.src = e.target.result;
            previewContainer.classList.remove('hidden');
        };

        reader.readAsDataURL(file);

        // Marquer l'image comme présente
        if (imageNumber === 1) {
            hasImage1 = true;
        } else {
            hasImage2 = true;
        }

        checkFormValidity();
    }

    // Gestion du clic sur la drop zone pour ouvrir le sélecteur
    dropZone1.addEventListener('click', function() {
        image1Input.click();
    });

    dropZone2.addEventListener('click', function() {
        image2Input.click();
    });

    // Gestion du changement de fichier pour Image 1
    image1Input.addEventListener('change', function(e) {
        const file = e.target.files[0];
        if (file) {
            showPreview(file, preview1, previewImg1, 1);
        }
    });

    // Gestion du changement de fichier pour Image 2
    image2Input.addEventListener('change', function(e) {
        const file = e.target.files[0];
        if (file) {
            showPreview(file, preview2, previewImg2, 2);
        }
    });

    // Drag & Drop pour Image 1
    setupDragAndDrop(dropZone1, image1Input, preview1, previewImg1, 1);

    // Drag & Drop pour Image 2
    setupDragAndDrop(dropZone2, image2Input, preview2, previewImg2, 2);

    // Fonction pour configurer le drag & drop
    function setupDragAndDrop(dropZone, input, previewContainer, previewImg, imageNumber) {

        // Prévenir le comportement par défaut
        ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
            dropZone.addEventListener(eventName, preventDefaults, false);
        });

        function preventDefaults(e) {
            e.preventDefault();
            e.stopPropagation();
        }

        // Highlight lors du survol
        ['dragenter', 'dragover'].forEach(eventName => {
            dropZone.addEventListener(eventName, function() {
                dropZone.classList.add('drag-over');
            });
        });

        ['dragleave', 'drop'].forEach(eventName => {
            dropZone.addEventListener(eventName, function() {
                dropZone.classList.remove('drag-over');
            });
        });

        // Gestion du drop
        dropZone.addEventListener('drop', function(e) {
            const dt = e.dataTransfer;
            const files = dt.files;

            if (files.length > 0) {
                const file = files[0];

                // Vérifier que c'est une image
                if (file.type.startsWith('image/')) {
                    // Créer un objet FileList simulé pour l'input
                    const dataTransfer = new DataTransfer();
                    dataTransfer.items.add(file);
                    input.files = dataTransfer.files;

                    // Afficher l'aperçu
                    showPreview(file, previewContainer, previewImg, imageNumber);
                } else {
                    alert('Veuillez déposer une image valide (JPG, PNG, BMP, TIFF)');
                }
            }
        });
    }

    // Gestion de la soumission du formulaire
    form.addEventListener('submit', function(e) {
        // Afficher le loader
        loader.classList.remove('hidden');
        analyzeBtn.disabled = true;
        analyzeBtn.innerHTML = '<span class="loading loading-spinner"></span> Analyse en cours...';
    });

    // Animation au chargement
    const dropZones = document.querySelectorAll('.drop-zone');
    dropZones.forEach((zone, index) => {
        setTimeout(() => {
            zone.style.opacity = '0';
            zone.style.transform = 'translateY(20px)';
            setTimeout(() => {
                zone.style.transition = 'all 0.5s ease';
                zone.style.opacity = '1';
                zone.style.transform = 'translateY(0)';
            }, 50);
        }, index * 100);
    });

});