
document.querySelectorAll('.toggle-desc').forEach(btn => {
  btn.addEventListener('click', () => {
    const content = btn.nextElementSibling;
    const expanded = content.style.display === 'block';
    content.style.display = expanded ? 'none' : 'block';
    btn.textContent = expanded ? 'Показать описание' : 'Скрыть описание';
  });
});
