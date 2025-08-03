// Загружаем описания из .md файлов и вставляем в плитки
document.querySelectorAll('.tile').forEach(tile => {
  const desc = tile.querySelector('.desc-content');
  const mdPath = tile.getAttribute('data-desc')
  if (mdPath && desc) {
    fetch(mdPath)
      .then(res => res.text())
      .then(md => {
        desc.innerHTML = marked.parse(md);
      })
      .catch(() => {
        desc.textContent = 'Не удалось загрузить описание.';
      });
  }
})
// Слайд-шоу фоновых изображений
const images = {
  'bg-builds': [
    'assets/images/builds/1.jpg',
    'assets/images/builds/2.jpg',
    'assets/images/builds/3.jpg'
  ],
  'bg-rp': [
    'assets/images/rp/1.jpg',
    'assets/images/rp/2.jpg',
    'assets/images/rp/3.jpg'
  ],
  'bg-models': [
    'assets/images/models/1.jpg',
    'assets/images/models/2.jpg',
    'assets/images/models/3.jpg'
  ],
  'bg-code': [
    'assets/images/code/1.jpg',
    'assets/images/code/2.jpg',
    'assets/images/code/3.jpg'
  ]
}
const bodyClass = document.body.classList[0];
const slideshowContainer = document.querySelector('.background-slideshow');
const bgList = images[bodyClass] || [];
let index = 0
if (slideshowContainer && bgList.length) {
  slideshowContainer.style.backgroundImage = `url('${bgList[index]}')`
  setInterval(() => {
    index = (index + 1) % bgList.length;
    slideshowContainer.style.backgroundImage = `url('${bgList[index]}')`;
  }, 8000);
}
