Progressive Web App functionality

// Install button handler
let deferredPrompt;

window.addEventListener('beforeinstallprompt', (e) => {
    console.log('💡 PWA: Install prompt available');
    e.preventDefault();
    deferredPrompt = e;
    
    // Show custom install UI
    showInstallPromotion();
});

function showInstallPromotion() {
    const installBanner = document.createElement('div');
    installBanner.id = 'installBanner';
    installBanner.style.cssText = `
        position: fixed;
        bottom: 20px;
        left: 50%;
        transform: translateX(-50%);
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 16px 24px;
        border-radius: 12px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.2);
        z-index: 9999;
        display: flex;
        align-items: center;
        gap: 16px;
        animation: slideUp 0.3s ease-out;
    `;
    
    installBanner.innerHTML = `
        <div style="flex: 1;">
            <div style="font-weight: 600; margin-bottom: 4px;">📱 Install SocialHub</div>
            <div style="font-size: 13px; opacity: 0.9;">Get quick access from your home screen</div>
        </div>
        <button id="installBtn" style="
            background: white;
            color: #667eea;
            border: none;
            padding: 8px 16px;
            border-radius: 6px;
            font-weight: 600;
            cursor: pointer;
        ">Install</button>
        <button id="dismissBtn" style="
            background: rgba(255,255,255,0.2);
            color: white;
            border: none;
            padding: 8px 16px;
            border-radius: 6px;
            cursor: pointer;
        ">Not now</button>
    `;
    
    document.body.appendChild(installBanner);
    
    document.getElementById('installBtn').addEventListener('click', async () => {
        installBanner.remove();
        
        if (deferredPrompt) {
            deferredPrompt.prompt();
            const { outcome } = await deferredPrompt.userChoice;
            console.log(`PWA install outcome: ${outcome}`);
            
            if (outcome === 'accepted') {
                console.log('✅ PWA installed');
            }
            
            deferredPrompt = null;
        }
    });
    
    document.getElementById('dismissBtn').addEventListener('click', () => {
        installBanner.remove();
        localStorage.setItem('installPromptDismissed', Date.now());
    });
    
    // Auto-dismiss after 10 seconds
    setTimeout(() => {
        if (document.getElementById('installBanner')) {
            installBanner.remove();
        }
    }, 10000);
}

// Check if should show install prompt
window.addEventListener('load', () => {
    const lastDismissed = localStorage.getItem('installPromptDismissed');
    if (lastDismissed) {
        const daysSinceDismissed = (Date.now() - parseInt(lastDismissed)) / (1000 * 60 * 60 * 24);
        if (daysSinceDismissed < 7) {
            console.log('Install prompt dismissed recently');
            return;
        }
    }
});

// Handle app installation
window.addEventListener('appinstalled', () => {
    console.log('✅ PWA: App installed successfully');
    deferredPrompt = null;
    
    // Show success message
    const successMsg = document.createElement('div');
    successMsg.className = 'notification success';
    successMsg.textContent = '✅ SocialHub installed! You can now access it from your home screen.';
    successMsg.style.position = 'fixed';
    successMsg.style.top = '90px';
    successMsg.style.right = '20px';
    successMsg.style.zIndex = '9999';
    document.body.appendChild(successMsg);
    
    setTimeout(() => successMsg.remove(), 4000);
});

// Check if running as installed PWA
function isStandalone() {
    return window.matchMedia('(display-mode: standalone)').matches ||
           window.navigator.standalone ||
           document.referrer.includes('android-app://');
}

if (isStandalone()) {
    console.log('✅ Running as installed PWA');
    document.body.classList.add('pwa-installed');
}

// Handle offline/online status for PWA
if ('serviceWorker' in navigator) {
    window.addEventListener('online', () => {
        console.log('✅ Back online');
        if ('serviceWorker' in navigator && navigator.serviceWorker.controller) {
            navigator.serviceWorker.controller.postMessage({ type: 'ONLINE' });
        }
    });
    
    window.addEventListener('offline', () => {
        console.log('❌ Offline mode');
    });
}

// Share API support
async function shareContent(title, text, url) {
    if (navigator.share) {
        try {
            await navigator.share({
                title: title,
                text: text,
                url: url
            });
            console.log('✅ Content shared');
        } catch (err) {
            console.log('Share cancelled or failed:', err);
        }
    } else {
        // Fallback: copy to clipboard
        navigator.clipboard.writeText(url).then(() => {
            alert('Link copied to clipboard!');
        });
    }
}

// Make share function available globally
window.shareContent = shareContent;

console.log('📱 PWA functionality loaded');
