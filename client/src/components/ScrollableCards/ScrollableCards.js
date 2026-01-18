import './ScrollableCards.css';
import { useState, useEffect, useRef } from 'react';

function ScrollableCards({ numberOfCards, renderCardContent, cardsData }) {
  const [selectedIndex, setSelectedIndex] = useState(0);
  const [isScrollingActive, setIsScrollingActive] = useState(false);
  const containerRef = useRef(null);
  const isScrolling = useRef(false);
  const scrollTimeout = useRef(null);
  const cards = Array(numberOfCards).fill(null);

  // Separate effect for motion blur timeout cleanup on unmount only
  useEffect(() => {
    return () => {
      if (scrollTimeout.current) {
        clearTimeout(scrollTimeout.current);
      }
    };
  }, []);

  useEffect(() => {
    const handleWheel = (e) => {
      e.preventDefault();
      
      if (isScrolling.current) return;
      
      const direction = e.deltaY > 0 ? 1 : -1;
      const newIndex = selectedIndex + direction;
      
      if (newIndex >= 0 && newIndex < cards.length) {
        isScrolling.current = true;
        setIsScrollingActive(true);
        setSelectedIndex(newIndex);
        
        // Clear existing timeout
        if (scrollTimeout.current) {
          clearTimeout(scrollTimeout.current);
        }
        
        // Very short cooldown for fast scrolling and remove blur immediately after
        scrollTimeout.current = setTimeout(() => {
          isScrolling.current = false;
          setIsScrollingActive(false);
        }, 20);
      }
    };

    // Attach to window instead of container to allow scrolling anywhere
    window.addEventListener('wheel', handleWheel, { passive: false });
    
    return () => {
      window.removeEventListener('wheel', handleWheel);
    };
  }, [selectedIndex, cards.length]);

  // Calculate z-index based on distance from selected card
  const getZIndex = (index) => {
    const distance = Math.abs(index - selectedIndex);
    return cards.length - distance;
  };

  const goToNextCard = () => {
    if (selectedIndex < cards.length - 1) {
      setSelectedIndex(selectedIndex + 1);
    }
  };

  return (
    <div 
      className={`scrollable-cards ${isScrollingActive ? 'scrollable-cards--scrolling' : ''}`} 
      ref={containerRef}
    >
      <div className="scrollable-cards__container">
        {cards.map((_, index) => (
          <div 
            key={index}
            className={`scrollable-cards__card ${index === selectedIndex ? 'scrollable-cards__card--selected' : ''}`}
            style={{
              '--offset': index - selectedIndex,
              zIndex: getZIndex(index)
            }}
            onClick={() => setSelectedIndex(index)}
          >
            <div className="scrollable-cards__card-inner">
              {renderCardContent && cardsData && cardsData[index] 
                ? renderCardContent(cardsData[index], index, index === selectedIndex, goToNextCard)
                : null
              }
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

export default ScrollableCards;
