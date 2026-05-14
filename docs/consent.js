(function() {
  var GA_ID = 'G-S6C1P3EQ6N';
  var KEY = 'kk_consent';

  function loadGA() {
    if (window.__kkGAloaded) return;
    window.__kkGAloaded = true;
    var s = document.createElement('script');
    s.async = true;
    s.src = 'https://www.googletagmanager.com/gtag/js?id=' + GA_ID;
    document.head.appendChild(s);
    window.dataLayer = window.dataLayer || [];
    window.gtag = function(){ window.dataLayer.push(arguments); };
    window.gtag('js', new Date());
    window.gtag('config', GA_ID, { anonymize_ip: true });
  }

  function removeBanner() {
    var b = document.getElementById('cookie-banner');
    if (b) b.remove();
  }

  function setChoice(value) {
    try { localStorage.setItem(KEY, value); } catch (e) {}
  }

  function showBanner() {
    var banner = document.createElement('div');
    banner.id = 'cookie-banner';
    banner.setAttribute('role', 'dialog');
    banner.setAttribute('aria-label', 'Cookie-samtycke');
    banner.innerHTML =
      '<div class="cookie-banner-inner">' +
        '<p class="cookie-banner-text">Vi använder Google Analytics för att förstå hur besökare hittar oss. Inga personuppgifter säljs vidare. <a href="integritet.html">Läs mer</a></p>' +
        '<div class="cookie-banner-buttons">' +
          '<button type="button" id="cookie-decline" class="cookie-btn cookie-btn-secondary">Bara nödvändiga</button>' +
          '<button type="button" id="cookie-accept" class="cookie-btn cookie-btn-primary">Acceptera</button>' +
        '</div>' +
      '</div>';
    document.body.appendChild(banner);
    document.getElementById('cookie-accept').addEventListener('click', function() {
      setChoice('accepted');
      removeBanner();
      loadGA();
    });
    document.getElementById('cookie-decline').addEventListener('click', function() {
      setChoice('declined');
      removeBanner();
    });
  }

  var stored = null;
  try { stored = localStorage.getItem(KEY); } catch (e) {}

  if (stored === 'accepted') {
    loadGA();
  } else if (stored !== 'declined') {
    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', showBanner);
    } else {
      showBanner();
    }
  }
})();
