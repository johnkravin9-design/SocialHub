// Real-time Notifications System
let socket = null; let notificationCount = 0;
// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', function() { 
    initializeNotifications(); updateNotificationBadge();
    
    // Update badge every 30 seconds
    setInterval(updateNotificationBadge, 30000);
});
function initializeNotifications() {
    // Connect to Socket.IO if available
    if (typeof io !== 'undefined') { socket = io();
        
        socket.on('connect', function() { console.log('✅ 
            Notifications: Connected');
        });
        
        socket.on('disconnect', function() { console.log('❌ 
            Notifications: Disconnected');
        });
        
        // Listen for new notifications
        socket.on('new_notification', function(data) { 
            console.log('🔔 New notification:', data); 
            showNotificationPopup(data); 
            updateNotificationBadge(); 
            playNotificationSound();
        });
        
        // Listen for new pokes
        socket.on('new_poke', function(data) { console.log('👋 
            New poke:', data); showPokeNotification(data); 
            updateNotificationBadge(); 
            playNotificationSound();
        });
    }
}
async function updateNotificationBadge() { try { const 
        response = await fetch('/api/notifications/count'); 
        const data = await response.json(); notificationCount 
        = data.count;
        
        const badge = document.getElementById('notifBadge'); 
        if (badge) {
            if (notificationCount > 0) { badge.textContent = 
                notificationCount > 9 ? '9+' : 
                notificationCount; badge.style.display = 
                'flex';
            } else {
                badge.style.display = 'none';
            }
        }
    } catch (error) {
        console.error('Error fetching notification count:', 
        error);
    }
}
function showNotificationPopup(data) { const popup = 
    document.createElement('div'); popup.className = 
    'notification-popup'; popup.style.cssText = `
        position: fixed; top: 90px; right: 20px; background: 
        white; padding: 16px; border-radius: 12px; box-shadow: 
        0 4px 12px rgba(0,0,0,0.15); max-width: 350px; 
        z-index: 9999; animation: slideInRight 0.3s ease-out; 
        cursor: pointer;
    `;
    
    popup.innerHTML = ` <div style="display: flex; gap: 12px; 
        align-items: start;">
            <div style="font-size: 32px;">🔔</div> <div 
            style="flex: 1;">
                <div style="font-weight: 600; margin-bottom: 
                4px;">New Notification</div> <div 
                style="color: #65676b; font-size: 
                14px;">${data.message || data.content}</div>
            </div> <button 
            onclick="this.parentElement.parentElement.remove()" 
            style="
                background: none; border: none; font-size: 
                20px; cursor: pointer; color: #65676b;
            ">×</button> </div> `;
    
    popup.addEventListener('click', function() { 
        window.location.href = '/notifications';
    });
    
    document.body.appendChild(popup);
    
    setTimeout(() => { popup.style.opacity = '0'; 
        popup.style.transform = 'translateX(400px)'; 
        setTimeout(() => popup.remove(), 300);
    }, 5000);
}
function showPokeNotification(data) { const popup = 
    document.createElement('div'); popup.className = 
    'notification-popup'; popup.style.cssText = `
        position: fixed; top: 90px; right: 20px; background: 
        linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
        color: white; padding: 16px; border-radius: 12px; 
        box-shadow: 0 4px 12px rgba(0,0,0,0.15); max-width: 
        350px; z-index: 9999; animation: slideInRight 0.3s 
        ease-out; cursor: pointer;
    `;
    
    popup.innerHTML = ` <div style="display: flex; gap: 12px; 
        align-items: center;">
            <div style="font-size: 48px;">👋</div> <div 
            style="flex: 1;">
                <div style="font-weight: 600; margin-bottom: 
                4px;">
                    ${data.from_user} poked you! </div> <div 
                style="font-size: 13px; opacity: 0.9;">
                    Click to poke back </div> </div> </div> `;
    
    popup.addEventListener('click', function() { 
        window.location.href = '/pokes';
    });
    
    document.body.appendChild(popup);
    
    setTimeout(() => { popup.style.opacity = '0'; 
        popup.style.transform = 'translateX(400px)'; 
        setTimeout(() => popup.remove(), 300);
    }, 5000);
}
// Request notification permission
if ('Notification' in window && Notification.permission === 
'default') {
    Notification.requestPermission().then(permission => {
        console.log('Notification permission:', pe
