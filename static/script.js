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
        const storedUser = localStorage.getItem("dorkyUser");
        if (storedUser) {
            const userObj = JSON.parse(storedUser);
            formData.append('uid', userObj.uid);
        } else {
            formData.append('uid', 'anonymous');
        }
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
            console.log("📦 [FRONTEND] Transmitting payload to /submit-requirements...");
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
            showToast("Error communicating with server.", "error");
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
