/* ============================================================
   Librería de iconos — trazo fino, sin dependencias externas.
   Uso: icon('dashboard', { size: 18, className: 'icon' })
   ============================================================ */

const ICONS = {
    dashboard: '<rect x="3" y="3" width="7" height="9" rx="1.5"></rect><rect x="14" y="3" width="7" height="5" rx="1.5"></rect><rect x="14" y="12" width="7" height="9" rx="1.5"></rect><rect x="3" y="16" width="7" height="5" rx="1.5"></rect>',
    providers: '<path d="M3 21h18"></path><path d="M5 21V7l7-4 7 4v14"></path><path d="M9 21v-6h6v6"></path><path d="M9 9h.01M15 9h.01M9 13h.01M15 13h.01"></path>',
    products: '<path d="M21 8l-9-5-9 5 9 5 9-5z"></path><path d="M3 8v8l9 5 9-5V8"></path><path d="M12 13v8"></path>',
    performance: '<path d="M3 3v18h18"></path><path d="M7 15l4-5 3 3 5-7"></path>',
    evaluations: '<path d="M9 11l3 3L22 4"></path><path d="M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11"></path>',
    search: '<circle cx="11" cy="11" r="7"></circle><path d="M21 21l-4.3-4.3"></path>',
    filter: '<path d="M4 5h16M7 12h10M10 19h4"></path>',
    plus: '<path d="M12 5v14M5 12h14"></path>',
    edit: '<path d="M12 20h9"></path><path d="M16.5 3.5a2.1 2.1 0 0 1 3 3L7 19l-4 1 1-4 12.5-12.5z"></path>',
    trash: '<path d="M3 6h18"></path><path d="M8 6V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path><path d="M19 6l-1 14a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2L5 6"></path><path d="M10 11v6M14 11v6"></path>',
    close: '<path d="M18 6L6 18M6 6l12 12"></path>',
    chevronDown: '<path d="M6 9l6 6 6-6"></path>',
    chevronRight: '<path d="M9 18l6-6-6-6"></path>',
    chevronLeft: '<path d="M15 18l-6-6 6-6"></path>',
    menu: '<path d="M3 6h18M3 12h18M3 18h18"></path>',
    bell: '<path d="M18 8a6 6 0 0 0-12 0c0 7-3 9-3 9h18s-3-2-3-9"></path><path d="M13.7 21a2 2 0 0 1-3.4 0"></path>',
    user: '<circle cx="12" cy="8" r="4"></circle><path d="M4 21c0-4 4-6 8-6s8 2 8 6"></path>',
    building: '<rect x="4" y="3" width="16" height="18" rx="1"></rect><path d="M9 8h1M14 8h1M9 12h1M14 12h1M9 16h1M14 16h1"></path>',
    star: '<path d="M12 2l2.9 6.26L21 9.27l-4.5 4.38L17.8 20 12 16.9 6.2 20l1.3-6.35L3 9.27l6.1-1.01L12 2z"></path>',
    alertTriangle: '<path d="M10.3 3.9L1.9 18a1.7 1.7 0 0 0 1.5 2.6h17.2a1.7 1.7 0 0 0 1.5-2.6L13.7 3.9a1.7 1.7 0 0 0-3.4 0z"></path><path d="M12 9v4M12 17h.01"></path>',
    alertCircle: '<circle cx="12" cy="12" r="10"></circle><path d="M12 8v4M12 16h.01"></path>',
    checkCircle: '<circle cx="12" cy="12" r="10"></circle><path d="M8.5 12.5l2.5 2.5 5-5.5"></path>',
    info: '<circle cx="12" cy="12" r="10"></circle><path d="M12 16v-5M12 8h.01"></path>',
    clock: '<circle cx="12" cy="12" r="9"></circle><path d="M12 7v5l3.5 2"></path>',
    externalLink: '<path d="M14 4h6v6"></path><path d="M20 4L10 14"></path><path d="M18 13v6a1 1 0 0 1-1 1H5a1 1 0 0 1-1-1V7a1 1 0 0 1 1-1h6"></path>',
    moreHorizontal: '<circle cx="5" cy="12" r="1.4"></circle><circle cx="12" cy="12" r="1.4"></circle><circle cx="19" cy="12" r="1.4"></circle>',
    arrowUpRight: '<path d="M7 17L17 7"></path><path d="M8 7h9v9"></path>',
    sparkles: '<path d="M12 3l1.5 4.5L18 9l-4.5 1.5L12 15l-1.5-4.5L6 9l4.5-1.5L12 3z"></path><path d="M19 15l.7 2.3L22 18l-2.3.7L19 21l-.7-2.3L16 18l2.3-.7L19 15z"></path>',
    shield: '<path d="M12 3l8 3v6c0 5-3.5 7.5-8 9-4.5-1.5-8-4-8-9V6l8-3z"></path>',
    dollar: '<path d="M12 2v20"></path><path d="M17 6.5c0-1.9-2.2-3-5-3s-5 1.1-5 3 2.2 2.5 5 3 5 1.1 5 3-2.2 3-5 3-5-1.1-5-3"></path>',
    truck: '<rect x="1" y="7" width="14" height="10" rx="1"></rect><path d="M15 10h4l3 3v4h-7z"></path><circle cx="6" cy="19" r="1.8"></circle><circle cx="17.5" cy="19" r="1.8"></circle>',
    award: '<circle cx="12" cy="8" r="5.5"></circle><path d="M9 13l-1.5 7L12 18l4.5 2L15 13"></path>',
    loader: '<path d="M12 3v3M12 18v3M4.2 4.2l2.1 2.1M17.7 17.7l2.1 2.1M3 12h3M18 12h3M4.2 19.8l2.1-2.1M17.7 6.3l2.1-2.1"></path>',
    package: '<path d="M21 8l-9-5-9 5v8l9 5 9-5V8z"></path><path d="M3 8l9 5 9-5"></path><path d="M12 13v8"></path>',
    clipboardCheck: '<rect x="5" y="4" width="14" height="17" rx="2"></rect><path d="M9 4V3a1 1 0 0 1 1-1h4a1 1 0 0 1 1 1v1"></path><path d="M9 13l2 2 4-4"></path>',
    logo: '<path d="M4 17V7l8-4 8 4v10l-8 4-8-4z"></path><path d="M4 7l8 4 8-4"></path><path d="M12 11v10"></path>',
};

function icon(name, opts = {}) {
    const size = opts.size || 18;
    const className = opts.className || 'icon';
    const body = ICONS[name] || ICONS.info;
    return `<svg class="${className}" width="${size}" height="${size}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round">${body}</svg>`;
}
