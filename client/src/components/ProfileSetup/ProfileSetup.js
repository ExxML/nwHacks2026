import './ProfileSetup.css';
import { useState } from 'react';
import ScrollableCards from '../ScrollableCards/ScrollableCards';

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
    placeholder: 'Enter city or postal code'
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
    subtitle: 'Current value of all investments',
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

    const handleKeyDown = (e) => {
      if (e.key === 'Enter' && !isLastCard) {
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
            <input
              type="text"
              className="profile-text-input"
              placeholder={question.placeholder}
              value={currentValue || ''}
              onChange={(e) => handleValueChange(question.id, e.target.value)}
              onKeyDown={handleKeyDown}
            />
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
    <ScrollableCards 
      numberOfCards={profileQuestions.length}
      renderCardContent={renderCardContent}
      cardsData={profileQuestions}
    />
  );
}

export default ProfileSetup;
