// Interactivité de la page de résultats

document.addEventListener('DOMContentLoaded', function() {

    // Animation d'apparition progressive
    animateResults();

    // Gestion des tooltips
    initTooltips();

    // Comparaison des images côte à côte
    initImageComparison();

});

// Animation d'apparition des éléments
function animateResults() {
    const elements = document.querySelectorAll('.card, .alert');

    elements.forEach((element, index) => {
        element.style.opacity = '0';
        element.style.transform = 'translateY(20px)';

        setTimeout(() => {
            element.style.transition = 'all 0.5s ease';
            element.style.opacity = '1';
            element.style.transform = 'translateY(0)';
        }, index * 100);
    });
}

// Initialiser les tooltips
function initTooltips() {
    const tooltips = document.querySelectorAll('[data-tooltip]');

    tooltips.forEach(tooltip => {
        tooltip.addEventListener('mouseenter', function() {
            const text = this.getAttribute('data-tooltip');
            showTooltip(this, text);
        });

        tooltip.addEventListener('mouseleave', function() {
            hideTooltip();
        });
    });
}

function showTooltip(element, text) {
    const tooltip = document.createElement('div');
    tooltip.className = 'tooltip-custom';
    tooltip.textContent = text;
    tooltip.style.position = 'absolute';
    tooltip.style.background = '#333';
    tooltip.style.color = '#fff';
    tooltip.style.padding = '8px 12px';
    tooltip.style.borderRadius = '4px';
    tooltip.style.fontSize = '14px';
    tooltip.style.zIndex = '1000';
    tooltip.id = 'active-tooltip';

    document.body.appendChild(tooltip);

    const rect = element.getBoundingClientRect();
    tooltip.style.top = (rect.top - tooltip.offsetHeight - 10) + 'px';
    tooltip.style.left = (rect.left + rect.width / 2 - tooltip.offsetWidth / 2) + 'px';
}

function hideTooltip() {
    const tooltip = document.getElementById('active-tooltip');
    if (tooltip) {
        tooltip.remove();
    }
}

// Comparaison interactive des images
function initImageComparison() {
    const images = document.querySelectorAll('figure img');

    images.forEach(img => {
        img.addEventListener('click', function() {
            openImageModal(this.src, this.alt);
        });

        // Ajouter un curseur pointer
        img.style.cursor = 'pointer';

        // Effet hover
        img.addEventListener('mouseenter', function() {
            this.style.transform = 'scale(1.05)';
            this.style.transition = 'transform 0.3s ease';
        });

        img.addEventListener('mouseleave', function() {
            this.style.transform = 'scale(1)';
        });
    });
}

// Ouvrir une modale pour voir l'image en grand
function openImageModal(src, alt) {
    const modal = document.createElement('div');
    modal.className = 'modal modal-open';
    modal.innerHTML = `
        <div class="modal-box max-w-5xl">
            <h3 class="font-bold text-lg mb-4">${alt}</h3>
            <img src="${src}" alt="${alt}" class="w-full rounded-lg">
            <div class="modal-action">
                <button class="btn" onclick="this.closest('.modal').remove()">Fermer</button>
            </div>
        </div>
        <div class="modal-backdrop" onclick="this.parentElement.remove()"></div>
    `;

    document.body.appendChild(modal);
}

// Animation des progress bars
function animateProgressBars() {
    const progressBars = document.querySelectorAll('.progress');

    progressBars.forEach(bar => {
        const value = bar.getAttribute('value');
        bar.setAttribute('value', '0');

        setTimeout(() => {
            bar.style.transition = 'value 1s ease';
            bar.setAttribute('value', value);
        }, 500);
    });
}

// Copier le hash MD5 au clic
document.addEventListener('click', function(e) {
    if (e.target.classList.contains('font-mono')) {
        const text = e.target.textContent;
        navigator.clipboard.writeText(text).then(() => {
            // Afficher un message de confirmation
            const toast = document.createElement('div');
            toast.className = 'toast toast-top toast-end';
            toast.innerHTML = '<div class="alert alert-success"><span>Hash copié dans le presse-papier!</span></div>';
            document.body.appendChild(toast);

            setTimeout(() => {
                toast.remove();
            }, 2000);
        });
    }
});

// Animer les progress bars au chargement
setTimeout(animateProgressBars, 300);