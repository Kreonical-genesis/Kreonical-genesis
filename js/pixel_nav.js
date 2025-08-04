

document.addEventListener('DOMContentLoaded', () => {
  const buttons = document.querySelectorAll('.nav-button');
  const nav = document.querySelector('.nav-bar');

  const pixelLine = document.createElement('div');
  pixelLine.classList.add('pixel-line');
  nav.appendChild(pixelLine);

  const colors = [
    'rgba(0,255,0,0.4)',
    'rgba(100,255,100,0.3)',
    'rgba(180,255,180,0.2)',
    'rgba(220,255,220,0.4)',
    'rgba(255,255,255,0.2)'
  ];

  const pixelCount = 30;
  const pixels = [];

  for (let i = 0; i < pixelCount; i++) {
    const pixel = document.createElement('div');
    pixel.classList.add('pixel');
    const size = Math.floor(6 + Math.random() * 12);
    pixel.style.width = size + 'px';
    pixel.style.height = size + 'px';
    pixel.style.backgroundColor = colors[Math.floor(Math.random() * colors.length)];
    pixelLine.appendChild(pixel);
    pixels.push(pixel);
  }

  const getButtonArea = (btn) => {
    const navRect = nav.getBoundingClientRect();
    const btnRect = btn.getBoundingClientRect();
    return {
      left: btnRect.left - navRect.left,
      top: btnRect.top - navRect.top,
      width: btnRect.width,
      height: btnRect.height
    };
  };

  const setInitialPixelPositions = (area) => {
    pixels.forEach(pixel => {
      const randX = area.left + Math.random() * area.width;
      const randY = area.top + area.height / 2 + (Math.random() * 10 - 5);
      pixel.style.transform = `translate(${randX}px, ${randY}px)`;
    });
  };

  const animatePixels = (fromArea, toArea) => {
    pixels.forEach(pixel => {
      const randXStart = fromArea.left + Math.random() * fromArea.width;
      const randXEnd = toArea.left + Math.random() * toArea.width;

      const randYStart = fromArea.top + fromArea.height / 2 + (Math.random() * 10 - 5);
      const randYEnd = toArea.top + toArea.height / 2 + (Math.random() * 10 - 5);

      const duration = 400 + Math.random() * 800;
      const delay = Math.random() * 200;

      pixel.animate([
          { transform: `translate(${randXStart}px, ${randYStart}px)` },
          { transform: `translate(${randXEnd}px, ${randYEnd}px)` }
      ], {
        duration,
        delay,
        fill: 'forwards',
        easing: 'cubic-bezier(0.4, 0, 0.2, 1)'
      });
    });
  };

  // Найти активную кнопку
  let activeButton = Array.from(buttons).find(b => b.dataset.page === "true") || buttons[0];
  let activeArea = getButtonArea(activeButton);
  setInitialPixelPositions(activeArea);

  buttons.forEach(btn => {
    btn.addEventListener('click', e => {
      e.preventDefault();

      const targetArea = getButtonArea(btn);
      animatePixels(activeArea, targetArea);
      activeArea = targetArea;

      setTimeout(() => {
        window.location.href = btn.getAttribute('data-target');
      }, 1200);
    });
  });
  window.addEventListener('resize', () => {
  activeArea = getButtonArea(activeButton);
  setInitialPixelPositions(activeArea);
});
});
