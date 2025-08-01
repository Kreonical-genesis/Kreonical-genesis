const slides = {
  'section-builds': [
    'assets/images/build1.jpg',
    'assets/images/build2.jpg'
  ],
  'section-rp': [
    'assets/images/rp1.jpg',
    'assets/images/rp2.jpg'
  ],
  'section-models': [
    'assets/images/model1.jpg',
    'assets/images/model2.jpg'
  ],
  'section-github': [
    'assets/images/code1.jpg',
    'assets/images/code2.jpg'
  ]
};

for (const [id, images] of Object.entries(slides)) {
  const el = document.getElementById(id);
  let i = 0;
  el.style.backgroundImage = `url('${images[i]}')`;

  setInterval(() => {
    i = (i + 1) % images.length;
    el.style.backgroundImage = `url('${images[i]}')`;
  }, 6000);
}

const sections = document.querySelectorAll('.section');

sections.forEach(section => {
  let animationId = null;
  let startTime = null;

  const animate = (timestamp) => {
    if (!startTime) startTime = timestamp;
    const progress = timestamp - startTime;
    const offset = Math.sin(progress / 1000) * 10 + 50; // значение между 40% и 60%
    section.style.backgroundPosition = `${offset}% center`;
    animationId = requestAnimationFrame(animate);
  };

  section.addEventListener('mouseenter', () => {
    startTime = null;
    animationId = requestAnimationFrame(animate);
  });

  section.addEventListener('mouseleave', () => {
    cancelAnimationFrame(animationId);
    section.style.backgroundPosition = '50% center';
  });
});