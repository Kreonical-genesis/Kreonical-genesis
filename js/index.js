const slides = {
  'section-builds': [
    'assets/images/builds/1.jpg',
    'assets/images/builds/2.jpg',
    'assets/images/builds/3.jpg'
  ],
  'section-rp': [
    'assets/images/rps/1.jpg',
    'assets/images/rps/2.jpg',
    'assets/images/rps/3.jpg'
  ],
  'section-models': [
    'assets/images/models/1.jpg',
    'assets/images/models/2.jpg',
    'assets/images/models/3.jpg'
  ],
  'section-github': [
    'assets/images/codes/1.jpg',
    'assets/images/codes/2.jpg',
    'assets/images/codes/3.jpg'
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