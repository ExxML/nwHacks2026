import './AccountPage.css';
import { useState, useEffect, useRef, useCallback } from 'react';
import { getUserProfile, updateUserProfile } from '../../firebase';

const profileFields = [
  {
    id: 'age',
    label: 'Age',
    options: [
      'Under 18',
      '18–24',
      '25–29',
      '30–34',
      '35–44',
      '45–54',
      '55–64',
      '65–74',
      '75+'
    ]
  },
  {
    id: 'location',
    label: 'Location',
    type: 'text',
    placeholder: 'Enter your city'
  },
  {
    id: 'propertyValue',
    label: 'Property Value',
    options: [
      'Prefer not to say',
      'No property',
      '<$100k',
      '$100k–$200k',
      '$200k–$350k',
      '$350k–$500k',
      '$500k–$750k',
      '$750k–$1M',
      '$1M–$1.5M',
      '$1.5M+',
    ]
  },
  {
    id: 'vehicleValue',
    label: 'Vehicle Value',
    options: [
      'Prefer not to say',
      'No car',
      '<$5k',
      '$5k–$10k',
      '$10k–$20k',
      '$20k–$35k',
      '$35k–$50k',
      '$50k–$75k',
      '$75k+'
    ]
  },
  {
    id: 'investments',
    label: 'Investments',
    options: [
      'Prefer not to say',
      '$0',
      '<$5k',
      '$5k–$15k',
      '$15k–$30k',
      '$30k–$60k',
      '$60k–$100k',
      '$100k–$250k',
      '$250k–$500k',
      '$500k+',
    ]
  },
  {
    id: 'debt',
    label: 'Debt',
    options: [
      'Prefer not to say',
      '$0',
      '<$5k',
      '$5k–$15k',
      '$15k–$30k',
      '$30k–$75k',
      '$75k–$150k',
      '$150k+'
    ]
  },
  {
    id: 'salary',
    label: 'Monthly Salary',
    options: [
      'Prefer not to say',
      '<$1k',
      '$1k–$2k',
      '$2k–$3k',
      '$3k–$5k',
      '$5k–$7k',
      '$7k+'
    ]
  }
];

function AccountPage({ user, onBack }) {
  const [profileData, setProfileData] = useState({});
  const [editedData, setEditedData] = useState({});
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [hasChanges, setHasChanges] = useState(false);
  const [saveMessage, setSaveMessage] = useState('');
  const [citySuggestions, setCitySuggestions] = useState([]);
  const [cityInput, setCityInput] = useState('');
  const [isLoadingCities, setIsLoadingCities] = useState(false);
  const [showCitySuggestions, setShowCitySuggestions] = useState(false);
  const debounceTimer = useRef(null);
  const cityInputRef = useRef(null);

  // Fetch user profile on mount
  useEffect(() => {
    const fetchProfile = async () => {
      try {
        const data = await getUserProfile(user.uid);
        if (data && data.profile) {
          setProfileData(data.profile);
          setEditedData(data.profile);
          setCityInput(data.profile.location || '');
        }
      } catch (error) {
        console.error('Error fetching profile:', error);
      } finally {
        setIsLoading(false);
      }
    };

    fetchProfile();
  }, [user.uid]);

  // Check for changes
  useEffect(() => {
    const changed = JSON.stringify(profileData) !== JSON.stringify(editedData);
    setHasChanges(changed);
  }, [profileData, editedData]);

  // Fetch city suggestions
  const fetchCitySuggestions = async (query) => {
    if (!query || query.length < 2) {
      setCitySuggestions([]);
      return;
    }

    setIsLoadingCities(true);
    try {
      const response = await fetch(
        `https://nominatim.openstreetmap.org/search?q=${encodeURIComponent(query)}&format=json&addressdetails=1&limit=5&featuretype=city`
      );
      const data = await response.json();
      
      const cities = data
        .filter(item => 
          item.address && 
          (item.type === 'city' || 
           item.type === 'town' || 
           item.type === 'village' || 
           item.address.city || 
           item.address.town || 
           item.address.village)
        )
        .map(item => {
          const city = item.address.city || item.address.town || item.address.village || item.name;
          const state = item.address.state || '';
          const country = item.address.country || '';
          return {
            displayName: `${city}${state ? ', ' + state : ''}${country ? ', ' + country : ''}`,
            city: city,
            fullAddress: item.display_name
          };
        })
        .slice(0, 5);
      
      setCitySuggestions(cities);
    } catch (error) {
      console.error('Error fetching city suggestions:', error);
      setCitySuggestions([]);
    } finally {
      setIsLoadingCities(false);
    }
  };

  // Debounce city input
  useEffect(() => {
    if (debounceTimer.current) {
      clearTimeout(debounceTimer.current);
    }

    if (cityInput && showCitySuggestions) {
      debounceTimer.current = setTimeout(() => {
        fetchCitySuggestions(cityInput);
      }, 300);
    }

    return () => {
      if (debounceTimer.current) {
        clearTimeout(debounceTimer.current);
      }
    };
  }, [cityInput, showCitySuggestions]);

  // Close suggestions when clicking outside
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (cityInputRef.current && !cityInputRef.current.contains(event.target)) {
        setShowCitySuggestions(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, []);

  const handleValueChange = (fieldId, value) => {
    setEditedData(prev => ({
      ...prev,
      [fieldId]: value
    }));
    setSaveMessage('');
  };

  const handleCityInputChange = (e) => {
    const value = e.target.value;
    setCityInput(value);
    setShowCitySuggestions(true);
    setEditedData(prev => ({
      ...prev,
      location: value
    }));
    setSaveMessage('');
  };

  const handleCitySelect = useCallback((city) => {
    setCityInput(city.displayName);
    setShowCitySuggestions(false);
    setCitySuggestions([]);
    setEditedData(prev => ({
      ...prev,
      location: city.displayName
    }));
  }, []);

  const handleSave = async () => {
    setIsSaving(true);
    setSaveMessage('');
    try {
      await updateUserProfile(user.uid, {
        profile: editedData,
        profileCompleted: true
      });
      setProfileData(editedData);
      setSaveMessage('Profile saved successfully!');
    } catch (error) {
      console.error('Error saving profile:', error);
      setSaveMessage('Failed to save profile. Please try again.');
    } finally {
      setIsSaving(false);
    }
  };

  const handleCancel = () => {
    setEditedData(profileData);
    setCityInput(profileData.location || '');
    setSaveMessage('');
  };

  if (isLoading) {
    return (
      <div className="account-page">
        <div className="account-loading">Loading profile...</div>
      </div>
    );
  }

  return (
    <div className="account-page">
      <div className="account-container">
        <button className="account-back-button" onClick={onBack}>
          <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M19 12H5M5 12L12 19M5 12L12 5" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
          </svg>
          Back
        </button>

        <div className="account-header">
          <div className="account-avatar-container">
            <img 
              src={user.photoURL || '/default-avatar.png'} 
              alt="Profile" 
              className="account-avatar"
            />
          </div>
          <h1 className="account-title">{user.displayName || 'User'}</h1>
          <p className="account-email">{user.email}</p>
        </div>

        <div className="account-section">
          <h2 className="account-section-title">Financial Profile</h2>
          
          <div className="account-fields">
            {profileFields.map((field) => (
              <div key={field.id} className="account-field">
                <label className="account-field-label">{field.label}</label>
                
                {field.type === 'text' ? (
                  field.id === 'location' ? (
                    <div className="city-autocomplete-container" ref={cityInputRef}>
                      <input
                        type="text"
                        className="account-input"
                        placeholder={field.placeholder}
                        value={cityInput}
                        onChange={handleCityInputChange}
                        onFocus={() => setShowCitySuggestions(true)}
                      />
                      {showCitySuggestions && (cityInput.length >= 2) && (
                        <div className="city-suggestions-dropdown">
                          {isLoadingCities ? (
                            <div className="city-suggestion-item loading">Loading...</div>
                          ) : citySuggestions.length > 0 ? (
                            citySuggestions.map((city, idx) => (
                              <div
                                key={idx}
                                className="city-suggestion-item"
                                onClick={() => handleCitySelect(city)}
                              >
                                {city.displayName}
                              </div>
                            ))
                          ) : (
                            <div className="city-suggestion-item no-results">
                              No cities found. Try a different search.
                            </div>
                          )}
                        </div>
                      )}
                    </div>
                  ) : (
                    <input
                      type="text"
                      className="account-input"
                      placeholder={field.placeholder}
                      value={editedData[field.id] || ''}
                      onChange={(e) => handleValueChange(field.id, e.target.value)}
                    />
                  )
                ) : (
                  <select
                    className="account-select"
                    value={editedData[field.id] || ''}
                    onChange={(e) => handleValueChange(field.id, e.target.value)}
                  >
                    <option value="" disabled>Select an option</option>
                    {field.options.map((option, idx) => (
                      <option key={idx} value={option}>
                        {option}
                      </option>
                    ))}
                  </select>
                )}
              </div>
            ))}
          </div>

          {saveMessage && (
            <div className={`account-message ${saveMessage.includes('Failed') ? 'error' : 'success'}`}>
              {saveMessage}
            </div>
          )}

          <div className="account-actions">
            <button 
              className="account-cancel-button"
              onClick={handleCancel}
              disabled={!hasChanges || isSaving}
            >
              Cancel
            </button>
            <button 
              className="account-save-button"
              onClick={handleSave}
              disabled={!hasChanges || isSaving}
            >
              {isSaving ? 'Saving...' : 'Save Changes'}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

export default AccountPage;
