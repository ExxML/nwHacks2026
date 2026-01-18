import React from 'react';

function StarDecorations() {
  return (
    <div className="decorative-elements">
      {/* 4-point stars (outline) */}
      <svg className="deco-star star-1" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
        <path d="M12 2L14.5 9.5L22 12L14.5 14.5L12 22L9.5 14.5L2 12L9.5 9.5L12 2Z" stroke="#0c2c55" strokeWidth="1.5" fill="none"/>
      </svg>
      <svg className="deco-star star-2" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
        <path d="M12 2L14.5 9.5L22 12L14.5 14.5L12 22L9.5 14.5L2 12L9.5 9.5L12 2Z" stroke="#0c2c55" strokeWidth="1.5" fill="none"/>
      </svg>
      <svg className="deco-star star-3" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
        <path d="M12 2L14.5 9.5L22 12L14.5 14.5L12 22L9.5 14.5L2 12L9.5 9.5L12 2Z" stroke="#0c2c55" strokeWidth="1.5" fill="none"/>
      </svg>
      <svg className="deco-star star-4" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
        <path d="M12 2L14.5 9.5L22 12L14.5 14.5L12 22L9.5 14.5L2 12L9.5 9.5L12 2Z" stroke="#0c2c55" strokeWidth="1.5" fill="none"/>
      </svg>
      
      {/* Sparkles - filled 4-point stars */}
      <svg className="deco-sparkle sparkle-1" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
        <path d="M12 0L14 10L24 12L14 14L12 24L10 14L0 12L10 10L12 0Z" fill="#0c2c55"/>
      </svg>
      <svg className="deco-sparkle sparkle-2" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
        <path d="M12 0L14 10L24 12L14 14L12 24L10 14L0 12L10 10L12 0Z" fill="#0c2c55"/>
      </svg>
      <svg className="deco-sparkle sparkle-3" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
        <path d="M12 0L14 10L24 12L14 14L12 24L10 14L0 12L10 10L12 0Z" fill="#0c2c55"/>
      </svg>
      <svg className="deco-sparkle sparkle-4" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
        <path d="M12 0L14 10L24 12L14 14L12 24L10 14L0 12L10 10L12 0Z" fill="#0c2c55"/>
      </svg>
      
      {/* Shooting stars */}
      <svg className="deco-shooting shooting-1" viewBox="0 0 120 40" xmlns="http://www.w3.org/2000/svg">
        <path d="M120 20C120 20 80 15 40 18C20 19 0 25 0 25" stroke="#0c2c55" strokeWidth="2" fill="none" strokeLinecap="round"/>
        <circle cx="0" cy="25" r="4" fill="#0c2c55"/>
      </svg>
      <svg className="deco-shooting shooting-2" viewBox="0 0 120 40" xmlns="http://www.w3.org/2000/svg">
        <path d="M120 20C120 20 80 15 40 18C20 19 0 25 0 25" stroke="#0c2c55" strokeWidth="2" fill="none" strokeLinecap="round"/>
        <circle cx="0" cy="25" r="4" fill="#0c2c55"/>
      </svg>
      
      {/* 5-point outline stars */}
      <svg className="deco-5star five-star-1" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
        <path d="M12 2L15.09 8.26L22 9.27L17 14.14L18.18 21.02L12 17.77L5.82 21.02L7 14.14L2 9.27L8.91 8.26L12 2Z" stroke="#0c2c55" strokeWidth="1.5" fill="none"/>
      </svg>
      <svg className="deco-5star five-star-2" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
        <path d="M12 2L15.09 8.26L22 9.27L17 14.14L18.18 21.02L12 17.77L5.82 21.02L7 14.14L2 9.27L8.91 8.26L12 2Z" stroke="#0c2c55" strokeWidth="1.5" fill="none"/>
      </svg>
    </div>
  );
}

export default StarDecorations;
