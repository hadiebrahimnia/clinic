// growl.js - Advanced Dynamic Animations + One-Line Header + RTL Support
;(() => {
  const defaults = {
    namespace: 'growl',
    duration: 4000,
    close: '×',
    location: 'top-right',
    style: 'default',
    size: 'medium',
    delayOnHover: true,
    title: '',
    message: '',
    url: null,
    background: null,
    fixed: false,
    animation: {
      in: 'slide',
      out: 'slide',
      duration: 400,
      easing: 'cubic-bezier(0.25, 0.8, 0.25, 1)',
      delay: 0
    }
  };

  class Growl {
    static instances = new Set();
    static styleInjected = false;

    static growl(options = {}) {
      return new Growl(options);
    }

    constructor(options = {}) {
      this.settings = this.deepMerge({}, defaults, options);
      this.id = `growl-${Date.now()}-${Math.floor(Math.random() * 1000)}`;
      this.$container = null;
      this.$growl = null;
      this.timer = null;
      this.hovered = false;

      this.initialize();
      this.injectDynamicStyles();
      this.render();
    }

    deepMerge(target, ...sources) {
      for (const source of sources) {
        for (const key in source) {
          if (source[key] && typeof source[key] === 'object' && !Array.isArray(source[key])) {
            if (!target[key]) target[key] = {};
            this.deepMerge(target[key], source[key]);
          } else {
            target[key] = source[key];
          }
        }
      }
      return target;
    }

    initialize() {
      const id = `growls-${this.settings.location}`;
      let $container = document.getElementById(id);

      if (!$container) {
        $container = document.createElement('div');
        $container.id = id;
        $container.className = 'growls';
        document.body.appendChild($container);
      }

      this.$container = $container;
    }

    injectDynamicStyles() {
      if (Growl.styleInjected) return;
      Growl.styleInjected = true;

      const style = document.createElement('style');
      style.id = 'growl-dynamic-styles';
      style.textContent = this.generateKeyframes();
      document.head.appendChild(style);
    }

    generateKeyframes() {
      const { duration, easing, delay } = this.settings.animation;
      const dur = `${duration / 1000}s`;
      const del = `${delay / 1000}s`;

      return `
        @keyframes growl-slide-in { 0% { opacity: 0; transform: translateY(-30px); } 100% { opacity: 1; transform: translateY(0); } }
        @keyframes growl-slide-out { 0% { opacity: 1; transform: translateY(0); } 100% { opacity: 0; transform: translateY(-30px); } }

        @keyframes growl-fade-in { 0% { opacity: 0; } 100% { opacity: 1; } }
        @keyframes growl-fade-out { 0% { opacity: 1; } 100% { opacity: 0; } }

        @keyframes growl-zoom-in { 0% { opacity: 0; transform: scale(0.3); } 100% { opacity: 1; transform: scale(1); } }
        @keyframes growl-zoom-out { 0% { opacity: 1; transform: scale(1); } 100% { opacity: 0; transform: scale(0.3); } }

        @keyframes growl-flip-in { 0% { opacity: 0; transform: perspective(400px) rotateY(90deg); } 100% { opacity: 1; transform: perspective(400px) rotateY(0); } }
        @keyframes growl-flip-out { 0% { opacity: 1; transform: perspective(400px) rotateY(0); } 100% { opacity: 0; transform: perspective(400px) rotateY(-90deg); } }

        @keyframes growl-bounce-in {
          0%, 20%, 40%, 60%, 80%, 100% { transition-timing-function: cubic-bezier(0.215, 0.61, 0.355, 1); }
          0% { opacity: 0; transform: scale3d(0.3, 0.3, 0.3); }
          20% { transform: scale3d(1.1, 1.1, 1.1); }
          40% { transform: scale3d(0.9, 0.9, 0.9); }
          60% { opacity: 1; transform: scale3d(1.03, 1.03, 1.03); }
          80% { transform: scale3d(0.97, 0.97, 0.97); }
          100% { opacity: 1; transform: scale3d(1, 1, 1); }
        }
        @keyframes growl-bounce-out {
          20% { transform: scale3d(0.9, 0.9, 0.9); }
          50%, 55% { opacity: 1; transform: scale3d(1.1, 1.1, 1.1); }
          100% { opacity: 0; transform: scale3d(0.3, 0.3, 0.3); }
        }

        .growl {
          animation-duration: ${dur} !important;
          animation-timing-function: ${easing} !important;
          animation-fill-mode: both;
          animation-delay: ${del};
        }
      `;
    }

    getAnimationClass(type) {
      const map = {
        slide: { in: 'growl-slide-in', out: 'growl-slide-out' },
        fade: { in: 'growl-fade-in', out: 'growl-fade-out' },
        zoom: { in: 'growl-zoom-in', out: 'growl-zoom-out' },
        flip: { in: 'growl-flip-in', out: 'growl-flip-out' },
        bounce: { in: 'growl-bounce-in', out: 'growl-bounce-out' }
      };
      return map[this.settings.animation[type]] || map.slide;
    }

    render() {
      const bg = this.settings.background || this.getDefaultBackground();
      const animIn = this.getAnimationClass('in').in;

      const html = `
        <div id="${this.id}" class="${this.settings.namespace} ${this.settings.namespace}-${this.settings.size} ${this.settings.namespace}-${this.settings.style}" style="background: ${bg};">
          <div class="growl-header">
            ${this.settings.title ? `<div class="growl-title">${this.escapeHtml(this.settings.title)}</div>` : ''}
            <div class="growl-close">${this.settings.close}</div>
          </div>
          <div class="growl-message">${this.escapeHtml(this.settings.message)}</div>
        </div>
      `;

      this.$container.insertAdjacentHTML('beforeend', html);
      this.$growl = document.getElementById(this.id);

      // Trigger animation
      requestAnimationFrame(() => {
        this.$growl.classList.add('growl-in');
        this.$growl.style.animationName = animIn;
      });

      this.bindEvents();

      if (this.settings.fixed) {
        this.present();
      } else {
        this.cycle();
      }

      Growl.instances.add(this);
    }

    escapeHtml(text) {
      const div = document.createElement('div');
      div.textContent = text;
      return div.innerHTML;
    }

    getDefaultBackground() {
      const styles = {
        default: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
        error: '#e74c3c',
        error1: 'linear-gradient(135deg, #c0392b, #e74c3c)',
        success: '#27ae60',
        success1: 'linear-gradient(135deg, #11998e, #38ef7d)',
        notice: '#3498db',
        notice1: 'linear-gradient(135deg, #2980b9, #3498db)',
        warning: '#f39c12',
        warning1: 'linear-gradient(135deg, #e67e22, #f1c40f)'
      };
      return styles[this.settings.style] || styles.default;
    }

    bindEvents() {
      const $el = this.$growl;

      const handleClose = (e) => {
        e.preventDefault();
        e.stopPropagation();
        this.close();
      };

      const handleClick = (e) => {
        if (this.settings.url && !e.target.closest('.growl-close')) {
          e.preventDefault();
          window.open(this.settings.url, '_blank');
        }
      };

      $el.addEventListener('click', handleClick);
      $el.querySelector('.growl-close').addEventListener('click', handleClose);
      $el.addEventListener('contextmenu', handleClose);

      if (this.settings.delayOnHover) {
        $el.addEventListener('mouseenter', () => this.pause());
        $el.addEventListener('mouseleave', () => this.resume());
      }
    }

    present() { /* fixed mode */ }

    cycle() {
      this.startTimer();
    }

    startTimer() {
      if (this.timer) clearTimeout(this.timer);
      this.timer = setTimeout(() => this.dismiss(), this.settings.duration);
    }

    pause() {
      if (this.hovered) return;
      this.hovered = true;
      if (this.timer) clearTimeout(this.timer);
      this.$growl.classList.add('growl-hovered');
    }

    resume() {
      this.hovered = false;
      this.$growl.classList.remove('growl-hovered');
      if (!this.settings.fixed) this.startTimer();
    }

    dismiss() {
      const animOut = this.getAnimationClass('out').out;
      this.$growl.style.animationName = animOut;
      this.$growl.classList.remove('growl-in');
      this.$growl.classList.add('growl-out');

      setTimeout(() => this.remove(), this.settings.animation.duration + 50);
    }

    close() {
      this.dismiss();
    }

    remove() {
      if (this.$growl && this.$growl.parentNode) {
        this.$growl.parentNode.removeChild(this.$growl);
      }
      Growl.instances.delete(this);
    }
  }

  // Global API
  window.Growl = Growl;

  // Shortcut methods
  ['error', 'success', 'notice', 'warning'].forEach(type => {
    Growl[type] = (options = {}) => Growl.growl({
      title: type.charAt(0).toUpperCase() + type.slice(1) + '!',
      style: type,
      ...options
    });

    Growl[type + '1'] = (options = {}) => Growl.growl({
      title: type.charAt(0).toUpperCase() + type.slice(1) + '!',
      style: type + '1',
      ...options
    });
  });

})();



// static/js/growl_handler.js
document.addEventListener('DOMContentLoaded', function () {
  const container = document.getElementById('growl-messages');
  if (!container) return;

  const items = container.querySelectorAll('.growl-message-item');
  items.forEach(item => {
    const message = item.dataset.message;
    const rawConfig = item.dataset.gconfig;

    let cfg = {};
    try {
      cfg = JSON.parse(rawConfig);
    } catch (e) {
      console.warn('Invalid Growl config:', rawConfig);
    }

    Growl.growl({
      message: message,
      title: cfg.title || '',
      style: cfg.style || 'default',
      size: cfg.size || 'medium',
      background: cfg.background || '',
      close: cfg.close || '×',
      duration: cfg.duration ?? 4000,
      fixed: !!cfg.fixed,
      delayOnHover: cfg.delayOnHover !== false,
      location: cfg.location || 'top-right',
      url: cfg.url || '',
      animation: {
        in: cfg.animation?.in || 'bounce',
        out: cfg.animation?.out || 'bounce',
        duration: cfg.animation?.duration ?? 400,
        easing: cfg.animation?.easing || 'cubic-bezier(0.25, 0.8, 0.25, 1)',
        delay: cfg.animation?.delay ?? 0
      }
    });
  });
});