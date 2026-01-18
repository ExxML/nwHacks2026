import './ProfileSetup.css';
import { useState, useEffect, useRef, useCallback } from 'react';
import ScrollableCards from '../ScrollableCards/ScrollableCards';
import welcomeImage from '../../assets/welcome_profilesetup.svg';

const profileQuestions = [
  {
    id: 'age',
    title: 'Age',
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
    title: 'Location',
    type: 'text',
    placeholder: 'Enter your city'
  },
  {
    id: 'propertyValue',
    title: 'Property Value',
    subtitle: 'Current market value of all properties',
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
    title: 'Vehicle Value',
    subtitle: 'Current market value of all vehicles',
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
    title: 'Investments',
    subtitle: 'Current value of all investments (stocks, bonds, etc.)',
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
    title: 'Debt',
    subtitle: 'Current total debt',
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
    title: 'Monthly Salary',
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

function ProfileSetup({ onComplete }) {
  const [profileData, setProfileData] = useState({});
  const [citySuggestions, setCitySuggestions] = useState([]);
  const [cityInput, setCityInput] = useState('');
  const [isLoadingCities, setIsLoadingCities] = useState(false);
  const [showCitySuggestions, setShowCitySuggestions] = useState(false);
  const [citySelected, setCitySelected] = useState(false);
  const [currentCardIndex, setCurrentCardIndex] = useState(0);
  const [showWelcomeImage, setShowWelcomeImage] = useState(true);
  const debounceTimer = useRef(null);
  const cityInputRef = useRef(null);
  const previousCardIndex = useRef(0);

  // Fetch city suggestions from API
  const fetchCitySuggestions = async (query) => {
    if (!query || query.length < 2) {
      setCitySuggestions([]);
      return;
    }

    setIsLoadingCities(true);
    try {
      // Using Nominatim API (OpenStreetMap) - free and no API key required
      const response = await fetch(
        `https://nominatim.openstreetmap.org/search?q=${encodeURIComponent(query)}&format=json&addressdetails=1&limit=5&featuretype=city`
      );
      const data = await response.json();
      
      // Filter and format results to show cities
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
        .slice(0, 5); // Limit to maximum 5 items
      
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

    if (cityInput && !citySelected) {
      debounceTimer.current = setTimeout(() => {
        fetchCitySuggestions(cityInput);
      }, 300);
    }

    return () => {
      if (debounceTimer.current) {
        clearTimeout(debounceTimer.current);
      }
    };
  }, [cityInput, citySelected]);

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

  const handleValueChange = (questionId, value, event) => {
    setProfileData(prev => ({
      ...prev,
      [questionId]: value
    }));
    // Blur the dropdown after selection to restore the arrow
    if (event && event.target) {
      event.target.blur();
    }
  };

  const handleCityInputChange = (e) => {
    const value = e.target.value;
    setCityInput(value);
    setCitySelected(false);
    setShowCitySuggestions(true);
    
    // Clear the location in profileData if user is typing
    setProfileData(prev => ({
      ...prev,
      location: ''
    }));
  };

  const handleCitySelect = useCallback((city) => {
    setCityInput(city.displayName);
    setCitySelected(true);
    setShowCitySuggestions(false);
    setCitySuggestions([]);
    
    // Set the location in profileData
    setProfileData(prev => ({
      ...prev,
      location: city.displayName
    }));
  }, []);

  const autoSelectFirstCity = useCallback(() => {
    // Auto-select first city if user has typed but not selected
    if (cityInput && !citySelected && citySuggestions.length > 0) {
      handleCitySelect(citySuggestions[0]);
    }
  }, [cityInput, citySelected, citySuggestions, handleCitySelect]);

  // Update welcome image visibility based on selected card
  useEffect(() => {
    setShowWelcomeImage(currentCardIndex === 0);
  }, [currentCardIndex]);

  // Auto-select first city when leaving location card (index 1)
  useEffect(() => {
    const locationCardIndex = 1; // Location is the second card (index 1)
    
    // If we're moving away from the location card
    if (previousCardIndex.current === locationCardIndex && currentCardIndex !== locationCardIndex) {
      autoSelectFirstCity();
    }
    
    previousCardIndex.current = currentCardIndex;
  }, [currentCardIndex, autoSelectFirstCity]);

  const handleSubmit = () => {
    // Check if all required fields are filled
    const allFilled = profileQuestions.every(q => profileData[q.id]);
    
    if (allFilled) {
      onComplete(profileData);
    } else {
      alert('Please complete all fields before submitting.');
    }
  };

  const renderCardContent = (question, index, isSelected, goToNextCard) => {
    const isLastCard = index === profileQuestions.length - 1;
    const currentValue = profileData[question.id];
    const allFilled = profileQuestions.every(q => profileData[q.id]);

    // Update current card index when card is selected
    if (isSelected && currentCardIndex !== index) {
      setCurrentCardIndex(index);
    }

    const handleKeyDown = (e) => {
      if (e.key === 'Enter' && !isLastCard) {
        // Auto-select first city if on location field
        if (question.id === 'location') {
          autoSelectFirstCity();
        }
        goToNextCard();
      }
    };

    return (
      <div className="profile-card-content">
        <div className="profile-card-header">
          <h2 className="profile-card-title">{question.title}</h2>
          {question.subtitle && (
            <p className="profile-card-subtitle">{question.subtitle}</p>
          )}
        </div>

        <div className="profile-card-input">
          {question.type === 'text' ? (
            question.id === 'location' ? (
              <div className="city-autocomplete-container" ref={cityInputRef}>
                <input
                  type="text"
                  className="profile-text-input"
                  placeholder={question.placeholder}
                  value={cityInput}
                  onChange={handleCityInputChange}
                  onFocus={() => setShowCitySuggestions(true)}
                  onKeyDown={handleKeyDown}
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
                className="profile-text-input"
                placeholder={question.placeholder}
                value={currentValue || ''}
                onChange={(e) => handleValueChange(question.id, e.target.value)}
                onKeyDown={handleKeyDown}
              />
            )
          ) : (
            <select
              className="profile-dropdown"
              value={currentValue || ''}
              onChange={(e) => handleValueChange(question.id, e.target.value, e)}
              onKeyDown={handleKeyDown}
            >
              <option value="" disabled>Select an option</option>
              {question.options.map((option, idx) => (
                <option key={idx} value={option}>
                  {option}
                </option>
              ))}
            </select>
          )}
        </div>

        {isLastCard && (
          <div 
            className={`profile-submit-button ${!isSelected || !allFilled ? 'disabled' : ''}`}
            onClick={isSelected && allFilled ? handleSubmit : () => {
              if (!allFilled) {
                alert('Please fill in all the fields.');
              }
            }}
            title={!allFilled ? 'Please fill in all the fields.' : ''}
          >
            Complete Profile
          </div>
        )}

        <div className="profile-card-progress">
          {index + 1} / {profileQuestions.length}
        </div>
      </div>
    );
  };

  return (
    <div className="profile-setup-container">
      <div className={`welcome-image-container ${showWelcomeImage ? 'visible' : 'hidden'}`}>
        <img src={welcomeImage} alt="Welcome" className="welcome-image" />
      </div>
      <ScrollableCards 
        numberOfCards={profileQuestions.length}
        renderCardContent={renderCardContent}
        cardsData={profileQuestions}
      />
    </div>
  );
}

export default ProfileSetup;
