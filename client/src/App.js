import './App.css';
import { useState, useEffect } from 'react';
import { auth, signInWithGoogle, logOut } from './firebase';
import { onAuthStateChanged } from 'firebase/auth';
import ProfileSetup from './components/ProfileSetup/ProfileSetup';

function App() {
  const [showButtons, setShowButtons] = useState(false);
  const [canClick, setCanClick] = useState(false);
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [profileComplete, setProfileComplete] = useState(false);
  const [showAccountMenu, setShowAccountMenu] = useState(false);
  const [isMenuClosing, setIsMenuClosing] = useState(false);

  useEffect(() => {
    // Enable clicking after initial animation completes
    const timer = setTimeout(() => {
      setCanClick(true);
    }, 1500);

    // Listen for auth state changes
    const unsubscribe = onAuthStateChanged(auth, (currentUser) => {
      setUser(currentUser);
      setLoading(false);
      // Ensure menu is closed when user changes
      setShowAccountMenu(false);
      setIsMenuClosing(false);
    });

    return () => {
      clearTimeout(timer);
      unsubscribe();
    };
  }, []);

  const handleScreenClick = (e) => {
    // Don't trigger if clicking on buttons
    if (e.target.closest('.auth-button') || e.target.closest('.logout-button')) {
      return;
    }
    if (canClick && !showButtons && !user) {
      setShowButtons(true);
    }
  };

  const handleGoogleLogin = async (e) => {
    e.stopPropagation();
    try {
      await signInWithGoogle();
    } catch (error) {
      console.error("Login failed:", error);
    }
  };

  const handleGoogleSignup = async (e) => {
    e.stopPropagation();
    // For Google OAuth, login and signup use the same flow
    try {
      await signInWithGoogle();
    } catch (error) {
      console.error("Signup failed:", error);
    }
  };

  const handleLogout = async (e) => {
    e.stopPropagation();
    try {
      await logOut();
      setShowButtons(false);
      setProfileComplete(false);
    } catch (error) {
      console.error("Logout failed:", error);
    }
  };

  const toggleAccountMenu = () => {
    if (showAccountMenu) {
      // Start closing animation
      setIsMenuClosing(true);
      setTimeout(() => {
        setShowAccountMenu(false);
        setIsMenuClosing(false);
      }, 300); // Match animation duration
    } else {
      setShowAccountMenu(true);
    }
  };

  const handleMouseLeave = () => {
    if (showAccountMenu && !isMenuClosing) {
      setIsMenuClosing(true);
      setTimeout(() => {
        setShowAccountMenu(false);
        setIsMenuClosing(false);
      }, 300); // Match animation duration
    }
  };

  const handleProfileComplete = (profileData) => {
    console.log('Profile data:', profileData);
    // TODO: Save profile data to database
    setProfileComplete(true);
  };

  if (loading) {
    return (
      <div className="App">
        <div className="loading">Loading...</div>
      </div>
    );
  }

  // If user is logged in, show profile setup or dashboard
  if (user) {
    // Show profile setup if not completed
    if (!profileComplete) {
      return (
        <div className="App">
          <div className="account-button-container" onMouseLeave={handleMouseLeave}>
            {showAccountMenu && (
              <div className={`account-menu ${isMenuClosing ? 'closing' : ''}`}>
                <button className="account-menu-button">Account</button>
                <button className="account-menu-button logout" onClick={handleLogout}>
                  Log Out
                </button>
              </div>
            )}
            <button 
              className="account-button" 
              onClick={toggleAccountMenu}
            >
              <svg className="account-icon" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <circle cx="12" cy="8" r="4" stroke="#EDEDCE" strokeWidth="2"/>
                <path d="M4 20C4 16.6863 6.68629 14 10 14H14C17.3137 14 20 16.6863 20 20" stroke="#EDEDCE" strokeWidth="2" strokeLinecap="round"/>
              </svg>
            </button>
          </div>
          <ProfileSetup onComplete={handleProfileComplete} />
        </div>
      );
    }

    // Show dashboard after profile is complete
    return (
      <div className="App">
        <div className="account-button-container" onMouseLeave={handleMouseLeave}>
          {showAccountMenu && (
            <div className={`account-menu ${isMenuClosing ? 'closing' : ''}`}>
              <button className="account-menu-button">Account</button>
              <button className="account-menu-button logout" onClick={handleLogout}>
                Log Out
              </button>
            </div>
          )}
          <button 
            className="account-button" 
            onClick={toggleAccountMenu}
          >
            <svg className="account-icon" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <circle cx="12" cy="8" r="4" stroke="#EDEDCE" strokeWidth="2"/>
              <path d="M4 20C4 16.6863 6.68629 14 10 14H14C17.3137 14 20 16.6863 20 20" stroke="#EDEDCE" strokeWidth="2" strokeLinecap="round"/>
            </svg>
          </button>
        </div>
        <div className="dashboard">
          <h1 className="title">ASCEND.ai</h1>
          <div className="user-info">
            <img 
              src={user.photoURL || '/default-avatar.png'} 
              alt="Profile" 
              className="user-avatar"
            />
            <h2 className="welcome-text">Welcome, {user.displayName || 'User'}!</h2>
            <p className="user-email">{user.email}</p>
          </div>
        </div>
      </div>
    );
  }

  // Landing page for non-authenticated users
  return (
    <div className="App" onClick={handleScreenClick}>
      <div className={`content-container ${showButtons ? 'show-buttons' : ''}`}>
        <h1 className="title">ASCEND.ai</h1>
        <div className="image-container">
          <img 
            src="/island.png" 
            alt="Ascend Island" 
            className="island-image"
          />
        </div>
        
        <div className={`button-container ${showButtons ? 'visible' : ''}`}>
          <button className="auth-button login-button" onClick={handleGoogleLogin}>
            <svg className="google-icon" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
              <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" fill="#4285F4"/>
              <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853"/>
              <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" fill="#FBBC05"/>
              <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="#EA4335"/>
            </svg>
            Login with Google
          </button>
          <button className="auth-button signup-button" onClick={handleGoogleSignup}>
            <svg className="google-icon" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
              <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" fill="#4285F4"/>
              <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853"/>
              <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" fill="#FBBC05"/>
              <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="#EA4335"/>
            </svg>
            Sign up with Google
          </button>
        </div>
      </div>
      
      {canClick && !showButtons && (
        <div className="click-hint">Click anywhere to continue</div>
      )}
    </div>
  );
}

export default App;
