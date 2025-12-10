class CustomSlider {
  constructor(wrapper) {
    this.wrapper = wrapper;
    this.slider = wrapper.querySelector('[data-slider]');
    this.track = wrapper.querySelector('[data-track]');
    this.items = wrapper.querySelectorAll('[data-item]');
    this.prevBtn = wrapper.querySelector('[data-prev]');
    this.nextBtn = wrapper.querySelector('[data-next]');

    this.itemWidth = this.items[0].offsetWidth + 24;
    this.currentIndex = 0;
    this.isDragging = false;
    this.startPos = 0;
    this.currentTranslate = 0;
    this.prevTranslate = 0;
    this.animationID = null;
    this.autoSlide = null;

    this.init();
  }

  init() {
    this.calculateVisibleItems();
    this.bindEvents();
    this.startAutoSlide();
    this.clampIndex();
    this.updateNavButtons();
  }

  calculateVisibleItems() {
    const sliderWidth = this.slider.offsetWidth;
    this.visibleItems = Math.round(sliderWidth / this.itemWidth);
    this.maxIndex = Math.max(0, this.items.length - this.visibleItems);
  }

  setPosition() {
    this.track.style.transform = `translateX(${this.currentTranslate}px)`;
  }

  clampIndex() {
    this.currentIndex = Math.max(0, Math.min(this.currentIndex, this.maxIndex));
    this.currentTranslate = this.currentIndex * this.itemWidth;
    this.prevTranslate = this.currentTranslate;
    this.setPosition();
    this.updateNavButtons();
  }

  next() {
    if (this.currentIndex < this.maxIndex) {
      this.currentIndex++;
      this.clampIndex();
    }
  }

  prev() {
    if (this.currentIndex > 0) {
      this.currentIndex--;
      this.clampIndex();
    }
  }

  startDrag(e) {
    this.isDragging = true;
    this.startPos = e.clientX || e.touches[0].clientX;
    this.prevTranslate = this.currentTranslate;
    this.track.style.transition = 'none';
    cancelAnimationFrame(this.animationID);
    e.preventDefault();
  }

  drag(e) {
    if (!this.isDragging) return;
    const currentPosition = e.clientX || e.touches[0].clientX;
    const diff = currentPosition - this.startPos;
    this.currentTranslate = this.prevTranslate + diff;
    this.setPosition();
  }

  endDrag() {
    if (!this.isDragging) return;
    this.isDragging = false;
    this.track.style.transition = 'transform 0.5s cubic-bezier(0.4, 0, 0.2, 1)';

    const movedBy = this.currentTranslate - this.prevTranslate;

    if (movedBy > 50 && this.currentIndex < this.maxIndex) {
      this.currentIndex++;
    } else if (movedBy < -50 && this.currentIndex > 0) {
      this.currentIndex--;
    }

    this.clampIndex();
  }


  updateNavButtons() {
    if (this.prevBtn) {
      const isDisabled = this.currentIndex === 0;
      this.prevBtn.style.opacity = isDisabled ? '0' : '1';
      this.prevBtn.style.pointerEvents = isDisabled ? 'none' : 'auto';
      this.prevBtn.disabled = isDisabled;
    }

    if (this.nextBtn) {
      const isDisabled = this.currentIndex === this.maxIndex;
      this.nextBtn.style.opacity = isDisabled ? '0' : '1';
      this.nextBtn.style.pointerEvents = isDisabled ? 'none' : 'auto';
      this.nextBtn.disabled = isDisabled;
    }
  }

  bindEvents() {
    // دکمه‌ها
    this.nextBtn?.addEventListener('click', () => this.next());
    this.prevBtn?.addEventListener('click', () => this.prev());

    // ماوس
    this.track.addEventListener('mousedown', (e) => this.startDrag(e));
    this.track.addEventListener('mousemove', (e) => this.drag(e));
    this.track.addEventListener('mouseup', () => this.endDrag());
    this.track.addEventListener('mouseleave', () => this.endDrag());

    // تاچ
    this.track.addEventListener('touchstart', (e) => this.startDrag(e), { passive: true });
    this.track.addEventListener('touchmove', (e) => this.drag(e), { passive: true });
    this.track.addEventListener('touchend', () => this.endDrag());

    // ریسایز
    window.addEventListener('resize', () => {
      this.itemWidth = this.items[0].offsetWidth + 24;
      this.calculateVisibleItems();
      if (this.currentIndex > this.maxIndex) {
        this.currentIndex = this.maxIndex;
      }
      this.clampIndex();
    });

    // توقف خودکار در هاور
    this.wrapper.addEventListener('mouseenter', () => clearInterval(this.autoSlide));
    this.wrapper.addEventListener('mouseleave', () => this.startAutoSlide());
  }

  startAutoSlide() {
    this.autoSlide = setInterval(() => {
      this.currentIndex = this.currentIndex < this.maxIndex ? this.currentIndex + 1 : 0;
      this.clampIndex();
    }, 5000);
  }
}

// راه‌اندازی تمام اسلایدرها
document.addEventListener('DOMContentLoaded', () => {
  document.querySelectorAll('[data-slider-wrapper]').forEach(wrapper => {
    new CustomSlider(wrapper);
  });
});