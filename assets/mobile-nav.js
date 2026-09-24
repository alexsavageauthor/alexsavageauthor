/* Mobile menu for pages whose header links are hidden under 720px.
   Builds a toggle and drop-down from the page's own nav.site .links, so the
   menu can never drift from the desktop nav. Pages that already ship their
   own .nav-toggle are left alone. */
(function () {
  var nav = document.querySelector('nav.site');
  if (!nav || nav.querySelector('.nav-toggle') || nav.querySelector('.asnav-toggle')) return;
  var links = nav.querySelector('.links');
  var row = nav.querySelector('.row') || links && links.parentNode;
  if (!links || !row) return;

  var css = document.createElement('style');
  css.textContent =
    '.asnav-toggle{display:none;background:none;border:1px solid rgba(245,239,230,0.25);color:#F5EFE6;' +
    'width:44px;height:44px;border-radius:8px;align-items:center;justify-content:center;font-size:20px;' +
    'cursor:pointer;transition:border-color .2s ease,color .2s ease}' +
    '.asnav-toggle:hover{border-color:#E8B756;color:#E8B756}' +
    '.asnav-menu{display:none;position:absolute;top:100%;left:0;right:0;background:rgba(22,12,36,0.98);' +
    'border-bottom:1px solid rgba(255,255,255,0.08);padding:16px 0;z-index:60}' +
    '.asnav-menu.open{display:block}' +
    '.asnav-menu a{display:block;padding:14px 24px;font-size:15px;color:#F5EFE6;' +
    'border-bottom:1px solid rgba(255,255,255,0.06)}' +
    '.asnav-menu a:last-child{border-bottom:none}' +
    '.asnav-menu a:hover{background:rgba(232,183,86,0.08);color:#E8B756}' +
    '@media (max-width:720px){.asnav-toggle{display:flex}}';
  document.head.appendChild(css);

  if (getComputedStyle(nav).position === 'static') nav.style.position = 'relative';

  var btn = document.createElement('button');
  btn.className = 'asnav-toggle';
  btn.type = 'button';
  btn.setAttribute('aria-label', 'Open menu');
  btn.setAttribute('aria-expanded', 'false');
  btn.setAttribute('aria-controls', 'asnav-menu');
  btn.textContent = '☰';
  row.appendChild(btn);

  var menu = document.createElement('div');
  menu.className = 'asnav-menu';
  menu.id = 'asnav-menu';
  Array.prototype.forEach.call(links.querySelectorAll('a'), function (a) {
    var c = a.cloneNode(true);
    c.removeAttribute('class');
    menu.appendChild(c);
  });
  nav.appendChild(menu);

  function set(open) {
    menu.classList.toggle('open', open);
    btn.setAttribute('aria-expanded', open ? 'true' : 'false');
    btn.setAttribute('aria-label', open ? 'Close menu' : 'Open menu');
    btn.textContent = open ? '✕' : '☰';
  }
  btn.addEventListener('click', function () { set(!menu.classList.contains('open')); });
  menu.addEventListener('click', function (e) { if (e.target.closest('a')) set(false); });
  document.addEventListener('keydown', function (e) { if (e.key === 'Escape') set(false); });
})();
