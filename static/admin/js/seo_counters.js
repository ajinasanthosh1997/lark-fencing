// SEO Field Character Counters
document.addEventListener('DOMContentLoaded', function() {
    // Meta title counter
    const titleField = document.querySelector('#id_meta_title');
    if (titleField) {
        const titleCounter = createCounter(titleField, 60);
        titleField.parentNode.appendChild(titleCounter);
        titleField.addEventListener('input', () => updateCounter(titleField, titleCounter, 60));
    }

    // Meta description counter
    const descField = document.querySelector('#id_meta_description');
    if (descField) {
        const descCounter = createCounter(descField, 160);
        descField.parentNode.appendChild(descCounter);
        descField.addEventListener('input', () => updateCounter(descField, descCounter, 160));
    }

    function createCounter(field, max) {
        const counter = document.createElement('div');
        counter.className = 'meta-counter';
        counter.textContent = `${field.value.length}/${max}`;
        return counter;
    }

    function updateCounter(field, counter, max) {
        const len = field.value.length;
        counter.textContent = `${len}/${max}`;
        counter.className = `meta-counter ${len > max ? 'warning' : ''}`;
    }
});