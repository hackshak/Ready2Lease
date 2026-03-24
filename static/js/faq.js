document.querySelectorAll('.faq-question').forEach(btn => {
    btn.addEventListener('click', () => {
        const item = btn.closest('.faq-item');
        const isOpen = btn.getAttribute('aria-expanded') === 'true';
        document.querySelectorAll('.faq-item').forEach(i => {
            i.querySelector('.faq-question').setAttribute('aria-expanded', 'false');
            i.classList.remove('open');
        });
        if (!isOpen) {
            btn.setAttribute('aria-expanded', 'true');
            item.classList.add('open');
        }
    });
});