
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
document.addEventListener('DOMContentLoaded', () => {
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

        // Also close when clicking links
        const mobileLinks = mobileNav.querySelectorAll('a');
        mobileLinks.forEach(link => {
            link.addEventListener('click', () => {
                mobileNav.classList.add('translate-x-full');
            });
        });
    }
});

// --- WORKBENCH FILTERING ---
document.addEventListener('DOMContentLoaded', () => {
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
});

// --- CASE STUDY MODAL ---
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

window.openModal = function(projectId) {
    const caseModal = document.getElementById('case-modal');
    const modalContent = document.getElementById('modal-content');
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

window.closeModal = function() {
    const caseModal = document.getElementById('case-modal');
    if(!caseModal) return;
    caseModal.classList.add('hidden');
    document.body.style.overflow = 'auto';
}

document.addEventListener('DOMContentLoaded', () => {
    const caseModal = document.getElementById('case-modal');
    if(caseModal) {
        caseModal.addEventListener('click', (e) => {
            if (e.target === caseModal) {
                window.closeModal();
            }
        });
    }
});

// --- TERMINAL COMMAND SYSTEM ---
document.addEventListener('DOMContentLoaded', () => {
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
});

// --- TOAST NOTIFICATIONS ---
function showToast(message, type = 'success') {
    const toast = document.getElementById('global-toast');
    const toastMsg = document.getElementById('toast-message');
    if (!toast || !toastMsg) return;

    toastMsg.innerText = `> ${message}`;

    if (type === 'error') {
        toast.classList.replace('bg-primary', 'bg-red-500');
        toast.classList.replace('border-primary', 'border-red-500');
        toast.classList.replace('shadow-[0_0_20px_rgba(0,255,65,0.4)]', 'shadow-[0_0_20px_rgba(239,68,68,0.4)]');
    } else {
        toast.classList.replace('bg-red-500', 'bg-primary');
        toast.classList.replace('border-red-500', 'border-primary');
        toast.classList.replace('shadow-[0_0_20px_rgba(239,68,68,0.4)]', 'shadow-[0_0_20px_rgba(0,255,65,0.4)]');
    }

    toast.classList.remove('-translate-y-[200%]', 'opacity-0');
    toast.classList.add('translate-y-0', 'opacity-100');

    setTimeout(() => {
        toast.classList.add('-translate-y-[200%]', 'opacity-0');
        toast.classList.remove('translate-y-0', 'opacity-100');
    }, 3000);
}

// --- MULTI-STEP ONBOARDING LOGIC (requirements.html) ---
const projectOptionsContainer = document.getElementById('project-options');
const stepIndicator = document.getElementById('step-indicator');
const currentStepNum = document.getElementById('current-step-num');
const progressBar = document.getElementById('progress-bar');
const moduleSelectFallback = document.getElementById('module-select-fallback');

let onboardingState = {
    module: '',
    projectType: '',
    plan: '',
    basePrice: 0,
    discountAmount: 0,
    couponCode: '',
    finalPrice: 0,
    advancePaid: 0,
    remainingAmount: 0,
    settings: {
        UPI_ID: 'bina.patil@axl',
        MIN_ADVANCE: 10,
        MAX_ADVANCE_PERCENT: 100
    }
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

document.addEventListener('DOMContentLoaded', async () => {
    const step1 = document.getElementById('step-1');
    if (!step1) return;

    // Fetch settings
    try {
        const res = await fetch('/api/settings');
        const data = await res.json();
        if(data.status === 'success') {
            if(data.settings['UPI_ID']) onboardingState.settings.UPI_ID = data.settings['UPI_ID'];
            if(data.settings['MIN_ADVANCE']) onboardingState.settings.MIN_ADVANCE = parseFloat(data.settings['MIN_ADVANCE']);
            if(data.settings['MAX_ADVANCE_PERCENT']) onboardingState.settings.MAX_ADVANCE_PERCENT = parseFloat(data.settings['MAX_ADVANCE_PERCENT']);
        }
    } catch(e) { console.error("Settings fetch error:", e); }

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
        goToStep(3);
    } else {
        if (projectOptionsContainer) projectOptionsContainer.classList.add('hidden');
        if (moduleSelectFallback) moduleSelectFallback.classList.remove('hidden');
        goToStep(1);
    }
});

window.goToStep = function(stepNum) {
    document.querySelectorAll('.step-container').forEach(el => {
        el.classList.add('hidden');
        el.classList.remove('flex');
    });

    const targetStep = document.getElementById(`step-${stepNum}`);
    if (targetStep) {
        targetStep.classList.remove('hidden');
        if (stepNum === 5) {
            targetStep.classList.add('flex');
        }
    }

    if (stepIndicator && currentStepNum && progressBar) {
        if (stepNum === 1) {
            currentStepNum.innerText = '1';
            stepIndicator.innerText = '> SELECT_PROJECT';
            progressBar.style.width = '20%';
        } else if (stepNum === 2) {
            currentStepNum.innerText = '2';
            stepIndicator.innerText = '> ALLOCATE_PLAN';
            progressBar.style.width = '40%';
        } else if (stepNum === 3) {
            currentStepNum.innerText = '3';
            stepIndicator.innerText = '> INPUT_SPECS';
            progressBar.style.width = '60%';
        } else if (stepNum === 4) {
            currentStepNum.innerText = '4';
            stepIndicator.innerText = '> CHECKOUT_EXECUTION';
            progressBar.style.width = '80%';
            updateCheckoutUI();
        }
    }
};

window.selectProjectType = function(projectName) {
    onboardingState.projectType = projectName;
    const reqProjectInput = document.getElementById('req-project');
    if (reqProjectInput) reqProjectInput.value = projectName;
    goToStep(2);
};

window.selectPlan = function(planName, price) {
    onboardingState.plan = planName;
    onboardingState.basePrice = price;
    const reqPlanInput = document.getElementById('req-plan');
    if (reqPlanInput) reqPlanInput.value = planName;
    goToStep(3);
};

window.applyCoupon = async function() {
    const couponInput = document.getElementById('coupon-input');
    const msgEl = document.getElementById('coupon-msg');
    const code = couponInput.value.trim();
    if(!code) return;

    msgEl.classList.remove('hidden', 'text-red-500', 'text-primary');
    msgEl.classList.add('text-on-surface-variant');
    msgEl.innerText = '> VERIFYING_CODE...';

    try {
        const res = await fetch('/api/validate_coupon', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ code: code, order_value: onboardingState.basePrice })
        });
        const data = await res.json();
        if (data.status === 'success') {
            const coupon = data.coupon;
            onboardingState.couponCode = coupon.code;

            if(coupon.type === 'percent') {
                onboardingState.discountAmount = (onboardingState.basePrice * coupon.value) / 100;
            } else {
                onboardingState.discountAmount = coupon.value;
            }

            // Ensure discount doesn't exceed base price
            if(onboardingState.discountAmount > onboardingState.basePrice) {
                onboardingState.discountAmount = onboardingState.basePrice;
            }

            msgEl.innerText = `> CODE_ACCEPTED: -₹${onboardingState.discountAmount.toFixed(0)}`;
            msgEl.classList.replace('text-on-surface-variant', 'text-primary');
            updateCheckoutUI();
        } else {
            msgEl.innerText = `> ERR: ${data.message}`;
            msgEl.classList.replace('text-on-surface-variant', 'text-red-500');
            onboardingState.couponCode = '';
            onboardingState.discountAmount = 0;
            updateCheckoutUI();
        }
    } catch(e) {
        msgEl.innerText = '> ERR: VERIFICATION_FAILED';
        msgEl.classList.replace('text-on-surface-variant', 'text-red-500');
        onboardingState.couponCode = '';
        onboardingState.discountAmount = 0;
        updateCheckoutUI();
    }
};

function updateCheckoutUI() {
    onboardingState.finalPrice = onboardingState.basePrice - onboardingState.discountAmount;
    if(onboardingState.finalPrice < 0) onboardingState.finalPrice = 0;

    document.getElementById('ui-base-price').innerText = `₹${onboardingState.basePrice}`;
    document.getElementById('ui-final-price').innerText = `₹${onboardingState.finalPrice}`;

    const discRow = document.getElementById('ui-discount-row');
    if (onboardingState.discountAmount > 0) {
        discRow.classList.remove('hidden');
        document.getElementById('ui-discount-amount').innerText = `-₹${onboardingState.discountAmount}`;
    } else {
        discRow.classList.add('hidden');
    }

    // Slider Limits
    const slider = document.getElementById('advance-slider');
    const minAdvance = Math.min(onboardingState.settings.MIN_ADVANCE, onboardingState.finalPrice);
    const maxAdvance = (onboardingState.finalPrice * onboardingState.settings.MAX_ADVANCE_PERCENT) / 100;

    slider.min = minAdvance;
    slider.max = maxAdvance;
    slider.value = minAdvance; // Default to min

    document.getElementById('ui-min-advance').innerText = `MIN: ₹${minAdvance}`;
    document.getElementById('ui-max-advance').innerText = `MAX: ₹${maxAdvance}`;

    // Attach slider listener if not already
    slider.oninput = function() {
        onboardingState.advancePaid = parseInt(this.value);
        updatePaymentDetails();
    };

    // Trigger update explicitly
    slider.dispatchEvent(new Event('input'));
}

function updatePaymentDetails() {
    onboardingState.remainingAmount = onboardingState.finalPrice - onboardingState.advancePaid;
    document.getElementById('ui-advance-display').innerText = `₹${onboardingState.advancePaid}`;
    document.getElementById('ui-remaining-amount').innerText = `₹${onboardingState.remainingAmount}`;
    document.getElementById('ui-paying-amount').innerText = `₹${onboardingState.advancePaid}`;

    const upiId = onboardingState.settings.UPI_ID;
    document.getElementById('ui-upi-id').innerText = upiId;

    const upiLink = `upi://pay?pa=${upiId}&pn=DorkyBuilds&am=${onboardingState.advancePaid}&cu=INR`;
    document.getElementById('upi-pay-btn').href = upiLink;

    // Generate QR using free API
    const qrUrl = `https://api.qrserver.com/v1/create-qr-code/?size=200x200&data=${encodeURIComponent(upiLink)}&bgcolor=121212&color=00FF41`;
    document.getElementById('upi-qr').src = qrUrl;
}

window.submitFinalOrder = async function() {
    const btn = document.getElementById('final-submit-btn');

    const name = document.getElementById('req-name').value.trim();
    const email = document.getElementById('req-email').value.trim();
    const phone = document.getElementById('req-phone').value.trim();
    let selectedParams = [];
    document.querySelectorAll('input[name="param_features"]:checked').forEach(el => {
        selectedParams.push(el.value);
    });
    const addDetails = document.getElementById('req-features').value.trim();
    let features = selectedParams.length > 0 ? "Parameters: " + selectedParams.join(', ') : "";
    if (addDetails) {
        features += features ? " | Details: " + addDetails : "Details: " + addDetails;
    }

    if(!features) features = "Standard Build";
    const upiRef = document.getElementById('req-upi-ref').value.trim();
    const screenshotInput = document.getElementById('req-screenshot');

    if(!name || !email || !upiRef || !screenshotInput.files[0]) {
        if(window.showToast) window.showToast("Missing required checkout fields or screenshot.", "error");
        return;
    }

    // File validation
    const file = screenshotInput.files[0];
    const allowedExtensions = ['png', 'jpg', 'jpeg'];
    const extension = file.name.split('.').pop().toLowerCase();

    if (!allowedExtensions.includes(extension)) {
        if(window.showToast) window.showToast("Invalid file type. Only PNG, JPG, JPEG allowed.", "error");
        return;
    }

    if (file.size > 5 * 1024 * 1024) {
        if(window.showToast) window.showToast("File is too large. Max size is 5MB.", "error");
        return;
    }

    const originalText = btn.innerHTML;
    btn.innerHTML = '<span class="relative z-10 animate-pulse">> UPLOADING & TRANSMITTING...</span>';
    btn.disabled = true;

    const formData = new FormData();
    formData.append('name', name);
    formData.append('email', email);
    formData.append('phone', phone);
    formData.append('projectType', document.getElementById('req-project').value || onboardingState.projectType);
    formData.append('plan', document.getElementById('req-plan').value || onboardingState.plan);
    formData.append('budget', document.getElementById('req-budget').value);
    formData.append('timeline', document.getElementById('req-timeline').value);
    formData.append('features', features);
    formData.append('total_price', onboardingState.basePrice);
    formData.append('advance_paid', onboardingState.advancePaid);
    formData.append('remaining_amount', onboardingState.remainingAmount);
    formData.append('upi_ref_id', upiRef);
    formData.append('coupon_applied', onboardingState.couponCode);
    formData.append('discount_amount', onboardingState.discountAmount);
    formData.append('final_price', onboardingState.finalPrice);
    formData.append('screenshot', file);

    try {
        console.log("📦 [FRONTEND] Transmitting payload and file to /submit-requirements...");
        const response = await fetch('/submit-requirements', {
            method: 'POST',
            body: formData
        });
        const result = await response.json();

        if (result.status === 'success') {
            if(window.showToast) window.showToast("Order submitted successfully.", "success");
            document.getElementById('booking-id-display').innerText = result.booking_id;
            goToStep(5);
        } else {
            if(window.showToast) window.showToast(result.message || "Upload or Database Error", "error");
            btn.innerHTML = originalText;
            btn.disabled = false;
        }
    } catch (error) {
        console.error("❌ [FRONTEND] Connection or parsing error:", error);
        if(window.showToast) window.showToast("Connection failed. Check network.", "error");
        btn.innerHTML = originalText;
        btn.disabled = false;
    }
};

window.copyBookingId = function() {
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
};

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

// --- AUTHENTICATION (MOCK FIREBASE FOR LOCAL TESTING) ---
let currentUser = null;

// Mock login function simulating Firebase Google Auth
function signInWithGoogle() {
    console.log("Mock Google Sign-In initiated...");
    // Simulate successful login
    setTimeout(() => {
        currentUser = {
            uid: "mock-uid-12345",
            displayName: "Test User",
            email: "test@example.com"
        };
        localStorage.setItem("dorkyUser", JSON.stringify(currentUser));
        updateAuthUI();

        // Auto-fill requirements form email if present
        const reqEmail = document.getElementById("req-email");
        if (reqEmail && reqEmail.value === "contact@aayushpatilofficial.online") {
            reqEmail.value = currentUser.email;
        }

        // Redirect to dashboard if logged in via navbar
        if (window.location.pathname !== '/requirements') {
            window.location.href = "/dashboard";
        }
    }, 1000);
}

function signOut() {
    console.log("Signing out...");
    currentUser = null;
    localStorage.removeItem("dorkyUser");
    updateAuthUI();
    if (window.location.pathname === '/dashboard') {
        window.location.href = "/";
    }
}

function updateAuthUI() {
    const authBtn = document.getElementById("auth-btn");
    const mobileAuthBtn = document.getElementById("mobile-auth-btn");

    if (currentUser) {
        if (authBtn) {
            authBtn.innerText = "[08] DASHBOARD";
            authBtn.href = "/dashboard";
            authBtn.onclick = null;
        }
        if (mobileAuthBtn) {
            mobileAuthBtn.innerText = "[08] DASHBOARD";
            mobileAuthBtn.href = "/dashboard";
            mobileAuthBtn.onclick = null;
        }
    } else {
        if (authBtn) {
            authBtn.innerText = "[08] LOGIN";
            authBtn.href = "#";
            authBtn.onclick = (e) => { e.preventDefault(); signInWithGoogle(); };
        }
        if (mobileAuthBtn) {
            mobileAuthBtn.innerText = "[08] LOGIN";
            mobileAuthBtn.href = "#";
            mobileAuthBtn.onclick = (e) => { e.preventDefault(); signInWithGoogle(); };
        }
    }
}

// Initialize Auth State on Load
document.addEventListener("DOMContentLoaded", () => {
    const storedUser = localStorage.getItem("dorkyUser");
    if (storedUser) {
        currentUser = JSON.parse(storedUser);
    }
    updateAuthUI();
});



// --- DYNAMIC BANNER ---
document.addEventListener('DOMContentLoaded', async () => {
    try {
        const res = await fetch('/api/banner');
        const data = await res.json();

        if (data.status === 'success' && data.banner) {
            const banner = document.getElementById('dynamic-banner');
            const nav = document.getElementById('main-nav');

            if (banner) {
                banner.innerText = data.banner.banner_text;
                banner.style.backgroundColor = data.banner.background_color || '#000000';
                banner.style.color = data.banner.text_color || '#00FF41';
                banner.style.display = 'block';

                // Adjust nav position
                const bannerHeight = banner.offsetHeight;
                if(nav) nav.style.top = bannerHeight + 'px';

                // Auto hide
                const duration = parseInt(data.banner.duration_seconds || 30);
                setTimeout(() => {
                    banner.style.display = 'none';
                    if(nav) nav.style.top = '0px';
                }, duration * 1000);
            }
        }
    } catch(e) {
        console.error("Banner fetch failed:", e);
    }
});
