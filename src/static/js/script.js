// DOM Content Loaded
document.addEventListener('DOMContentLoaded', function() {
    // Initialize all functionality
    initCustomCursor();
    initNavigation();
    initTypingAnimation();
    initScrollAnimations();
    initServices();
    initPricing();
    initPortfolio();
    initTestimonials();
    initContactForm();
    initSmoothScrolling();
});

// Custom Cursor
function initCustomCursor() {
    const cursor = document.querySelector('.cursor');
    const interactiveElements = document.querySelectorAll('a, button, .service-card, .portfolio-item, .nav-toggle, .filter-btn, .dot, input, textarea, select');
    
    if (!cursor) return;
    
    // Check for reduced motion preference
    if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
        cursor.style.display = 'none';
        document.body.style.cursor = 'auto';
        return;
    }
    
    document.addEventListener('mousemove', (e) => {
        cursor.style.left = e.clientX + 'px';
        cursor.style.top = e.clientY + 'px';
    });
    
    interactiveElements.forEach(element => {
        element.addEventListener('mouseenter', () => {
            cursor.classList.add('hover');
        });
        
        element.addEventListener('mouseleave', () => {
            cursor.classList.remove('hover');
        });
    });
}

// Navigation
function initNavigation() {
    const navbar = document.getElementById('navbar');
    const navToggle = document.getElementById('nav-toggle');
    const navMenu = document.getElementById('nav-menu');
    const navLinks = document.querySelectorAll('.nav-link');
    
    // Navbar scroll effect
    window.addEventListener('scroll', () => {
        if (window.scrollY > 100) {
            navbar.classList.add('scrolled');
        } else {
            navbar.classList.remove('scrolled');
        }
    });
    
    // Mobile menu toggle
    navToggle.addEventListener('click', () => {
        navMenu.classList.toggle('active');
        navToggle.classList.toggle('active');
    });
    
    // Close mobile menu when clicking on links
    navLinks.forEach(link => {
        link.addEventListener('click', () => {
            navMenu.classList.remove('active');
            navToggle.classList.remove('active');
        });
    });
    
    // Active nav link on scroll
    const sections = document.querySelectorAll('section[id]');
    
    window.addEventListener('scroll', () => {
        let current = '';
        sections.forEach(section => {
            const sectionTop = section.offsetTop;
            const sectionHeight = section.clientHeight;
            if (scrollY >= (sectionTop - 200)) {
                current = section.getAttribute('id');
            }
        });
        
        navLinks.forEach(link => {
            link.classList.remove('active');
            if (link.getAttribute('href') === `#${current}`) {
                link.classList.add('active');
            }
        });
    });
}

// Typing Animation
function initTypingAnimation() {
    const typingElement = document.getElementById('typing-text');
    if (!typingElement) return;
    
    const texts = [
        'Digital Marketing Expert',
        'Web Developer',
        'Shopify Dropshipping Specialist'
    ];
    
    let textIndex = 0;
    let charIndex = 0;
    let isDeleting = false;
    let typeSpeed = 100;
    
    function type() {
        const currentText = texts[textIndex];
        
        if (isDeleting) {
            typingElement.textContent = currentText.substring(0, charIndex - 1);
            charIndex--;
            typeSpeed = 50;
        } else {
            typingElement.textContent = currentText.substring(0, charIndex + 1);
            charIndex++;
            typeSpeed = 100;
        }
        
        if (!isDeleting && charIndex === currentText.length) {
            typeSpeed = 2000; // Pause at end
            isDeleting = true;
        } else if (isDeleting && charIndex === 0) {
            isDeleting = false;
            textIndex = (textIndex + 1) % texts.length;
            typeSpeed = 500; // Pause before next word
        }
        
        setTimeout(type, typeSpeed);
    }
    
    type();
}

// Scroll Animations
function initScrollAnimations() {
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    };
    
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('visible');
            }
        });
    }, observerOptions);
    
    // Add fade-in class to elements that should animate
    const animateElements = document.querySelectorAll('.service-card, .portfolio-item, .testimonial-slide, .contact-item, .about-image, .about-text, .pricing-card');
    
    animateElements.forEach(element => {
        element.classList.add('fade-in');
        observer.observe(element);
    });
}

// Services
function initServices() {
    const serviceCards = document.querySelectorAll('.service-card');
    const serviceDetails = document.querySelectorAll('.service-details');
    
    serviceCards.forEach(card => {
        const learnMoreBtn = card.querySelector('.service-learn-more');
        if (!learnMoreBtn) return;
        
        learnMoreBtn.addEventListener('click', () => {
            const serviceType = learnMoreBtn.getAttribute('data-service');
            const targetDetail = document.getElementById(`${serviceType}-details`);
            
            // Hide all service details
            serviceDetails.forEach(detail => {
                detail.classList.remove('active');
            });
            
            // Show target detail
            if (targetDetail) {
                targetDetail.classList.add('active');
                targetDetail.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
            }
        });
    });
}

// Pricing Toggle
function initPricing() {
    const pricingToggle = document.getElementById('pricing-toggle');
    const monthlyPrices = document.querySelectorAll('.monthly-price');
    const yearlyPrices = document.querySelectorAll('.yearly-price');
    
    if (!pricingToggle) return;
    
    pricingToggle.addEventListener('change', () => {
        if (pricingToggle.checked) {
            // Show yearly prices
            monthlyPrices.forEach(price => price.style.display = 'none');
            yearlyPrices.forEach(price => price.style.display = 'inline');
        } else {
            // Show monthly prices
            monthlyPrices.forEach(price => price.style.display = 'inline');
            yearlyPrices.forEach(price => price.style.display = 'none');
        }
    });
}

// Portfolio
function initPortfolio() {
    const filterBtns = document.querySelectorAll('.filter-btn');
    const portfolioItems = document.querySelectorAll('.portfolio-item');
    const portfolioBtns = document.querySelectorAll('.portfolio-btn');
    const modal = document.getElementById('portfolio-modal');
    const modalBody = document.getElementById('modal-body');
    const modalClose = document.querySelector('.modal-close');
    
    // Portfolio filtering
    filterBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            const filter = btn.getAttribute('data-filter');
            
            // Update active filter button
            filterBtns.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            
            // Filter portfolio items
            portfolioItems.forEach(item => {
                const category = item.getAttribute('data-category');
                
                if (filter === 'all' || category === filter) {
                    item.style.display = 'block';
                    setTimeout(() => {
                        item.style.opacity = '1';
                        item.style.transform = 'translateY(0)';
                    }, 100);
                } else {
                    item.style.opacity = '0';
                    item.style.transform = 'translateY(20px)';
                    setTimeout(() => {
                        item.style.display = 'none';
                    }, 300);
                }
            });
        });
    });
    
    // Portfolio modals
    portfolioBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            const portfolioId = btn.getAttribute('data-portfolio');
            const modalContent = getPortfolioModalContent(portfolioId);
            
            modalBody.innerHTML = modalContent;
            modal.classList.add('show');
            document.body.style.overflow = 'hidden';
        });
    });
    
    // Close modal
    if (modalClose) {
        modalClose.addEventListener('click', closeModal);
    }
    
    if (modal) {
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                closeModal();
            }
        });
    }
    
    function closeModal() {
        modal.classList.remove('show');
        document.body.style.overflow = 'auto';
    }
    
    // ESC key to close modal
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && modal.classList.contains('show')) {
            closeModal();
        }
    });
}

// Portfolio Modal Content
function getPortfolioModalContent(portfolioId) {
    const portfolioData = {
        'marketing-1': {
            title: 'E-commerce SEO Campaign',
            client: 'Fashion Retailer',
            duration: '6 months',
            challenge: 'Low organic visibility and declining traffic',
            strategy: 'Comprehensive SEO audit, keyword optimization, content strategy, and technical improvements',
            results: [
                '300% increase in organic traffic',
                '150% improvement in keyword rankings',
                '200% boost in online sales',
                '85% increase in conversion rate'
            ],
            tools: ['Google Analytics', 'SEMrush', 'Ahrefs', 'Google Search Console'],
            image: 'images/case-study-marketing-1.jpg'
        },
        'web-1': {
            title: 'Corporate Website Redesign',
            client: 'Tech Consulting Firm',
            duration: '3 months',
            challenge: 'Outdated design, poor mobile experience, slow loading times',
            strategy: 'Modern responsive design, performance optimization, user experience improvements',
            results: [
                '60% improvement in page load speed',
                '40% increase in mobile conversions',
                '25% reduction in bounce rate',
                '90% client satisfaction score'
            ],
            tools: ['React', 'Node.js', 'MongoDB', 'AWS'],
            image: 'images/case-study-web-1.jpg'
        },
        'shopify-1': {
            title: 'Dropshipping Store Launch',
            client: 'Health & Wellness Brand',
            duration: '4 months',
            challenge: 'New market entry with zero brand recognition',
            strategy: 'Market research, product selection, store optimization, targeted advertising',
            results: [
                '$50K revenue in first 3 months',
                '15% conversion rate achieved',
                '2.5x return on ad spend',
                '1000+ satisfied customers'
            ],
            tools: ['Shopify', 'Oberlo', 'Facebook Ads', 'Google Analytics'],
            image: 'images/case-study-shopify-1.jpg'
        },
        'marketing-2': {
            title: 'Facebook Ads Optimization',
            client: 'SaaS Startup',
            duration: '4 months',
            challenge: 'High cost per acquisition, low conversion rates',
            strategy: 'Audience research, ad creative optimization, funnel improvements, A/B testing',
            results: [
                '50% reduction in cost per acquisition',
                '75% increase in click-through rate',
                '120% improvement in ROAS',
                '300% growth in qualified leads'
            ],
            tools: ['Facebook Ads Manager', 'Google Analytics', 'Hotjar', 'Unbounce'],
            image: 'images/case-study-marketing-2.jpg'
        },
        'web-2': {
            title: 'High-Converting Landing Page',
            client: 'Digital Marketing Agency',
            duration: '2 months',
            challenge: 'Low conversion rates on existing landing pages',
            strategy: 'Conversion rate optimization, A/B testing, user experience improvements',
            results: [
                '25% conversion rate improvement',
                '35% increase in lead quality',
                '20% reduction in cost per lead',
                '95% client retention rate'
            ],
            tools: ['Unbounce', 'Google Optimize', 'Hotjar', 'Google Analytics'],
            image: 'images/case-study-web-2.jpg'
        },
        'shopify-2': {
            title: 'Store Conversion Optimization',
            client: 'Fashion E-commerce',
            duration: '3 months',
            challenge: 'High traffic but low checkout completion rates',
            strategy: 'Checkout optimization, trust signals, payment options, mobile improvements',
            results: [
                '40% increase in checkout completion',
                '30% reduction in cart abandonment',
                '25% improvement in average order value',
                '200% increase in customer lifetime value'
            ],
            tools: ['Shopify Plus', 'Klaviyo', 'Yotpo', 'Google Analytics'],
            image: 'images/case-study-shopify-2.jpg'
        }
    };
    
    const data = portfolioData[portfolioId];
    if (!data) return '<p>Case study not found.</p>';
    
    return `
        <div class="case-study">
            <img src="${data.image}" alt="${data.title}" style="width: 100%; height: 300px; object-fit: cover; border-radius: 12px; margin-bottom: 2rem;">
            <h2 style="color: #1a1a1a; margin-bottom: 1rem;">${data.title}</h2>
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1rem; margin-bottom: 2rem;">
                <div><strong>Client:</strong> ${data.client}</div>
                <div><strong>Duration:</strong> ${data.duration}</div>
            </div>
            
            <div style="margin-bottom: 2rem;">
                <h3 style="color: #3b82f6; margin-bottom: 1rem;">Challenge</h3>
                <p style="color: #6b7280; line-height: 1.6;">${data.challenge}</p>
            </div>
            
            <div style="margin-bottom: 2rem;">
                <h3 style="color: #3b82f6; margin-bottom: 1rem;">Strategy</h3>
                <p style="color: #6b7280; line-height: 1.6;">${data.strategy}</p>
            </div>
            
            <div style="margin-bottom: 2rem;">
                <h3 style="color: #3b82f6; margin-bottom: 1rem;">Results</h3>
                <ul style="list-style: none; padding: 0;">
                    ${data.results.map(result => `
                        <li style="display: flex; align-items: center; margin-bottom: 0.5rem; color: #6b7280;">
                            <i class="fas fa-check" style="color: #10b981; margin-right: 0.5rem;"></i>
                            ${result}
                        </li>
                    `).join('')}
                </ul>
            </div>
            
            <div>
                <h3 style="color: #3b82f6; margin-bottom: 1rem;">Tools Used</h3>
                <div style="display: flex; flex-wrap: wrap; gap: 0.5rem;">
                    ${data.tools.map(tool => `
                        <span style="background: #e0f2fe; color: #0369a1; padding: 0.5rem 1rem; border-radius: 20px; font-size: 0.875rem; font-weight: 500;">
                            ${tool}
                        </span>
                    `).join('')}
                </div>
            </div>
        </div>
    `;
}

// Testimonials Carousel
function initTestimonials() {
    const slides = document.querySelectorAll('.testimonial-slide');
    const dots = document.querySelectorAll('.dot');
    const prevBtn = document.getElementById('prev-testimonial');
    const nextBtn = document.getElementById('next-testimonial');
    
    let currentSlide = 0;
    let autoPlayInterval;
    
    function showSlide(index) {
        slides.forEach(slide => slide.classList.remove('active'));
        dots.forEach(dot => dot.classList.remove('active'));
        
        slides[index].classList.add('active');
        dots[index].classList.add('active');
        
        currentSlide = index;
    }
    
    function nextSlide() {
        const next = (currentSlide + 1) % slides.length;
        showSlide(next);
    }
    
    function prevSlide() {
        const prev = (currentSlide - 1 + slides.length) % slides.length;
        showSlide(prev);
    }
    
    function startAutoPlay() {
        autoPlayInterval = setInterval(nextSlide, 5000);
    }
    
    function stopAutoPlay() {
        clearInterval(autoPlayInterval);
    }
    
    // Event listeners
    if (nextBtn) nextBtn.addEventListener('click', () => {
        nextSlide();
        stopAutoPlay();
        startAutoPlay();
    });
    
    if (prevBtn) prevBtn.addEventListener('click', () => {
        prevSlide();
        stopAutoPlay();
        startAutoPlay();
    });
    
    dots.forEach((dot, index) => {
        dot.addEventListener('click', () => {
            showSlide(index);
            stopAutoPlay();
            startAutoPlay();
        });
    });
    
    // Pause on hover
    const carousel = document.querySelector('.testimonials-carousel');
    if (carousel) {
        carousel.addEventListener('mouseenter', stopAutoPlay);
        carousel.addEventListener('mouseleave', startAutoPlay);
    }
    
    // Start auto play
    startAutoPlay();
}

// Contact Form
function initContactForm() {
    const form = document.getElementById('contact-form');
    const successMessage = document.getElementById('success-message');
    
    if (!form) return;
    
    // Form validation
    const validators = {
        name: (value) => {
            if (!value.trim()) return 'Name is required';
            if (value.trim().length < 2) return 'Name must be at least 2 characters';
            return null;
        },
        email: (value) => {
            if (!value.trim()) return 'Email is required';
            const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
            if (!emailRegex.test(value)) return 'Please enter a valid email address';
            return null;
        },
        phone: (value) => {
            if (value.trim() && !/^[\+]?[1-9][\d]{0,15}$/.test(value.replace(/[\s\-\(\)]/g, ''))) {
                return 'Please enter a valid phone number';
            }
            return null;
        },
        service: (value) => {
            if (!value) return 'Please select a service';
            return null;
        },
        message: (value) => {
            if (!value.trim()) return 'Message is required';
            if (value.trim().length < 10) return 'Message must be at least 10 characters';
            return null;
        }
    };
    
    // Real-time validation
    Object.keys(validators).forEach(fieldName => {
        const field = form.querySelector(`[name="${fieldName}"]`);
        const errorElement = document.getElementById(`${fieldName}-error`);
        
        if (field && errorElement) {
            field.addEventListener('blur', () => {
                const error = validators[fieldName](field.value);
                if (error) {
                    errorElement.textContent = error;
                    errorElement.classList.add('show');
                    field.style.borderColor = '#ef4444';
                } else {
                    errorElement.textContent = '';
                    errorElement.classList.remove('show');
                    field.style.borderColor = '#10b981';
                }
            });
            
            field.addEventListener('input', () => {
                if (errorElement.classList.contains('show')) {
                    const error = validators[fieldName](field.value);
                    if (!error) {
                        errorElement.textContent = '';
                        errorElement.classList.remove('show');
                        field.style.borderColor = '#10b981';
                    }
                }
            });
        }
    });
    
    // Form submission
    async function submitContact(formData) {
        const r = await fetch('/api/contact', {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify(formData)
        });
        const j = await r.json();
        if (!r.ok || !j.success) throw new Error(j.error || 'Failed');
        return j;
      }
    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const submitBtn = form.querySelector('.submit-btn');
        const formData = new FormData(form);
        
        // Check honeypot
        if (formData.get('honeypot')) {
            return; // Likely spam
        }
        
        // Validate all fields
        let hasErrors = false;
        Object.keys(validators).forEach(fieldName => {
            const field = form.querySelector(`[name="${fieldName}"]`);
            const errorElement = document.getElementById(`${fieldName}-error`);
            
            if (field && errorElement) {
                const error = validators[fieldName](field.value);
                if (error) {
                    errorElement.textContent = error;
                    errorElement.classList.add('show');
                    field.style.borderColor = '#ef4444';
                    hasErrors = true;
                }
            }
        });
        
        if (hasErrors) return;
        
        // Show loading state
        submitBtn.classList.add('loading');
        submitBtn.disabled = true;
        
        try {
            // Check rate limiting
            if (!contactFormLimiter.isAllowed()) {
                const timeUntilReset = Math.ceil(contactFormLimiter.getTimeUntilReset() / 60000);
                alert(`Too many attempts. Please try again in ${timeUntilReset} minutes.`);
                return;
            }
            
            // Prepare JSON data
            const jsonData = {
                name: formData.get('name'),
                email: formData.get('email'),
                phone: formData.get('phone'),
                service: formData.get('service'),
                message: formData.get('message'),
                honeypot: formData.get('honeypot')
            };
            
            // Submit form
            const response = await fetch('/api/contact', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(jsonData)
            });
            
            const result = await response.json();
            
            if (result.success) {
                // Show success message
                form.style.display = 'none';
                successMessage.classList.add('show');
                
                // Reset form after delay
                setTimeout(() => {
                    form.reset();
                    form.style.display = 'block';
                    successMessage.classList.remove('show');
                    
                    // Reset field styles
                    form.querySelectorAll('input, select, textarea').forEach(field => {
                        field.style.borderColor = '#e5e7eb';
                    });
                }, 5000);
            } else {
                // Handle validation errors from server
                if (result.errors) {
                    Object.keys(result.errors).forEach(fieldName => {
                        const errorElement = document.getElementById(`${fieldName}-error`);
                        const field = form.querySelector(`[name="${fieldName}"]`);
                        
                        if (errorElement && field) {
                            errorElement.textContent = result.errors[fieldName];
                            errorElement.classList.add('show');
                            field.style.borderColor = '#ef4444';
                        }
                    });
                } else {
                    alert(result.error || 'An error occurred. Please try again.');
                }
            }
        } catch (error) {
            console.error('Form submission error:', error);
            alert('Sorry, there was an error sending your message. Please try again or contact us directly.');
        } finally {
            // Hide loading state
            submitBtn.classList.remove('loading');
            submitBtn.disabled = false;
        }
    });
}

// Smooth Scrolling
function initSmoothScrolling() {
    const links = document.querySelectorAll('a[href^="#"]');
    
    links.forEach(link => {
        link.addEventListener('click', (e) => {
            e.preventDefault();
            
            const targetId = link.getAttribute('href').substring(1);
            const targetElement = document.getElementById(targetId);
            
            if (targetElement) {
                const headerOffset = 80;
                const elementPosition = targetElement.offsetTop;
                const offsetPosition = elementPosition - headerOffset;
                
                window.scrollTo({
                    top: offsetPosition,
                    behavior: 'smooth'
                });
            }
        });
    });
}

// Rate limiting for form submissions
class RateLimiter {
    constructor(maxAttempts = 3, windowMs = 300000) { // 3 attempts per 5 minutes
        this.maxAttempts = maxAttempts;
        this.windowMs = windowMs;
        this.attempts = [];
    }
    
    isAllowed() {
        const now = Date.now();
        this.attempts = this.attempts.filter(time => now - time < this.windowMs);
        
        if (this.attempts.length >= this.maxAttempts) {
            return false;
        }
        
        this.attempts.push(now);
        return true;
    }
    
    getTimeUntilReset() {
        if (this.attempts.length === 0) return 0;
        const oldestAttempt = Math.min(...this.attempts);
        const timeUntilReset = this.windowMs - (Date.now() - oldestAttempt);
        return Math.max(0, timeUntilReset);
    }
}

// Initialize rate limiter
const contactFormLimiter = new RateLimiter();

// Utility functions
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

function throttle(func, limit) {
    let inThrottle;
    return function() {
        const args = arguments;
        const context = this;
        if (!inThrottle) {
            func.apply(context, args);
            inThrottle = true;
            setTimeout(() => inThrottle = false, limit);
        }
    };
}

// Performance optimizations
const optimizedScrollHandler = throttle(() => {
    // Handle scroll events
}, 16); // ~60fps

const optimizedResizeHandler = debounce(() => {
    // Handle resize events
}, 250);

window.addEventListener('scroll', optimizedScrollHandler);
window.addEventListener('resize', optimizedResizeHandler);

// Error handling
window.addEventListener('error', (e) => {
    console.error('JavaScript error:', e.error);
    // Could send error reports to analytics service
});

// Service Worker registration (for future PWA features)
if ('serviceWorker' in navigator) {
    window.addEventListener('load', () => {
        // navigator.serviceWorker.register('/sw.js')
        //     .then(registration => console.log('SW registered'))
        //     .catch(error => console.log('SW registration failed'));
  
  
    });
}

 

