// Portfolio content rendering
const CONTENT_UNAVAILABLE_MESSAGE = 'This content is temporarily unavailable.';

function isRecord(value) {
    return value !== null && typeof value === 'object' && !Array.isArray(value);
}

function showContentFallback(container, sectionName) {
    if (!container) return;
    container.replaceChildren();
    const message = appendTextElement(container, 'p', 'content-fallback', CONTENT_UNAVAILABLE_MESSAGE);
    message.setAttribute('role', 'status');
    message.setAttribute('aria-label', `${sectionName} unavailable`);
}

function reportContentError(path, reason, error) {
    const detail = error instanceof Error ? error.message : reason;
    console.error(`[Portfolio content] ${path}: ${detail}`, error instanceof Error ? error : '');
}

function renderItemsSafely(items, path, renderItem) {
    let renderedCount = 0;
    items.forEach((item, index) => {
        try {
            renderItem(item, index);
            renderedCount += 1;
        } catch (error) {
            reportContentError(`${path}[${index}]`, 'skipping malformed item', error);
        }
    });
    return renderedCount;
}

function appendTextElement(parent, tagName, className, text) {
    const element = document.createElement(tagName);
    if (className) element.className = className;
    element.textContent = text;
    parent.appendChild(element);
    return element;
}

function isSafeContentUrl(value) {
    if (typeof value !== 'string') return false;
    try {
        return ['http:', 'https:', 'mailto:'].includes(new URL(value).protocol);
    } catch {
        return false;
    }
}

function appendContentParts(parent, parts, path) {
    if (!Array.isArray(parts) || parts.length === 0) {
        throw new TypeError(`${path}.parts must be a nonempty array`);
    }

    let atLineStart = true;
    parts.forEach((part, index) => {
        const partPath = `${path}.parts[${index}]`;
        if (!isRecord(part)) throw new TypeError(`${partPath} must be an object`);
        if (Array.isArray(part.targets) && !part.targets.includes('portfolio')) return;
        if (part.type === 'break') {
            parent.appendChild(document.createElement('br'));
            atLineStart = true;
            return;
        }

        const value = part.type === 'text' ? part.value : part.label;
        if (!['text', 'link'].includes(part.type) || typeof value !== 'string' || !value.trim()) {
            throw new TypeError(`${partPath} must be valid text or link content`);
        }
        if (!atLineStart && part.join !== 'none') parent.appendChild(document.createTextNode(' '));

        let content = document.createTextNode(value);
        [...(part.styles || [])].reverse().forEach(style => {
            if (!['bold', 'italic'].includes(style)) throw new TypeError(`${partPath}.styles contains an invalid style`);
            const wrapper = document.createElement(style === 'bold' ? 'strong' : 'em');
            wrapper.appendChild(content);
            content = wrapper;
        });
        if (part.type === 'link') {
            if (!isSafeContentUrl(part.url)) throw new TypeError(`${partPath}.url is invalid`);
            const link = document.createElement('a');
            link.href = part.url;
            link.target = '_blank';
            link.rel = 'noopener noreferrer';
            link.appendChild(content);
            content = link;
        }
        parent.appendChild(content);
        atLineStart = false;
    });
}

function appendContentItems(parent, items, { list = false, className = '', path = 'items' } = {}) {
    if (!Array.isArray(items) || items.length === 0) return 0;
    const container = list ? document.createElement('ul') : document.createDocumentFragment();
    if (list && className) container.className = className;
    let renderedCount = 0;

    items.forEach((item, index) => {
        const itemPath = `${path}[${index}]`;
        try {
            if (!isRecord(item)) throw new TypeError(`${itemPath} must be an object`);
            if (Array.isArray(item.targets) && !item.targets.includes('portfolio')) return;
            const element = document.createElement(list ? 'li' : 'p');
            appendContentParts(element, item.parts, itemPath);
            if (Array.isArray(item.children)) {
                appendContentItems(element, item.children, { list: true, className: 'sublist', path: `${itemPath}.children` });
            }
            container.appendChild(element);
            renderedCount += 1;
        } catch (error) {
            reportContentError(itemPath, 'skipping malformed content item', error);
        }
    });
    parent.appendChild(container);
    return renderedCount;
}

function renderIdentity(profile) {
    const person = isRecord(profile.person) ? profile.person : {};
    const about = isRecord(profile.about) ? profile.about : {};

    [document.getElementById('nav-profile-name'), document.getElementById('profile-name')]
        .forEach(element => {
            if (element && person.name) element.textContent = person.name;
        });

    const title = document.getElementById('profile-title');
    if (title && person.title) title.textContent = person.title;

    const introduction = document.getElementById('profile-introduction');
    if (introduction && Array.isArray(about.items)) {
        introduction.replaceChildren();
        appendContentItems(introduction, about.items, { path: 'PROFILE_DATA.about.items' });
    }

    const resumeLink = document.getElementById('resume-link');
    if (resumeLink && profile.resumeUrl) resumeLink.href = profile.resumeUrl;

    const socialLinks = {
        github: document.getElementById('github-link'),
        linkedin: document.getElementById('linkedin-link'),
        email: document.getElementById('email-link')
    };
    Object.entries(socialLinks).forEach(([key, element]) => {
        const value = isRecord(person.social) && person.social[key];
        if (element && value) element.href = key === 'email' ? `mailto:${value}` : value;
    });
}

function renderExperience(experience) {
    const timeline = document.querySelector('.experience-timeline');
    if (!timeline) return;
    timeline.replaceChildren();

    return renderItemsSafely(experience, 'PROFILE_DATA.experience', (entry, index) => {
        if (!isRecord(entry)) throw new TypeError(`experience[${index}] must be an object`);
        const item = document.createElement('div');
        item.className = 'experience-item';
        appendTextElement(item, 'h3', '', entry.title);
        appendTextElement(item, 'div', 'experience-company', entry.company);
        appendTextElement(item, 'div', 'experience-dates', entry.dates);
        const description = document.createElement('div');
        description.className = 'experience-description';
        appendContentItems(description, entry.items, {
            list: true,
            className: 'experience-list',
            path: `PROFILE_DATA.experience[${index}].items`
        });
        item.appendChild(description);
        timeline.appendChild(item);
    });
}

function renderEducation(education) {
    const timeline = document.querySelector('.education-timeline');
    if (!timeline) return;
    timeline.replaceChildren();

    return renderItemsSafely(education, 'PROFILE_DATA.education', (entry, index) => {
        if (!isRecord(entry)) throw new TypeError(`education[${index}] must be an object`);
        const item = document.createElement('div');
        item.className = 'education-item';
        appendTextElement(item, 'h3', '', entry.degree);
        appendTextElement(item, 'div', 'education-institution', entry.institution);
        appendTextElement(item, 'div', 'education-dates', entry.dates);
        if (entry.details) appendTextElement(item, 'p', 'education-details', entry.details);
        timeline.appendChild(item);
    });
}

function renderSkills(skillGroups) {
    const grid = document.querySelector('.skills-grid');
    if (!grid) return;
    grid.replaceChildren();

    return renderItemsSafely(skillGroups, 'PROFILE_DATA.skills', (group, index) => {
        if (!isRecord(group) || !Array.isArray(group.items)) {
            throw new TypeError(`skills[${index}] must be an object with an items array`);
        }
        const section = document.createElement('div');
        section.className = 'skills-group';
        appendTextElement(section, 'h3', '', group.title);
        const list = document.createElement('div');
        list.className = 'skill-list';
        group.items.forEach(skill => appendTextElement(list, 'div', 'skill-card', skill));
        section.appendChild(list);
        grid.appendChild(section);
    });
}

function appendProjectMedia(parent, mediaItems) {
    if (!Array.isArray(mediaItems)) return;
    mediaItems.forEach((media, index) => {
        if (!isRecord(media)) {
            reportContentError(`projects.media[${index}]`, 'expected an object');
            return;
        }
        if (media.type !== 'video' || typeof media.url !== 'string') return;
        const video = document.createElement('video');
        video.controls = true;
        video.preload = 'metadata';
        video.setAttribute('aria-label', media.label || 'Project demo');
        const source = document.createElement('source');
        source.src = media.url;
        if (media.mimeType) source.type = media.mimeType;
        video.appendChild(source);
        parent.appendChild(video);
    });
}

function renderProjects(projects) {
    const grid = document.querySelector('.projects-grid');
    if (!grid) return;
    grid.replaceChildren();

    return renderItemsSafely(projects, 'PROFILE_DATA.projects', (project, index) => {
        if (!isRecord(project) || !Array.isArray(project.technologies)) {
            throw new TypeError(`projects[${index}] must be an object with a technologies array`);
        }
        const card = document.createElement('div');
        card.className = 'project-card';
        card.id = project.id;
        appendTextElement(card, 'h3', '', project.title);
        const description = document.createElement('div');
        description.className = 'project-description';
        appendContentItems(description, project.items, {
            list: true,
            path: `PROFILE_DATA.projects[${index}].items`
        });
        appendProjectMedia(description, project.media);
        card.appendChild(description);
        appendTextElement(card, 'div', 'tech', project.technologies.join(', '));
        grid.appendChild(card);
    });
}

function renderCertifications(certifications) {
    const grid = document.querySelector('.certifications-grid');
    if (!grid) return;
    grid.replaceChildren();

    return renderItemsSafely(certifications, 'PROFILE_DATA.certifications', (certification, index) => {
        if (!isRecord(certification)) throw new TypeError(`certifications[${index}] must be an object`);
        const card = document.createElement('div');
        card.className = 'certification-card';
        const heading = document.createElement('h3');
        const link = document.createElement('a');
        link.href = certification.link;
        link.textContent = certification.title;
        link.target = '_blank';
        link.rel = 'noopener noreferrer';
        heading.appendChild(link);
        card.appendChild(heading);
        appendTextElement(card, 'p', '', certification.issuer);
        appendTextElement(card, 'div', 'cert-date', certification.date);
        grid.appendChild(card);
    });
}

function scrollToInitialAnchor() {
    const anchorId = decodeURIComponent(window.location.hash.slice(1));
    const target = anchorId && document.getElementById(anchorId);
    if (target) target.scrollIntoView({ behavior: 'smooth' });
}

function renderCollectionSection(profile, key, selector, render) {
    const container = document.querySelector(selector);
    const items = profile[key];

    if (!Array.isArray(items)) {
        reportContentError(`PROFILE_DATA.${key}`, 'expected an array');
        showContentFallback(container, key);
        return;
    }

    try {
        const renderedCount = render(items);
        if (items.length > 0 && renderedCount === 0) {
            showContentFallback(container, key);
        }
    } catch (error) {
        reportContentError(`PROFILE_DATA.${key}`, 'could not render section', error);
        showContentFallback(container, key);
    }
}

document.addEventListener('DOMContentLoaded', () => {
    const profile = window.PROFILE_DATA;
    if (!isRecord(profile)) {
        reportContentError('window.PROFILE_DATA', 'missing or invalid; expected a profile object');
        [
            ['experience', '.experience-timeline'],
            ['education', '.education-timeline'],
            ['skills', '.skills-grid'],
            ['projects', '.projects-grid'],
            ['certifications', '.certifications-grid']
        ].forEach(([sectionName, selector]) => {
            showContentFallback(document.querySelector(selector), sectionName);
        });
        scrollToInitialAnchor();
        return;
    }

    try {
        renderIdentity(profile);
    } catch (error) {
        reportContentError('PROFILE_DATA identity', 'could not render identity', error);
    }

    renderCollectionSection(profile, 'experience', '.experience-timeline', renderExperience);
    renderCollectionSection(profile, 'education', '.education-timeline', renderEducation);
    renderCollectionSection(profile, 'skills', '.skills-grid', renderSkills);
    renderCollectionSection(profile, 'projects', '.projects-grid', renderProjects);
    renderCollectionSection(profile, 'certifications', '.certifications-grid', renderCertifications);
    scrollToInitialAnchor();
});

// Animated background is independent of generated profile content.
document.addEventListener('DOMContentLoaded', () => {
    const canvas = document.getElementById('techBg');
    const context = canvas && canvas.getContext('2d');
    if (!canvas || !context) return;

    function resizeCanvas() {
        canvas.width = window.innerWidth;
        canvas.height = window.innerHeight;
    }

    class Particle {
        constructor() { this.reset(); }
        reset() {
            this.x = Math.random() * canvas.width;
            this.y = Math.random() * canvas.height;
            this.size = Math.random() * 2;
            this.speed = Math.random() * 0.5 + 0.1;
            this.angle = Math.random() * Math.PI * 2;
        }
        update() {
            this.x += Math.cos(this.angle) * this.speed;
            this.y += Math.sin(this.angle) * this.speed;
            if (this.x < 0 || this.x > canvas.width || this.y < 0 || this.y > canvas.height) this.reset();
        }
        draw() {
            context.fillStyle = 'rgba(35,134,54,0.3)';
            context.beginPath();
            context.arc(this.x, this.y, this.size, 0, Math.PI * 2);
            context.fill();
        }
    }

    const particles = Array.from({ length: 100 }, () => new Particle());
    function animate() {
        context.clearRect(0, 0, canvas.width, canvas.height);
        particles.forEach(particle => { particle.update(); particle.draw(); });
        requestAnimationFrame(animate);
    }
    resizeCanvas();
    animate();
    window.addEventListener('resize', resizeCanvas);
});

// Navigation is independent of generated profile content.
document.addEventListener('DOMContentLoaded', () => {
    const menuButton = document.querySelector('.menu-btn');
    const navigationLinks = document.querySelector('.nav-links');
    if (menuButton && navigationLinks) {
        menuButton.addEventListener('click', () => {
            const isOpen = navigationLinks.classList.toggle('active');
            menuButton.setAttribute('aria-expanded', String(isOpen));
        });
        navigationLinks.querySelectorAll('a').forEach(link => {
            link.addEventListener('click', () => {
                navigationLinks.classList.remove('active');
                menuButton.setAttribute('aria-expanded', 'false');
            });
        });
    }

    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', event => {
            const targetSelector = anchor.getAttribute('href');
            const target = targetSelector === '#'
                ? document.documentElement
                : document.querySelector(targetSelector);
            if (target) {
                event.preventDefault();
                target.scrollIntoView({ behavior: 'smooth' });
            }
        });
    });
});
