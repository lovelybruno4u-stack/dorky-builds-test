// --- ROTATING TEXT ANIMATION ---
const words = ["SYSTEMS", "WEBSITES", "AI TOOLS"];
let currentWordIndex = 0;
const rotatingTextElement = document.getElementById("rotating-text");

function rotateText() {
    if(!rotatingTextElement) return;
    rotatingTextElement.style.opacity = 0;
    setTimeout(() => {
        currentWordIndex = (currentWordIndex + 1) % words.length;
        rotatingTextElement.innerText = words[currentWordIndex];
        rotatingTextElement.style.opacity = 1;
    }, 300); // Wait for fade out
}
if(rotatingTextElement) {
    rotatingTextElement.style.transition = "opacity 0.3s ease-in-out";
    setInterval(rotateText, 2500);
}

// --- ANIMATED COUNTERS ---
const counters = document.querySelectorAll('.counter');
const speed = 200; // The lower the slower

const animateCounters = () => {
    counters.forEach(counter => {
        const updateCount = () => {
            const target = +counter.getAttribute('data-target');
            const count = +counter.innerText;

            const inc = target / speed;

            if (count < target) {
                counter.innerText = Math.ceil(count + inc);
                setTimeout(updateCount, 10);
            } else {
                counter.innerText = target;
            }
        };

        const observer = new IntersectionObserver((entries) => {
            if(entries[0].isIntersecting) {
                updateCount();
                observer.disconnect();
            }
        }, { threshold: 0.5 });

        observer.observe(counter);
    });
}
document.addEventListener('DOMContentLoaded', animateCounters);

// --- CURSOR GLOW ---
const cursorGlow = document.getElementById('cursor-glow');
if (cursorGlow) {
    document.addEventListener('mousemove', (e) => {
        cursorGlow.style.display = 'block';
        cursorGlow.style.left = e.clientX + 'px';
        cursorGlow.style.top = e.clientY + 'px';
    });
    document.addEventListener('mouseleave', () => {
        cursorGlow.style.display = 'none';
    });
}

// --- SCANLINE ANIMATION ---
const scanline = document.getElementById('scanline');
if(scanline) {
    let position = 0;
    setInterval(() => {
        position += 2;
        if(position > window.innerHeight) position = -10;
        scanline.style.top = position + 'px';
    }, 16);
}

// --- SMOOTH SCROLLING ---
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
        if(this.getAttribute('href') === '#') return;

        const target = document.querySelector(this.getAttribute('href'));
        if (target) {
            e.preventDefault();
            target.scrollIntoView({
                behavior: 'smooth'
            });
            const mobileNav = document.getElementById('mobile-nav');
            if (mobileNav && !mobileNav.classList.contains('translate-x-full')) {
                mobileNav.classList.add('translate-x-full');
            }
        }
    });
});

// --- MOBILE MENU TOGGLE ---
const mobileMenuBtn = document.getElementById('mobile-menu-btn');
const closeMenuBtn = document.getElementById('close-menu-btn');
const mobileNav = document.getElementById('mobile-nav');

if (mobileMenuBtn && closeMenuBtn && mobileNav) {
    mobileMenuBtn.addEventListener('click', () => {
        mobileNav.classList.remove('translate-x-full');
    });
    closeMenuBtn.addEventListener('click', () => {
        mobileNav.classList.add('translate-x-full');
    });
}

// --- WORKBENCH FILTERING ---
const filterBtns = document.querySelectorAll('.filter-btn');
const projectCards = document.querySelectorAll('.project-card');

if (filterBtns.length > 0) {
    filterBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            filterBtns.forEach(b => {
                b.classList.remove('active', 'text-white');
                b.classList.add('text-on-surface-variant');
            });

            btn.classList.add('active', 'text-white');
            btn.classList.remove('text-on-surface-variant');

            const filterValue = btn.getAttribute('data-filter');

            projectCards.forEach(card => {
                if (filterValue === 'all' || card.classList.contains(filterValue)) {
                    card.style.display = 'block';
                } else {
                    card.style.display = 'none';
                }
            });
        });
    });
}

// --- CASE STUDY MODAL ---
const caseModal = document.getElementById('case-modal');
const modalContent = document.getElementById('modal-content');

const caseStudies = {
    'proj1': {
        title: 'Neural_Net_Dashboard',
        problem: 'Client needed a real-time visualization tool for training complex ML models across distributed clusters. Existing tools were too slow and crashed under high data loads.',
        process: 'We engineered a custom WebSocket architecture streaming binary data to a WebGL-accelerated React frontend. Bypassed standard DOM rendering entirely for the data layer.',
        tech: 'React, Tailwind CSS, WebSockets, WebGL, Node.js',
        results: 'Achieved 60fps rendering of 1M+ data points. Reduced memory footprint by 80%. System deployed to 5 enterprise clusters.'
    },
    'proj2': {
        title: 'Cognitive_Agent',
        problem: 'Customer support team was overwhelmed with repetitive technical queries. Previous chatbot attempts failed due to lack of context awareness and rigid decision trees.',
        process: 'Developed a custom RAG (Retrieval-Augmented Generation) pipeline. Ingested their entire documentation and ticket history into a vector database. Implemented LangChain to handle multi-turn conversations.',
        tech: 'Python, OpenAI GPT-4, LangChain, Pinecone, FastAPI',
        results: 'Automated 65% of Tier 1 support tickets. Average resolution time dropped from 4 hours to 2 minutes. High user satisfaction scores.'
    },
    'proj3': {
        title: 'Data_Pipeline_V2',
        problem: 'Legacy monolithic architecture was choking on daily ETL jobs. Data latency was unacceptable for live trading algorithms relying on the output.',
        process: 'Deconstructed the monolith into a suite of microservices. Introduced Redis for aggressive caching and decoupled components using an event-driven architecture.',
        tech: 'Node.js, PostgreSQL, Redis, Docker, AWS ECS',
        results: 'ETL execution time reduced by 90%. System handles 10x the previous data volume with zero degraded performance. 99.99% uptime achieved.'
    }
};

function openModal(projectId) {
    if(!caseModal || !modalContent) return;
    const data = caseStudies[projectId];
    if(!data) return;

    modalContent.innerHTML = `
        <h2 class="text-3xl font-bold text-primary mb-6">> ${data.title}</h2>
        <div class="space-y-6 text-sm text-on-surface-variant">
            <div class="border-l-2 border-primary pl-4">
                <h3 class="text-white font-bold mb-2 uppercase">[ PROBLEM_STATEMENT ]</h3>
                <p>${data.problem}</p>
            </div>
            <div class="border-l-2 border-primary pl-4">
                <h3 class="text-white font-bold mb-2 uppercase">[ EXECUTION_PROCESS ]</h3>
                <p>${data.process}</p>
            </div>
            <div class="border-l-2 border-primary pl-4">
                <h3 class="text-white font-bold mb-2 uppercase">[ TECH_STACK ]</h3>
                <p class="font-mono text-primary">${data.tech}</p>
            </div>
            <div class="border-l-2 border-primary pl-4">
                <h3 class="text-white font-bold mb-2 uppercase">[ METRICS_&_RESULTS ]</h3>
                <p>${data.results}</p>
            </div>
        </div>
    `;

    caseModal.classList.remove('hidden');
    document.body.style.overflow = 'hidden';
}

function closeModal() {
    if(!caseModal) return;
    caseModal.classList.add('hidden');
    document.body.style.overflow = 'auto';
}

if(caseModal) {
    caseModal.addEventListener('click', (e) => {
        if (e.target === caseModal) {
            closeModal();
        }
    });
}

// --- TERMINAL COMMAND SYSTEM ---
const terminalToggle = document.getElementById('terminal-toggle');
const terminalOverlay = document.getElementById('terminal-overlay');
const closeTerminal = document.getElementById('close-terminal');
const terminalInput = document.getElementById('terminal-input');
const terminalOutput = document.getElementById('terminal-output');

if (terminalToggle && terminalOverlay && closeTerminal && terminalInput && terminalOutput) {

    function toggleTerminal() {
        if (terminalOverlay.classList.contains('translate-y-[120%]')) {
            terminalOverlay.classList.remove('hidden');
            setTimeout(() => {
                terminalOverlay.classList.remove('translate-y-[120%]');
                terminalInput.focus();
            }, 10);
        } else {
            terminalOverlay.classList.add('translate-y-[120%]');
            setTimeout(() => {
                terminalOverlay.classList.add('hidden');
            }, 300);
        }
    }

    terminalToggle.addEventListener('click', toggleTerminal);
    closeTerminal.addEventListener('click', toggleTerminal);

    const commands = {
        'help': 'Available commands:\n- help: Show this message\n- clear: Clear terminal output\n- about: Display system info\n- deploy: Initiate deployment sequence\n- contact: Open communication link\n- sudo: Request elevated privileges',
        'clear': () => { terminalOutput.innerHTML = ''; return ''; },
        'about': 'Dorky Builds OS v1.0.0\nKernel: Hacker_Mindset_x64\nMission: Build production-grade systems.',
        'deploy': () => { window.location.href = '/services'; return 'Redirecting to Engine Modules...'; },
        'contact': () => { window.location.href = '/contact'; return 'Navigating to contact module...'; },
        'sudo': 'Access denied. Incident reported.'
    };

    terminalInput.addEventListener('keydown', function(e) {
        if (e.key === 'Enter') {
            const val = this.value.trim().toLowerCase();
            this.value = '';

            if (val === '') return;

            const echoLine = document.createElement('div');
            echoLine.className = 'mb-1';
            echoLine.innerHTML = `<span class="text-primary">></span> ${val}`;
            terminalOutput.appendChild(echoLine);

            const responseLine = document.createElement('div');
            responseLine.className = 'text-on-surface-variant mb-3 whitespace-pre-wrap';

            let response = '';
            if (commands[val]) {
                if (typeof commands[val] === 'function') {
                    response = commands[val]();
                } else {
                    response = commands[val];
                }
            } else {
                response = `Command not found: ${val}. Type 'help' for available commands.`;
            }

            if (response) {
                responseLine.innerText = response;
                terminalOutput.appendChild(responseLine);
            }

            terminalOutput.scrollTop = terminalOutput.scrollHeight;
        }
    });
}

// --- FORM HANDLING ---
const contactForm = document.getElementById('contact-form');
if (contactForm) {
    contactForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const statusDiv = document.getElementById('contact-status');
        const btn = contactForm.querySelector('button[type="submit"]');
        const originalText = btn.innerHTML;

        btn.innerHTML = '<span class="relative z-10">> PROCESSING...</span>';
        btn.classList.add('animate-pulse');

        try {
            const formData = new FormData(contactForm);
            const response = await fetch('/contact-submit', {
                method: 'POST',
                body: formData
            });

            const result = await response.json();

            statusDiv.innerText = result.message;
            statusDiv.classList.remove('hidden', 'text-red-500');
            statusDiv.classList.add('text-primary');
            contactForm.reset();
        } catch (error) {
            statusDiv.innerText = "Error: Connection refused. Try again.";
            statusDiv.classList.remove('hidden', 'text-primary');
            statusDiv.classList.add('text-red-500');
        } finally {
            btn.innerHTML = originalText;
            btn.classList.remove('animate-pulse');
            setTimeout(() => {
                statusDiv.classList.add('hidden');
            }, 5000);
        }
    });
}

const applyForm = document.getElementById('apply-form');
if (applyForm) {
    applyForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const statusDiv = document.getElementById('apply-status');
        const btn = applyForm.querySelector('button[type="submit"]');
        const originalText = btn.innerHTML;

        btn.innerHTML = '> TRANSMITTING...';
        btn.classList.add('animate-pulse');

        try {
            const formData = new FormData(applyForm);
            const response = await fetch('/apply', {
                method: 'POST',
                body: formData
            });

            const result = await response.json();

            statusDiv.innerText = result.message;
            statusDiv.classList.remove('hidden', 'text-red-500');
            statusDiv.classList.add('text-primary');
            applyForm.reset();
        } catch (error) {
            statusDiv.innerText = "Error: Transmission failed.";
            statusDiv.classList.remove('hidden', 'text-primary');
            statusDiv.classList.add('text-red-500');
        } finally {
            btn.innerHTML = originalText;
            btn.classList.remove('animate-pulse');
            setTimeout(() => {
                statusDiv.classList.add('hidden');
            }, 5000);
        }
    });
}

// --- MULTI-STEP ONBOARDING LOGIC (requirements.html) ---
const projectOptionsContainer = document.getElementById('project-options');
const stepIndicator = document.getElementById('step-indicator');
const currentStepNum = document.getElementById('current-step-num');
const progressBar = document.getElementById('progress-bar');
const requirementsForm = document.getElementById('requirements-form');
const moduleSelectFallback = document.getElementById('module-select-fallback');

let onboardingState = {
    module: '',
    projectType: '',
    plan: '',
    basePrice: 0,
    speed: '',
    speedPrice: 0
};

const moduleProjects = {
    'web_dev': [
        { id: 'business_website', name: 'Business Website', desc: 'Corporate presence & landing pages' },
        { id: 'ecommerce', name: 'E-commerce Store', desc: 'Full online retail systems' },
        { id: 'portfolio', name: 'Portfolio', desc: 'Personal branding & showcases' },
        { id: 'custom_web_app', name: 'Custom Web App', desc: 'Complex interactive applications' }
    ],
    'ai_tools': [
        { id: 'chatbot', name: 'Chatbot', desc: 'Intelligent conversational agents' },
        { id: 'ai_tool', name: 'AI Tool', desc: 'Custom LLM-powered utilities' },
        { id: 'automation_ai', name: 'Automation AI', desc: 'AI-driven workflow systems' }
    ],
    'automation': [
        { id: 'bots', name: 'Bots', desc: 'Automated task execution' },
        { id: 'scripts', name: 'Scripts', desc: 'Data processing & utilities' },
        { id: 'workflow', name: 'Workflow Automation', desc: 'Connecting APIs and services' }
    ],
    'student': [
        { id: 'school_project', name: 'School Project', desc: 'Academic assignments & thesis' },
        { id: 'student_portfolio', name: 'Portfolio', desc: 'Early-career showcase' },
        { id: 'learning_project', name: 'Learning Project', desc: 'Mentored builds' }
    ]
};

document.addEventListener('DOMContentLoaded', () => {
    const step1 = document.getElementById('step-1');
    if (!step1) return;

    const urlParams = new URLSearchParams(window.location.search);
    const urlModule = urlParams.get('module');
    const urlPlan = urlParams.get('plan');

    if (urlModule && moduleProjects[urlModule]) {
        onboardingState.module = urlModule;
        if (projectOptionsContainer) {
            projectOptionsContainer.innerHTML = moduleProjects[urlModule].map(proj => `
                <div class="brutalist-border bg-surface p-4 cursor-pointer hover:border-primary transition-colors group" onclick="selectProjectType('${proj.name}')">
                    <h3 class="text-xl font-bold mb-2 group-hover:text-primary transition-colors">> ${proj.name}</h3>
                    <p class="text-sm text-on-surface-variant">${proj.desc}</p>
                </div>
            `).join('');
            projectOptionsContainer.classList.remove('hidden');
        }
        if (moduleSelectFallback) moduleSelectFallback.classList.add('hidden');
        goToStep(1);
    } else if (urlPlan) {
        // Find price roughly based on plan name
        const planPrices = {
            'MINI': 500, 'STARTER': 999, 'BASIC': 2999, 'STANDARD': 4999,
            'PRO': 9999, 'ADVANCED': 14999, 'ELITE': 29999, 'ENTERPRISE': 50000
        };
        onboardingState.plan = urlPlan;
        onboardingState.basePrice = planPrices[urlPlan] || 0;

        const reqPlanInput = document.getElementById('req-plan');
        if (reqPlanInput) reqPlanInput.value = urlPlan;

        const reqProjectInput = document.getElementById('req-project');
        if (reqProjectInput) {
            reqProjectInput.value = "Unspecified (from Pricing)";
            reqProjectInput.removeAttribute('readonly');
        }

        goToStep('speed');
    } else {
        if (projectOptionsContainer) projectOptionsContainer.classList.add('hidden');
        if (moduleSelectFallback) moduleSelectFallback.classList.remove('hidden');
        goToStep(1);
    }
});

function goToStep(stepNum) {
    document.querySelectorAll('.step-container').forEach(el => {
        el.classList.add('hidden');
        el.classList.remove('flex');
    });

    const targetStep = document.getElementById(`step-${stepNum}`);
    if (targetStep) {
        targetStep.classList.remove('hidden');
        if (stepNum === 4) {
            targetStep.classList.add('flex');
        }
    }

    if (stepIndicator && currentStepNum && progressBar) {
        if (stepNum === 1) {
            currentStepNum.innerText = '1';
            stepIndicator.innerText = '> SELECT_PROJECT';
            progressBar.style.width = '25%';
        } else if (stepNum === 2) {
            currentStepNum.innerText = '2';
            stepIndicator.innerText = '> ALLOCATE_PLAN';
            progressBar.style.width = '50%';
        } else if (stepNum === 'speed') {
            currentStepNum.innerText = '3';
            stepIndicator.innerText = '> SET_DELIVERY';
            progressBar.style.width = '75%';
            // Update UI base price display
            const basePriceDisplay = document.getElementById('current-base-price');
            if (basePriceDisplay) basePriceDisplay.innerText = `₹${onboardingState.basePrice.toLocaleString()}`;
        } else if (stepNum === 3) {
            currentStepNum.innerText = '4';
            stepIndicator.innerText = '> INPUT_SPECS';
            progressBar.style.width = '100%';

            // Update total price display
            const finalTotalDisplay = document.getElementById('final-total-price');
            if (finalTotalDisplay) {
                const total = onboardingState.basePrice + onboardingState.speedPrice;
                finalTotalDisplay.innerText = `₹${total.toLocaleString()}`;
            }
        }
    }
}

function selectProjectType(projectName) {
    onboardingState.projectType = projectName;
    const reqProjectInput = document.getElementById('req-project');
    if (reqProjectInput) {
        reqProjectInput.value = projectName;
    }
    goToStep(2);
}

function selectPlan(planName, price) {
    onboardingState.plan = planName;
    onboardingState.basePrice = price;
    const reqPlanInput = document.getElementById('req-plan');
    if (reqPlanInput) {
        reqPlanInput.value = planName;
    }
    goToStep('speed');
}

function selectSpeed(speedName, extraPrice) {
    onboardingState.speed = speedName;
    onboardingState.speedPrice = extraPrice;
    const reqSpeedInput = document.getElementById('req-speed');
    if (reqSpeedInput) {
        reqSpeedInput.value = speedName;
    }
    goToStep(3);
}

if (requirementsForm) {
    requirementsForm.addEventListener('submit', async (e) => {
        e.preventDefault();

        const btn = document.getElementById('submit-requirements-btn');
        const originalText = btn.innerHTML;
        btn.innerHTML = '<span class="relative z-10">> TRANSMITTING TO SERVER...</span>';
        btn.classList.add('animate-pulse');

        const formData = new FormData();
        formData.append('name', document.getElementById('req-name').value);
        formData.append('email', document.getElementById('req-email').value);
        formData.append('phone', document.getElementById('req-phone').value);

        const reqProjInput = document.getElementById('req-project');
        formData.append('projectType', reqProjInput ? reqProjInput.value : onboardingState.projectType);

        const reqPlanInput = document.getElementById('req-plan');
        formData.append('plan', reqPlanInput ? reqPlanInput.value : onboardingState.plan);

        const reqSpeedInput = document.getElementById('req-speed');
        formData.append('deliverySpeed', reqSpeedInput ? reqSpeedInput.value : onboardingState.speed);

        formData.append('budget', document.getElementById('req-budget').value);
        formData.append('timeline', document.getElementById('req-timeline').value);
        formData.append('features', document.getElementById('req-features').value);

        try {
            const response = await fetch('/submit-requirements', {
                method: 'POST',
                body: formData
            });
            const result = await response.json();

            if (result.status === 'success') {
                const bookingDisplay = document.getElementById('booking-id-display');
                if (bookingDisplay) {
                    bookingDisplay.innerText = result.booking_id;
                }
                goToStep(4);
            }
        } catch (error) {
            console.error("Transmission error:", error);
            alert("Error communicating with server. Please try again.");
        } finally {
            btn.innerHTML = originalText;
            btn.classList.remove('animate-pulse');
        }
    });
}

function copyBookingId() {
    const bookingId = document.getElementById('booking-id-display').innerText;
    navigator.clipboard.writeText(bookingId).then(() => {
        const statusEl = document.getElementById('copy-status');
        if (statusEl) {
            statusEl.innerText = "> COPIED TO CLIPBOARD";
            setTimeout(() => {
                statusEl.innerText = "";
            }, 3000);
        }
    });
}

// --- SCROLL PROGRESS & REVEAL ANIMATIONS (ABOUT PAGE) ---
document.addEventListener('DOMContentLoaded', () => {
    // Progress Bar
    const originProgressBar = document.getElementById('origin-progress-bar');
    if (originProgressBar) {
        window.addEventListener('scroll', () => {
            const scrollTop = window.scrollY || document.documentElement.scrollTop;
            const scrollHeight = document.documentElement.scrollHeight - document.documentElement.clientHeight;
            const progress = (scrollTop / scrollHeight) * 100;
            originProgressBar.style.width = progress + '%';
        });
    }

    // Section Reveal on Scroll
    const revealElements = document.querySelectorAll('.reveal-section');
    if (revealElements.length > 0) {
        const revealOptions = {
            threshold: 0.15,
            rootMargin: "0px 0px -50px 0px"
        };

        const revealObserver = new IntersectionObserver(function(entries, observer) {
            entries.forEach(entry => {
                if (!entry.isIntersecting) return;

                entry.target.classList.add('is-visible');
                observer.unobserve(entry.target); // Only animate once
            });
        }, revealOptions);

        revealElements.forEach(el => {
            revealObserver.observe(el);
        });
    }
});
