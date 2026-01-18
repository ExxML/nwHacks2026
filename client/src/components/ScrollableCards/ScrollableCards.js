import './ScrollableCards.css';
import { useState, useEffect, useRef } from 'react';

function ScrollableCards({ numberOfCards, renderCardContent, cardsData }) {
  const [selectedIndex, setSelectedIndex] = useState(0);
  const containerRef = useRef(null);
  const isScrolling = useRef(false);
  const cards = Array(numberOfCards).fill(null);

  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;

    const handleWheel = (e) => {
      e.preventDefault();
      
      if (isScrolling.current) return;
      
      const direction = e.deltaY > 0 ? 1 : -1;
      const newIndex = selectedIndex + direction;
      
      if (newIndex >= 0 && newIndex < cards.length) {
        isScrolling.current = true;
        setSelectedIndex(newIndex);
        
        // Very short cooldown for fast scrolling
        setTimeout(() => {
          isScrolling.current = false;
        }, 80);
      }
    };

    container.addEventListener('wheel', handleWheel, { passive: false });
    
    return () => {
      container.removeEventListener('wheel', handleWheel);
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
    <div className="scrollable-cards" ref={containerRef}>
      <div className="scrollable-cards__container">
        {cards.map((_, index) => (
          <div 
            key={index}
            className={`scrollable-cards__card ${index === selectedIndex ? 'scrollable-cards__card--selected' : ''}`}
            style={{
              '--offset': index - selectedIndex,
              zIndex: getZIndex(index)
            }}
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
