
document.querySelectorAll('.toggle-desc').forEach(btn => {
  btn.addEventListener('click', () => {
    const content = btn.nextElementSibling;
    const expanded = content.style.display === 'block';
    content.style.display = expanded ? 'none' : 'block';
    btn.textContent = expanded ? 'Показать описание' : 'Скрыть описание';
  });
});
const images = {
  'bg-builds': [
    'assets/images/build1.jpg',
    'assets/images/build2.jpg',
    'assets/images/build3.jpg'
  ],
  'bg-rp': [
    'assets/images/rp1.jpg',
    'assets/images/rp2.jpg',
    'assets/images/rp3.jpg'
  ],
  'bg-models': [
    'assets/images/model1.jpg',
    'assets/images/model2.jpg',
    'assets/images/model3.jpg'
  ],
  'bg-code': [
    'assets/images/code1.jpg',
    'assets/images/code2.jpg',
    'assets/images/code3.jpg'
  ]
};

const bodyClass = document.body.classList[0];
const slideshowContainer = document.querySelector('.background-slideshow');
const bgList = images[bodyClass] || [];
let index = 0;

if (slideshowContainer && bgList.length) {
  slideshowContainer.style.backgroundImage = `url('${bgList[index]}')`;

  setInterval(() => {
    index = (index + 1) % bgList.length;
    slideshowContainer.style.backgroundImage = `url('${bgList[index]}')`;
  }, 8000); // смена каждые 8 секунд
}
