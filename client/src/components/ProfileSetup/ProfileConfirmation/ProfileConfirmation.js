import './ProfileConfirmation.css';
 
function ProfileConfirmation({ profileData, onConfirm, onEdit }) {
  const fields = [
    { id: 'age', label: 'age' },
    { id: 'location', label: 'location' },
    { id: 'propertyValue', label: 'property' },
    { id: 'vehicleValue', label: 'vehicle' },
    { id: 'investments', label: 'investments' },
    { id: 'debt', label: 'debt' },
    { id: 'salary', label: 'salary' },
  ];
 
  const getDisplayValue = (fieldId) => {
    if (!profileData) return '—';
    const value = profileData[fieldId];
    return value && value !== '' ? value : '—';
  };
 
  return (
    <div className="profile-confirmation-wrapper">
      <div className="profile-confirmation-card">
        <div className="profile-confirmation-corner" />
 
        <h1 className="profile-confirmation-title">confirm your portfolio</h1>
 
        <div className="profile-confirmation-content">
          {fields.map((field) => (
            <div key={field.id} className="profile-confirmation-row">
              <span className="profile-confirmation-label">{field.label}:</span>
              <span className="profile-confirmation-value">{getDisplayValue(field.id)}</span>
            </div>
          ))}
        </div>
 
        <div className="profile-confirmation-bottom">
          <div className="profile-confirmation-actions">
            <button
              type="button"
              className="profile-confirmation-button secondary"
              onClick={onEdit}
            >
              Edit answers
            </button>
            <button
              type="button"
              className="profile-confirmation-button primary"
              onClick={onConfirm}
            >
              Confirm
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
 
export default ProfileConfirmation;