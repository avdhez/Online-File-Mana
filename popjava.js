
  var popup2004 = {
    // Configuration
    timer: null,
    secondsLeft: 20,
    timerRunning: false,
    storageKey: 'popup2004_data',
    externalUrl: 'https://otieu.com/4/9646541', // Replace with your actual URL
    lastActiveTime: null,
    timeSpentAway: 0,
    cooldownEnd: null,
    savedScrollPosition: 0,
    
    // Initialize the popup system
    init: function() {
      this.setupElements();
      this.restoreState();
      
      // Set up event listeners
      document.addEventListener('visibilitychange', this.handleVisibilityChange.bind(this));
      window.addEventListener('beforeunload', this.saveState.bind(this));
      window.addEventListener('load', this.checkShouldShow.bind(this));
    },
    
    // Set up DOM element event listeners
    setupElements: function() {
      var popup = this;
      
      document.getElementById('popup2004-link').addEventListener('click', function(e) {
        e.preventDefault();
        popup.handleLinkClick();
      });
      
      document.getElementById('popup2004-close').addEventListener('click', function() {
        popup.closePopup();
      });
    },
    
    // Check if we should show the popup (considering cooldown)
    checkShouldShow: function() {
      var now = Date.now();
      
      // Reset cooldown if expired (using device clock)
      if (this.cooldownEnd && now >= this.cooldownEnd) {
        this.cooldownEnd = null;
        this.saveState();
      }
      
      // Don't show if in cooldown period
      if (this.cooldownEnd) {
        var minutesLeft = Math.ceil((this.cooldownEnd - now) / 60000);
        console.log('Cooldown active: ' + minutesLeft + ' minutes remaining');
        return;
      }
      
      // Show popup if there's remaining time or no completion recorded
      if (this.secondsLeft < 20 || !this.cooldownEnd) {
        this.showPopup();
        this.updateTimerDisplay();
        
        if (this.timerRunning) {
          document.getElementById('popup2004-message').style.display = 'block';
        }
      }
    },
    
    // Handle when user clicks the external link
    handleLinkClick: function() {
      window.open(this.externalUrl, '_blank');
      this.lastActiveTime = Date.now();
      
      if (!this.timerRunning) {
        this.startTimer();
      } else {
        this.resumeTimer();
      }
    },
    
    // Start the countdown timer
    startTimer: function() {
      this.secondsLeft = 20;
      this.timerRunning = true;
      this.timeSpentAway = 0;
      document.getElementById('popup2004-message').style.display = 'none';
      this.runTimer();
      this.showPopup();
    },
    
    // Resume timer after interruption
    resumeTimer: function() {
      var remainingTime = 20000 - this.timeSpentAway;
      this.secondsLeft = Math.ceil(remainingTime / 1000);
      
      this.timerRunning = true;
      document.getElementById('popup2004-message').style.display = 'none';
      this.runTimer();
    },
    
    // Run the timer countdown
    runTimer: function() {
      if (this.timer) clearInterval(this.timer);
      
      this.updateTimerDisplay();
      
      var popup = this;
      this.timer = setInterval(function() {
        popup.secondsLeft--;
        popup.updateTimerDisplay();
        
        if (popup.secondsLeft <= 0) {
          popup.completeTask();
        }
        
        popup.saveState();
      }, 1000);
    },
    
    // Pause the timer when user leaves
    pauseTimer: function() {
      if (this.timer) {
        clearInterval(this.timer);
        this.timer = null;
      }
      this.timerRunning = false;
      
      if (this.lastActiveTime) {
        this.timeSpentAway += (Date.now() - this.lastActiveTime);
      }
      
      this.saveState();
    },
    
    // Handle when user switches tabs/windows
    handleVisibilityChange: function() {
      if (document.visibilityState === 'visible') {
        if (this.lastActiveTime && this.timerRunning) {
          var timeAway = Date.now() - this.lastActiveTime;
          
          if (timeAway < 20000) {
            this.pauseTimer();
            var remaining = Math.ceil((20000 - this.timeSpentAway)/1000);
            document.getElementById('popup2004-message').textContent = 
              'Please complete ' + remaining + ' more seconds on the external site';
            document.getElementById('popup2004-message').style.display = 'block';
          }
        }
      } else if (document.visibilityState === 'hidden' && this.timerRunning) {
        this.lastActiveTime = Date.now();
      }
    },
    
    // Complete the 20-second requirement
    completeTask: function() {
      clearInterval(this.timer);
      document.getElementById('popup2004-close').style.display = 'block';
      this.timerRunning = false;
      this.timeSpentAway = 0;
      
      // Set cooldown to 30 minutes from current device time
      this.cooldownEnd = Date.now() + (40 * 60 * 1000); // 30 minutes in ms
      this.saveState();
    },
    
    // Close the popup overlay
    closePopup: function() {
      document.getElementById('popup2004-overlay').style.display = 'none';
      this.enableScroll(); // Re-enable scrolling
      this.resetTimer();
    },
    
    // Reset timer to initial state
    resetTimer: function() {
      this.secondsLeft = 20;
      this.timerRunning = false;
      this.timeSpentAway = 0;
      this.updateTimerDisplay();
      document.getElementById('popup2004-close').style.display = 'none';
      document.getElementById('popup2004-message').style.display = 'none';
    },
    
    // Show the popup overlay
    showPopup: function() {
      this.disableScroll(); // Disable scrolling first
      document.getElementById('popup2004-overlay').style.display = 'block';
    },
    
    // Disable page scrolling
    disableScroll: function() {
      // Save current scroll position
      this.savedScrollPosition = window.pageYOffset || document.documentElement.scrollTop;
      
      // Apply scroll lock styles
      document.body.style.overflow = 'hidden';
      document.body.style.position = 'fixed';
      document.body.style.top = `-${this.savedScrollPosition}px`;
      document.body.style.width = '100%';
    },
    
    // Enable page scrolling
    enableScroll: function() {
      // Remove scroll lock styles
      document.body.style.overflow = '';
      document.body.style.position = '';
      document.body.style.top = '';
      document.body.style.width = '';
      
      // Restore scroll position
      window.scrollTo(0, this.savedScrollPosition);
    },
    
    // Load saved state from localStorage
    restoreState: function() {
      var data = localStorage.getItem(this.storageKey);
      if (data) {
        data = JSON.parse(data);
        this.secondsLeft = data.secondsLeft || 20;
        this.timerRunning = data.timerRunning || false;
        this.lastActiveTime = data.lastActiveTime || null;
        this.timeSpentAway = data.timeSpentAway || 0;
        this.cooldownEnd = data.cooldownEnd || null;
        
        // Check if cooldown has expired
        if (this.cooldownEnd && Date.now() >= this.cooldownEnd) {
          this.cooldownEnd = null;
        }
      }
    },
    
    // Save current state to localStorage
    saveState: function() {
      var data = {
        secondsLeft: this.secondsLeft,
        timerRunning: this.timerRunning,
        lastActiveTime: this.lastActiveTime,
        timeSpentAway: this.timeSpentAway,
        cooldownEnd: this.cooldownEnd
      };
      
      localStorage.setItem(this.storageKey, JSON.stringify(data));
    },
    
    // Update the timer display
    updateTimerDisplay: function() {
      document.getElementById('popup2004-timer').textContent = 'Time remaining: ' + this.secondsLeft + 's';
    }
  };
  
  // Initialize when DOM is ready
  document.addEventListener('DOMContentLoaded', function() {
    popup2004.init();
  });

         