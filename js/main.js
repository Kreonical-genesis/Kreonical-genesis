document.addEventListener('DOMContentLoaded', () => {
  const uploader = document.getElementById('previewUploader');
  const portfolio = document.getElementById('portfolio');

  uploader.addEventListener('change', (event) => {
    const file = event.target.files[0];
    if (file && file.type.startsWith('image/')) {
      const reader = new FileReader();
      reader.onload = function (e) {
        const card = document.createElement('div');
        card.className = 'model-card';
        card.innerHTML = `
          <img src="${e.target.result}" class="model-preview" alt="Custom Preview" />
          <h2>Новая модель</h2>
          <p>Описание можно добавить вручную.</p>
          <a href="#">Скачать (пока нет)</a>
        `;
        portfolio.prepend(card);
      };
      reader.readAsDataURL(file);
    }
  });
});